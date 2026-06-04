
import io
import os
import sys
import stat
import json
import shutil
import hashlib
import zipfile
import tempfile
import argparse
import subprocess
import urllib.error
import urllib.request
import threading
from pathlib import Path

OUTPUT = Path("msvc")
DOWNLOADS = Path("downloads")


DEFAULT_HOST = "x64"
ALL_HOSTS    = "x64 x86 arm64".split()

DEFAULT_TARGET = "x64"
ALL_TARGETS    = "x64 x86 arm arm64".split()

DEFAULT_VERSION = "latest"
ALL_VERSIONS    = "2019 2022 2026 latest".split()

MANIFEST_URLS = {
  "latest": ["https://aka.ms/vs/stable/channel",     "https://aka.ms/vs/insiders/channel"   ],
  "2026":   ["https://aka.ms/vs/18/stable/channel",  "https://aka.ms/vs/18/insiders/channel"],
  "2022":   ["https://aka.ms/vs/17/release/channel", "https://aka.ms/vs/17/pre/channel"     ],
  "2019":   ["https://aka.ms/vs/16/release/channel", "https://aka.ms/vs/16/pre/channel"     ],
}

ssl_context = None
def download_aria2c_style(url, num_threads=16):
  ARIA2C = r"D:\Programs\msys64\ucrt64\bin\aria2c.exe"
  import tempfile, os
  with tempfile.TemporaryDirectory() as tmp:
    out_file = os.path.join(tmp, "download.bin")
    cmd = [
      ARIA2C,
      "--split", str(num_threads),
      "--max-connection-per-server", str(num_threads),
      "--min-split-size", "1M",
      "--out", "download.bin",
      "--dir", tmp,
      "--console-log-level", "warn",
      "--show-console-readout", "true",
      "--async-dns-server", "8.8.8.8",
      url
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
      print("  aria2c failed, falling back to threaded download...")
      return download(url)  # fallback
    with open(out_file, "rb") as f:
      return f.read()
  
def download(url):
  print(f"  Fetching {url[:80]}...", flush=True)
  req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
  })
  with urllib.request.urlopen(req, context=ssl_context, timeout=120) as res:
    total = res.headers.get("Content-Length")
    total = int(total) if total else None
    data = b""
    start = __import__("time").time()
    while True:
      block = res.read(1 << 16)
      if not block:
        break
      data += block
      elapsed = __import__("time").time() - start
      kb = len(data) / 1024
      speed = kb / elapsed if elapsed > 0 else 0
      if total:
        perc = len(data) * 100 // total
        print(f"\r  {kb:.0f} KB / {total//1024} KB  ({perc}%)  {speed:.1f} KB/s", end="", flush=True)
      else:
        print(f"\r  {kb:.0f} KB downloaded  {speed:.1f} KB/s", end="", flush=True)
    print(f"\n  Done ({len(data)/1024:.0f} KB in {__import__('time').time()-start:.1f}s)", flush=True)
    return data

total_download = 0
total_cached = 0
total_sdk_download = 0
total_sdk_unchanged = 0

def download_progress(url, check, filename):
  fpath = DOWNLOADS / filename
  if fpath.exists():
    data = fpath.read_bytes()
    if hashlib.sha256(data).hexdigest() == check.lower():
      global total_cached
      total_cached += len(data)
      print(f"\r{filename} ... OK")
      return data

  global total_download
  with fpath.open("wb") as f:
    data = io.BytesIO()
    with urllib.request.urlopen(url, context=ssl_context) as res:
      total = int(res.headers["Content-Length"])
      size = 0
      while True:
        block = res.read(1<<20)
        if not block:
          break
        f.write(block)
        data.write(block)
        size += len(block)
        perc = size * 100 // total
        print(f"\r{filename} ... {perc}%", end="")
    print()
    data = data.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    if check.lower() != digest:
      sys.exit(f"Hash mismatch for {filename}")
    total_download += len(data)
    return data

def get_msi_cabs(msi):
  index = 0
  while True:
    index = msi.find(b".cab", index+4)
    if index < 0:
      return
    yield msi[index-32:index+4].decode("ascii")

def first(items, cond = lambda x: True):
  return next((item for item in items if cond(item)), None)

def _get_file_product_version(path):
  """
  Read ProductVersion from a Windows PE binary using pure Python (no PowerShell).

  VS_FIXEDFILEINFO layout (all LE 32-bit words from the signature):
    +0  dwSignature   (0xFEEF04BD)
    +4  dwStrucVersion
    +8  dwFileVersionMS
    +12 dwFileVersionLS
    +16 dwProductVersionMS
    +20 dwProductVersionLS

  Each 32-bit word packs (high16 << 16 | low16).  A canonical Windows version
  like 10.0.26100.3915 encodes as:
    ProductVersionMS = (10 << 16) | 0       → high=10,  low=0
    ProductVersionLS = (26100 << 16) | 3915 → high=26100, low=3915

  Some Windows SDK / Insider Preview binaries store the parts in a different
  arrangement (e.g. rc.exe in 10.0.28000 builds), yielding "28000.1721.10.0"
  when parsed with the wrong offsets.  We detect this (first component > 999
  and 10 appears elsewhere) and reconstruct the canonical 10.0.BUILD.PATCH form.

  Also try dwFileVersionMS/LS (offsets +8/+12) as a fallback in case
  ProductVersion fields are zeroed.
  """
  try:
    import struct
    with open(path, "rb") as f:
      data = f.read()
    sig = b"\xbd\x04\xef\xfe"
    idx = data.find(sig)
    if idx < 0:
      return None

    def _parse(ms, ls):
      a, b, c, d = ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF
      return a, b, c, d

    def _reconstruct_sdk(parts):
      """If parts look like a scrambled Windows SDK version, return canonical form."""
      a, b, c, d = parts
      if a > 999:
        build = a
        remainder = [b, c, d]
        ten_pos  = next((i for i, v in enumerate(remainder) if v == 10), None)
        zero_pos = next((i for i, v in enumerate(remainder) if v == 0 and i != ten_pos), None)
        patches  = [v for i, v in enumerate(remainder) if i != ten_pos and i != zero_pos]
        patch = patches[0] if patches else 0
        return f"10.0.{build}.{patch}"
      return f"{a}.{b}.{c}.{d}"

    ms = struct.unpack_from("<I", data, idx + 12)[0]
    ls = struct.unpack_from("<I", data, idx + 16)[0]
    if ms or ls:
      return _reconstruct_sdk(_parse(ms, ls))

    ms = struct.unpack_from("<I", data, idx + 8)[0]
    ls = struct.unpack_from("<I", data, idx + 12)[0]
    if ms or ls:
      return _reconstruct_sdk(_parse(ms, ls))

    return None
  except Exception:
    return None


_SDK_MSI_MANIFEST_FILE = "sdk_msi_manifest.json"

def _sha256_file(path):
  """Compute SHA256 of a file on disk, reading in 1 MB blocks."""
  h = hashlib.sha256()
  with open(path, "rb") as f:
    while True:
      block = f.read(1 << 20)
      if not block:
        break
      h.update(block)
  return h.hexdigest()

def _load_sdk_msi_manifest(downloads_dir):
  """Load the saved per-MSI SHA256 manifest, or return {}."""
  path = downloads_dir / _SDK_MSI_MANIFEST_FILE
  if path.exists():
    try:
      return json.loads(path.read_text())
    except Exception:
      pass
  return {}


ap = argparse.ArgumentParser()
ap.add_argument("--show-versions", action="store_true", help="Show available MSVC and Windows SDK versions")
ap.add_argument("--accept-license", action="store_true", help="Automatically accept license")
ap.add_argument("--msvc-version", help="Get specific MSVC version")
ap.add_argument("--sdk-version", help="Get specific Windows SDK version")
ap.add_argument("--vs", default=DEFAULT_VERSION, help=f"Visual Studio version to use for installation", choices=ALL_VERSIONS)
ap.add_argument("--insiders", "--preview", action="store_true", help="Use insiders/preview versions")
ap.add_argument("--target", default=DEFAULT_TARGET, help=f"Target architectures, comma separated ({','.join(ALL_TARGETS)})")
ap.add_argument("--host", default=DEFAULT_HOST, help=f"Host architecture", choices=ALL_HOSTS)
ap.add_argument("--sdk-use-cache", action="store_true",
  help="Skip wiping the SDK layout folder before running winsdksetup /layout. "
       "By default the layout folder is always wiped so every MSI is re-fetched "
       "from Microsoft's CDN and its SHA256 is compared against the hash saved "
       "from the previous successful install -- the only way to reliably detect "
       "silent server-side MSI replacements within the same version number. "
       "With --sdk-use-cache winsdksetup reuses any MSI already present in the "
       "layout folder by filename alone and never contacts the server to verify "
       "content, so 'OK' means locally unchanged, NOT server-verified. "
       "Use only when bandwidth is constrained and you accept the trade-off.")
args = ap.parse_args()

host = args.host
targets = args.target.split(',')
for target in targets:
  if target not in ALL_TARGETS:
    sys.exit(f"Unknown {target} target architecture!")


URL = MANIFEST_URLS[args.vs][args.insiders]

try:
  print("Step 1/2: Downloading VS channel manifest (may take 30+ seconds from your location)...")
  # manifest = json.loads(download(URL))          # comment this out
  manifest = json.loads(download_aria2c_style(URL))
  #manifest = json.loads(download(URL))
except urllib.error.URLError as err:
  import ssl
  if isinstance(err.args[0], ssl.SSLCertVerificationError):
    print("ERROR: ssl certificate verification error")
    try:
      import certifi
    except ModuleNotFoundError:
      print("ERROR: please install 'certifi' package to use Mozilla certificates")
      print("ERROR: or update your Windows certs, see instructions here: https://woshub.com/updating-trusted-root-certificates-in-windows-10/#h2_3")
      sys.exit()
    print("NOTE: retrying with certifi certificates")
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    manifest = json.loads(download(URL))
  else:
    raise


ITEM_NAME = "Microsoft.VisualStudio.Manifests.VisualStudioPreview" if args.insiders else "Microsoft.VisualStudio.Manifests.VisualStudio"

vs = first(manifest["channelItems"], lambda x: x["id"] == ITEM_NAME)
payload = vs["payloads"][0]["url"]

print("Step 2/2: Downloading VS packages manifest (large file, please wait)...")
# vsmanifest = json.loads(download(payload))    # comment this out
vsmanifest = json.loads(download_aria2c_style(payload))


packages = {}
for p in vsmanifest["packages"]:
  packages.setdefault(p["id"].lower(), []).append(p)

msvc = {}
sdk = {}

for pid,p in packages.items():
  if pid.startswith("microsoft.vc.") and pid.endswith(".tools.hostx64.targetx64.base"):
    pver = ".".join(pid.split(".")[2:4])
    if pver[0].isnumeric():
      msvc[pver] = pid
  elif pid.startswith("microsoft.visualstudio.component.windows10sdk.") or \
       pid.startswith("microsoft.visualstudio.component.windows11sdk."):
    pver = pid.split(".")[-1]
    if pver.isnumeric():
      sdk[pver] = pid

if args.show_versions:
  print("MSVC versions:", " ".join(sorted(msvc.keys())))
  print("Windows SDK versions:", " ".join(sorted(sdk.keys())))
  sys.exit(0)


def get_version_string_variants(short_ver, packages):
  """
  Find all version string formats that actually appear in package IDs.
  """
  variants = set()
  prefix = f"microsoft.vc.{short_ver}"

  for pid in packages.keys():
    if pid.startswith(prefix):
      parts = pid.split(".")
      version_parts = []
      for i in range(2, len(parts)):
        if parts[i].isnumeric():
          version_parts.append(parts[i])
        else:
          break
      if version_parts:
        variants.add(".".join(version_parts))

  return sorted(variants)


def count_available_packages(short_ver, packages, host, targets):
  """
  Count how many packages are available for a given version.
  Returns: (available_count, total_expected, version_string, full_version)
  """

  version_variants = get_version_string_variants(short_ver, packages)

  if not version_variants:
    return (0, 0, None, None)

  best_available = 0
  best_version_str = None
  best_full_version = None

  for ver_str in version_variants:
    expected_patterns = [
      f"microsoft.visualcpp.dia.sdk",
      f"microsoft.vc.{ver_str}.crt.headers.base",
      f"microsoft.vc.{ver_str}.crt.source.base",
      f"microsoft.vc.{ver_str}.asan.headers.base",
      f"microsoft.vc.{ver_str}.pgo.headers.base",
    ]

    for target in targets:
      expected_patterns += [
        f"microsoft.vc.{ver_str}.tools.host{host}.target{target}.base",
        f"microsoft.vc.{ver_str}.tools.host{host}.target{target}.res.base",
        f"microsoft.vc.{ver_str}.crt.{target}.desktop.base",
        f"microsoft.vc.{ver_str}.crt.{target}.store.base",
        f"microsoft.vc.{ver_str}.premium.tools.host{host}.target{target}.base",
        f"microsoft.vc.{ver_str}.pgo.{target}.base",
      ]
      if target in ["x86", "x64"]:
        expected_patterns.append(f"microsoft.vc.{ver_str}.asan.{target}.base")

    available = 0
    for pattern in expected_patterns:
      if pattern in packages:
        available += 1

    if available > best_available:
      best_available = available
      best_version_str = ver_str

      sample_pkg = f"microsoft.vc.{ver_str}.tools.host{host}.target{targets[0]}.base"
      if sample_pkg in packages:
        pkg_data = first(packages[sample_pkg])
        if pkg_data and "version" in pkg_data:
          best_full_version = pkg_data["version"]

  if best_full_version is None:
    best_full_version = best_version_str

  total_expected = len(expected_patterns)

  return (best_available, total_expected, best_version_str, best_full_version)


print("\n" + "="*70)
print("Analyzing MSVC versions...")
print("="*70)

version_analysis = {}
for ver in sorted(msvc.keys(), reverse=True):
  avail, total, pkg_ver, full_ver = count_available_packages(ver, packages, host, targets)
  percentage = (avail / total * 100) if total > 0 else 0
  version_analysis[ver] = {
    'available': avail,
    'total': total,
    'percentage': percentage,
    'pkg_version': pkg_ver,
    'full_version': full_ver
  }

  status = "✓ COMPLETE" if percentage == 100 else f"⚠ {percentage:.0f}% ({avail}/{total} packages)"
  print(f"  {ver:8s} [{full_ver:16s}]: {status}")

print("="*70)

if args.msvc_version:
  if args.msvc_version not in msvc:
    sys.exit(f"ERROR: MSVC version {args.msvc_version} not found")
  selected_short_ver = args.msvc_version
else:
  best_ver = None
  best_count = -1

  for ver in sorted(version_analysis.keys(), reverse=True):
    count = version_analysis[ver]['available']
    if count > best_count:
      best_count = count
      best_ver = ver

  selected_short_ver = best_ver

selected = version_analysis[selected_short_ver]
msvc_short_ver = selected_short_ver
msvc_pkg_ver = selected['pkg_version']
msvc_full_ver = selected['full_version']

print(f"\n✓ Selected best available version: {msvc_short_ver}")
print(f"  Full version: {msvc_full_ver}")
print(f"  Available packages: {selected['available']}/{selected['total']} ({selected['percentage']:.0f}%)")

if selected['percentage'] < 100:
  print(f"  ⚠ Warning: This version is incomplete ({selected['total'] - selected['available']} packages missing)")
  print(f"     Microsoft may still be uploading files for this version")
else:
  print(f"  ✓ All required packages available")


import re

def _github_raw_get(url):
  """Fetch a URL with a browser-like User-Agent, return raw bytes."""
  req = urllib.request.Request(url, headers={
    "Accept": "application/vnd.github+json",
    "User-Agent": "portable-msvc-script",
  })
  with urllib.request.urlopen(req, context=ssl_context, timeout=20) as res:
    return res.read()

def _github_api_get(url):
  """Fetch a GitHub API URL, return parsed JSON."""
  return json.loads(_github_raw_get(url))

def _ver_tuple(s):
  """Turn '10.0.26100.7705' into (10, 0, 26100, 7705) for comparison."""
  return tuple(int(x) if x.isnumeric() else 0 for x in s.split("."))


def _fetch_msdocs_page():
  """Fetch the SDK downloads page once and return the HTML text."""
  page_url = "https://learn.microsoft.com/en-us/windows/apps/windows-sdk/downloads"
  req = urllib.request.Request(page_url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) portable-msvc-script",
    "Accept": "text/html,application/xhtml+xml",
  })
  with urllib.request.urlopen(req, context=ssl_context, timeout=30) as res:
    return res.read().decode("utf-8", errors="replace")

_msdocs_page_cache = None

def _get_msdocs_page():
  """Return cached SDK downloads page HTML."""
  global _msdocs_page_cache
  if _msdocs_page_cache is None:
    _msdocs_page_cache = _fetch_msdocs_page()
  return _msdocs_page_cache


def get_latest_sdk_build_from_msdocs():
  """
  Scan the entire learn.microsoft.com SDK downloads page and return the
  highest SDK build number (e.g. 28000, 26100) found across all listed
  releases. This is used to auto-detect the latest SDK when the user has
  not specified --sdk-version and the VS manifest is behind.
  Returns an integer build number, or None on failure.
  """
  try:
    text = _get_msdocs_page()
    build_re = re.compile(r'10\.0\.(\d{5,})')
    builds = set(int(m.group(1)) for m in build_re.finditer(text))
    if builds:
      return max(builds)
  except Exception:
    pass
  return None


def _get_sdk_url_via_msdocs(sdk_build):
  """
  Strategy 1 – learn.microsoft.com/en-us/windows/apps/windows-sdk/downloads

  The page lists every SDK release in an HTML table. Each row contains the
  version string like (10.0.26100.7705) and a fwlink Installer href.
  The links are go.microsoft.com/fwlink redirects — urllib follows them
  automatically at download time, no need to resolve them here.

  Returns (url, full_version) or raises on any error.
  """
  text = _get_msdocs_page()

  build_re = re.compile(rf'10\.0\.{re.escape(str(sdk_build))}\.(\d+)')
  fwlink_re = re.compile(
    r'href="(https://go\.microsoft\.com/fwlink/[^"]+)"[^>]*>\s*Installer\s*<',
    re.IGNORECASE,
  )

  best_ver = None
  best_url = None
  pos = 0
  while True:
    m = build_re.search(text, pos)
    if not m:
      break
    full_ver = f"10.0.{sdk_build}.{m.group(1)}"
    window = text[m.start(): m.start() + 2000]
    um = fwlink_re.search(window)
    if um:
      if best_ver is None or _ver_tuple(full_ver) > _ver_tuple(best_ver):
        best_ver = full_ver
        best_url = um.group(1)
    pos = m.end()

  if not best_url:
    raise ValueError(
      f"no Installer fwlink found for build {sdk_build} on learn.microsoft.com"
    )
  return best_url, best_ver


def _get_sdk_url_via_insider_preview(sdk_build):
  """
  Strategy 1b – Windows Insider Preview SDK Download Center.
  Preview SDK builds are NOT listed on the main downloads page.
  Tries aka.ms/win/sdk/insider first, then scrapes the Insider Preview page.
  Returns (url, full_version) or raises on any error.
  """
  insider_aka = "https://aka.ms/win/sdk/insider"
  req = urllib.request.Request(insider_aka, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) portable-msvc-script",
  })
  try:
    with urllib.request.urlopen(req, context=ssl_context, timeout=15) as res:
      final_url = res.url
      m = re.search(rf'10\.0\.{re.escape(str(sdk_build))}\.(\d+)', final_url)
      if m:
        return final_url, f"10.0.{sdk_build}.{m.group(1)}"
  except Exception:
    pass

  insider_url = "https://www.microsoft.com/en-us/software-download/windowsinsiderpreviewSDK"
  req2 = urllib.request.Request(insider_url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) portable-msvc-script",
    "Accept": "text/html",
  })
  with urllib.request.urlopen(req2, context=ssl_context, timeout=30) as res2:
    page = res2.read().decode("utf-8", errors="replace")

  build_re = re.compile(rf'10\.0\.{re.escape(str(sdk_build))}\.(\d+)')
  url_re = re.compile(
    r'href="(https://(?:go\.microsoft\.com/fwlink/[^"]+|download\.microsoft\.com/[^"]+\.exe))"',
    re.IGNORECASE,
  )
  best_ver = None
  best_url = None
  pos = 0
  while True:
    m = build_re.search(page, pos)
    if not m:
      break
    full_ver = f"10.0.{sdk_build}.{m.group(1)}"
    window = page[m.start(): m.start() + 2000]
    um = url_re.search(window)
    if um:
      if best_ver is None or _ver_tuple(full_ver) > _ver_tuple(best_ver):
        best_ver = full_ver
        best_url = um.group(1)
    pos = m.end()

  if not best_url:
    raise ValueError(
      f"no installer URL found for insiders build {sdk_build} on Insider Preview page"
    )
  return best_url, best_ver


def _get_sdk_url_via_winget_pkgs(sdk_build):
  """
  Strategy 2 – microsoft/winget-pkgs community manifest.
  Usually behind by several weeks and doesn't carry insiders builds, but
  works as a fallback for stable QFEs.
  Returns (url, full_version) or raises on any error.
  """
  path = f"manifests/m/Microsoft/WindowsSDK/10.0.{sdk_build}"
  entries = _github_api_get(
    f"https://api.github.com/repos/microsoft/winget-pkgs/contents/{path}"
  )
  if not isinstance(entries, list):
    raise ValueError("unexpected GitHub API response")

  version_dirs = [e for e in entries if e["type"] == "dir"]
  if not version_dirs:
    raise ValueError("no version directories found")

  latest = max(version_dirs, key=lambda e: _ver_tuple(e["name"]))
  full_version = latest["name"]

  files = _github_api_get(
    f"https://api.github.com/repos/microsoft/winget-pkgs/contents/{path}/{full_version}"
  )
  installer_file = next(
    (f for f in files if "installer" in f["name"].lower() and f["name"].endswith(".yaml")),
    None,
  )
  if not installer_file:
    raise ValueError("installer YAML not found in manifest folder")

  yaml_text = _github_raw_get(installer_file["download_url"]).decode("utf-8")

  for line in yaml_text.splitlines():
    m = re.search(r'InstallerUrl\s*:\s*(https?://\S+\.exe)', line, re.IGNORECASE)
    if m:
      return m.group(1), full_version

  raise ValueError("no .exe InstallerUrl found in YAML")


def get_sdk_installer_url(sdk_build, insiders=False):
  """
  Try each strategy in order; return (url, full_version) from the first that
  succeeds, or (None, None) if all fail.
  """
  strategies = []
  if insiders:
    strategies += [
      ("Windows Insider Preview SDK page", lambda: _get_sdk_url_via_insider_preview(sdk_build)),
    ]
  strategies += [
    ("learn.microsoft.com/windows/apps/windows-sdk/downloads", lambda: _get_sdk_url_via_msdocs(sdk_build)),
    ("microsoft/winget-pkgs",                                  lambda: _get_sdk_url_via_winget_pkgs(sdk_build)),
  ]
  for name, fn in strategies:
    try:
      url, ver = fn()
      if url:
        print(f"  (resolved via {name})")
        return url, ver
    except Exception as e:
      print(f"  ({name} failed: {e})")
  return None, None


print(f"\nQuerying for latest Windows SDK installer...")

if args.sdk_version:
  sdk_ver = args.sdk_version
else:
  manifest_latest = max(sorted(sdk.keys()))
  print(f"  Checking learn.microsoft.com for latest SDK build...")
  msdocs_latest = get_latest_sdk_build_from_msdocs()
  if msdocs_latest and msdocs_latest > int(manifest_latest):
    sdk_ver = str(msdocs_latest)
    print(f"  Downloads page has newer SDK {sdk_ver} (VS manifest only knows {manifest_latest})")
  else:
    sdk_ver = manifest_latest
    print(f"  VS manifest SDK is current: {sdk_ver}")

sdk_in_manifest = sdk_ver in sdk
if not sdk_in_manifest:
  print(f"  Note: SDK {sdk_ver} is not in the VS manifest - will use standalone installer only.")

print(f"  Resolving installer URL for SDK {sdk_ver}...")
winsdksetup_url, sdk_full_ver = get_sdk_installer_url(sdk_ver, insiders=args.insiders)

if winsdksetup_url:
  print(f"  Latest SDK: {sdk_full_ver}  (VS manifest base: 10.0.{sdk_ver}.0)")
else:
  sdk_full_ver = f"10.0.{sdk_ver}.0"
  print(f"  Falling back to VS manifest SDK: {sdk_full_ver}")


sdk_packages = [
  f"Windows SDK for Windows Store Apps Tools-x86_en-us.msi",
  f"Windows SDK for Windows Store Apps Headers-x86_en-us.msi",
  f"Windows SDK for Windows Store Apps Headers OnecoreUap-x86_en-us.msi",
  f"Windows SDK for Windows Store Apps Libs-x86_en-us.msi",
  f"Universal CRT Headers Libraries and Sources-x86_en-us.msi",
]
for target in ALL_TARGETS:
  sdk_packages += [
    f"Windows SDK Desktop Headers {target}-x86_en-us.msi",
    f"Windows SDK OnecoreUap Headers {target}-x86_en-us.msi",
  ]
for target in targets:
  sdk_packages += [f"Windows SDK Desktop Libs {target}-x86_en-us.msi"]

print(f"\n{'='*70}")
print(f"Windows SDK v{sdk_full_ver} — state from last run (will re-check via /layout after license)...")
print(f"{'='*70}")

_sdk_layout_dir   = DOWNLOADS / "sdk_layout"
_sdk_marker_file  = DOWNLOADS / "sdk_layout.version"
_sdk_cached_ver   = _sdk_marker_file.read_text().strip() if _sdk_marker_file.exists() else ""

_sdk_kits_check = None
_sdk_kits_root  = None
for _kv in ["11", "10"]:
  _cb = OUTPUT / f"Windows Kits/{_kv}/bin"
  if _cb.exists():
    _installed = first(_cb.glob("*"))
    if _installed:
      _sdk_kits_check = _installed.name
      _sdk_kits_root  = OUTPUT / f"Windows Kits/{_kv}"
    break

_sdk_binary_ver = None
if _sdk_kits_check and _sdk_kits_root:
  _rc_exe_pre = _sdk_kits_root / "bin" / _sdk_kits_check / "x64" / "rc.exe"
  if _rc_exe_pre.exists():
    _sdk_binary_ver = _get_file_product_version(_rc_exe_pre)
    print(f"  Installed SDK binary version (rc.exe): {_sdk_binary_ver or 'unreadable'}")

if _sdk_binary_ver and _sdk_binary_ver != sdk_full_ver:
  print(f"  Installed binary ({_sdk_binary_ver}) != target ({sdk_full_ver})")
  print(f"  Removing stale Windows Kits folder to force clean install...")
  shutil.rmtree(_sdk_kits_root)
  print(f"  Stale Windows Kits removed ✓")
  _sdk_kits_check = None
  _sdk_kits_root  = None
  _sdk_binary_ver = None
elif _sdk_binary_ver and _sdk_binary_ver == sdk_full_ver:
  print(f"  ✓ Installed binary already matches target — no reinstall needed")

_sdk_layout_has_msis = _sdk_layout_dir.exists() and any(_sdk_layout_dir.rglob("*.msi"))
_sdk_ver_matches     = (_sdk_cached_ver == sdk_full_ver) or (_sdk_binary_ver == sdk_full_ver)

if winsdksetup_url and _sdk_layout_has_msis and _sdk_ver_matches:
  _sdk_saved_manifest = _load_sdk_msi_manifest(DOWNLOADS)

  if _sdk_saved_manifest:
    _found_msis_pre = {p.name: p for p in _sdk_layout_dir.rglob("*.msi")}
    _missing_pre = 0
    _changed_pre = 0
    for _pkg in sorted(sdk_packages):
      if _pkg not in _found_msis_pre:
        print(f"  {_pkg} ... NOT IN LAYOUT (skipping)")
        _missing_pre += 1
        continue
      _saved = _sdk_saved_manifest.get(_pkg)
      if _saved is None or "sha256" not in _saved:
        print(f"  {_pkg} ... NEW (no baseline yet)")
        _changed_pre += 1
      else:
        print(f"  {_pkg} ...", end=" ", flush=True)
        _actual = _sha256_file(_found_msis_pre[_pkg])
        if _actual != _saved["sha256"]:
          print(f"CHANGED ✗  (sha256 mismatch)")
          _changed_pre += 1
        else:
          print(f"OK ✓")
    if _missing_pre:
      print(f"  ({_missing_pre} MSI(s) absent from this SDK build — normal for Insider/Preview)")
    _sdk_pre_needs_relayout = _changed_pre > 0
    if not _sdk_pre_needs_relayout:
      print(f"  ✓ All SDK MSIs present and unchanged since last run")
    else:
      print(f"  ⚠ {_changed_pre} SDK MSI(s) changed or new since last run")
  else:
    _sdk_pre_needs_relayout = True
    print(f"  No SHA256 baseline yet — will hash after /layout completes")
  print(f"  Note: /layout will always run after license to check Microsoft's servers for updates")
else:
  _sdk_pre_needs_relayout = True
  if not winsdksetup_url:
    print(f"  Using VS manifest fallback (no standalone installer URL found)")
  elif not _sdk_ver_matches:
    if _sdk_cached_ver:
      print(f"  SDK version changed ({_sdk_cached_ver} → {sdk_full_ver}) — full download required")
    else:
      print(f"  No version marker found — full download required")
    if _sdk_layout_dir.exists():
      shutil.rmtree(_sdk_layout_dir)
      print(f"  Cleared stale layout folder to prevent stale MSI reuse")
  else:
    print(f"  No cached layout found — full download required")
  print(f"  Note: /layout will run after license to download SDK MSIs")

print(f"{'='*70}")


tools = first(manifest["channelItems"], lambda x: x["id"] == "Microsoft.VisualStudio.Product.BuildTools")
resource = first(tools["localizedResources"], lambda x: x["language"] == "en-us")
license = resource["license"]

if not args.accept_license:
  print(f"\nDownloading MSVC v{msvc_full_ver} and Windows SDK v{sdk_ver}")
  accept = input(f"Do you accept Visual Studio license at {license} [Y/N] ? ")
  if not accept or accept[0].lower() != "y":
    sys.exit(0)

OUTPUT.mkdir(exist_ok=True)
DOWNLOADS.mkdir(exist_ok=True)


msvc_packages = [
  f"microsoft.visualcpp.dia.sdk",
  f"microsoft.vc.{msvc_pkg_ver}.crt.headers.base",
  f"microsoft.vc.{msvc_pkg_ver}.crt.source.base",
  f"microsoft.vc.{msvc_pkg_ver}.asan.headers.base",
  f"microsoft.vc.{msvc_pkg_ver}.pgo.headers.base",
]

for target in targets:
  msvc_packages += [
    f"microsoft.vc.{msvc_pkg_ver}.tools.host{host}.target{target}.base",
    f"microsoft.vc.{msvc_pkg_ver}.tools.host{host}.target{target}.res.base",
    f"microsoft.vc.{msvc_pkg_ver}.crt.{target}.desktop.base",
    f"microsoft.vc.{msvc_pkg_ver}.crt.{target}.store.base",
    f"microsoft.vc.{msvc_pkg_ver}.premium.tools.host{host}.target{target}.base",
    f"microsoft.vc.{msvc_pkg_ver}.pgo.{target}.base",
  ]
  if target in ["x86", "x64"]:
    msvc_packages += [f"microsoft.vc.{msvc_pkg_ver}.asan.{target}.base"]

  redist_suffix = ".onecore.desktop" if target == "arm" else ""
  redist_pkg = f"microsoft.vc.{msvc_pkg_ver}.crt.redist.{target}{redist_suffix}.base"
  if redist_pkg not in packages:
    redist_name = f"microsoft.visualcpp.crt.redist.{target}{redist_suffix}"
    redist = first(packages[redist_name])
    if redist and "dependencies" in redist:
      redist_pkg = first(redist["dependencies"], lambda dep: dep.endswith(".base"))
      if redist_pkg:
        redist_pkg = redist_pkg.lower()
  if redist_pkg:
    msvc_packages += [redist_pkg]

missing_packages = []
successful_packages = []
_packages_lock = __import__("threading").Lock()

print(f"\n{'='*70}")
print(f"Downloading MSVC v{msvc_full_ver} packages...")
print(f"{'='*70}\n")

import concurrent.futures, threading

_print_lock = threading.Lock()

def _download_one_package(pkg):
  if pkg not in packages:
    with _print_lock:
      print(f"⚠ {pkg} ... MISSING")
    with _packages_lock:
      missing_packages.append(pkg)
    return

  p = first(packages[pkg], lambda p: p.get("language") in (None, "en-US"))
  if not p:
    with _print_lock:
      print(f"⚠ {pkg} ... NO SUITABLE LANGUAGE")
    with _packages_lock:
      missing_packages.append(pkg)
    return

  for payload in p["payloads"]:
    filename = payload["fileName"]
    fpath = DOWNLOADS / filename
    if fpath.exists():
      data = fpath.read_bytes()
      if hashlib.sha256(data).hexdigest() == payload["sha256"].lower():
        with _print_lock:
          print(f"\r{filename} ... OK (cached)")
        global total_cached
        with _packages_lock:
          total_cached += len(data)
        with zipfile.ZipFile(DOWNLOADS / filename) as z:
          for name in z.namelist():
            if name.startswith("Contents/"):
              out = OUTPUT / Path(name).relative_to("Contents")
              out.parent.mkdir(parents=True, exist_ok=True)
              out.write_bytes(z.read(name))
        continue

    with _print_lock:
      print(f"  Downloading {filename}...")
    req = urllib.request.Request(payload["url"], headers={
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    })
    with urllib.request.urlopen(req, context=ssl_context, timeout=120) as res:
      total = int(res.headers.get("Content-Length", 0))
      data = b""
      while True:
        block = res.read(1 << 20)
        if not block:
          break
        data += block
        if total:
          perc = len(data) * 100 // total
          with _print_lock:
            print(f"\r  {filename} ... {perc}%", end="", flush=True)
    with _print_lock:
      print(f"\r  {filename} ... done ({len(data)//1024} KB)")

    digest = hashlib.sha256(data).hexdigest()
    if payload["sha256"].lower() != digest:
      with _print_lock:
        print(f"  ⚠ Hash mismatch for {filename} — skipping")
      return

    fpath.write_bytes(data)
    global total_download
    with _packages_lock:
      total_download += len(data)

    with zipfile.ZipFile(DOWNLOADS / filename) as z:
      for name in z.namelist():
        if name.startswith("Contents/"):
          out = OUTPUT / Path(name).relative_to("Contents")
          out.parent.mkdir(parents=True, exist_ok=True)
          out.write_bytes(z.read(name))

  with _packages_lock:
    successful_packages.append(pkg)


MAX_WORKERS = 4

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
  futures = {executor.submit(_download_one_package, pkg): pkg for pkg in sorted(msvc_packages)}
  for future in concurrent.futures.as_completed(futures):
    try:
      future.result()
    except Exception as e:
      pkg = futures[future]
      with _print_lock:
        print(f"⚠ Error downloading {pkg}: {e}")
      with _packages_lock:
        missing_packages.append(pkg)


print(f"\n{'='*70}")
print(f"Downloading Windows SDK v{sdk_full_ver} packages...")
print(f"{'='*70}\n")

msi = []
_used_winsdksetup = False
_skip_msi_unpack = False

if winsdksetup_url:
  layout_dir  = _sdk_layout_dir
  marker_file = _sdk_marker_file
  cached_ver  = _sdk_cached_ver
  _kits_check = _sdk_kits_check


  winsdksetup_path     = DOWNLOADS / "winsdksetup.exe"
  winsdksetup_ver_file = DOWNLOADS / "winsdksetup.version"
  cached_setup_ver     = winsdksetup_ver_file.read_text().strip() if winsdksetup_ver_file.exists() else ""

  base_ver = f"10.0.{sdk_ver}.0"
  if sdk_full_ver != base_ver:
    for pkg in sdk_packages:
      stale = DOWNLOADS / pkg
      if stale.exists():
        print(f"  Removing stale cached MSI: {pkg}")
        stale.unlink()
    for cab in DOWNLOADS.glob("*.cab"):
      print(f"  Removing stale cached CAB: {cab.name}")
      cab.unlink()

  if winsdksetup_path.exists() and cached_setup_ver == sdk_full_ver:
    print(f"  winsdksetup.exe ({sdk_full_ver}) already downloaded — skipping.")
  else:
    print(f"  Downloading winsdksetup.exe ({sdk_full_ver})...")
    sdk_data = io.BytesIO()
    with urllib.request.urlopen(winsdksetup_url, context=ssl_context) as res:
      total = int(res.headers.get("Content-Length", 0))
      size = 0
      while True:
        block = res.read(1 << 20)
        if not block:
          break
        sdk_data.write(block)
        size += len(block)
        if total:
          perc = size * 100 // total
          print(f"\rwinsdksetup.exe ... {perc}%", end="")
    print()
    winsdksetup_path.write_bytes(sdk_data.getvalue())
    winsdksetup_ver_file.write_text(sdk_full_ver)
    total_sdk_download += size

  _pre_layout_manifest = _load_sdk_msi_manifest(DOWNLOADS)

  if not args.sdk_use_cache:
    if layout_dir.exists():
      print(f"  Wiping layout cache -- re-fetching all MSIs from Microsoft's CDN...")
      shutil.rmtree(layout_dir)
  else:
    print(f"  --sdk-use-cache: reusing layout folder (MSIs NOT re-verified against server)")
  layout_dir.mkdir(exist_ok=True)

  print(f"  Running winsdksetup.exe /layout to fetch SDK MSIs...")
  print(f"  (Monitoring download folder every 5s for activity...)")
  import threading, time

  proc = subprocess.Popen([
    str(winsdksetup_path),
    "/layout", str(layout_dir),
    "/quiet",
    "/norestart",
  ])

  _stall_secs = [0]

  def _monitor_layout():
    last_size = 0
    while proc.poll() is None:
      time.sleep(5)
      try:
        files = list(layout_dir.rglob("*"))
        total_bytes = sum(f.stat().st_size for f in files if f.is_file())
        count = sum(1 for f in files if f.suffix.lower() == ".msi")
        delta = total_bytes - last_size
        if delta == 0:
          _stall_secs[0] += 5
        else:
          _stall_secs[0] = 0
        stall_note = f"  ⚠ No change for {_stall_secs[0]}s" if _stall_secs[0] >= 15 else ""
        print(f"\r  Layout: {count} MSI(s)  {total_bytes>>20} MB total  (+{delta>>20} MB in last 5s){stall_note}    ", end="", flush=True)
        last_size = total_bytes
      except Exception:
        pass
    print()

  t = threading.Thread(target=_monitor_layout, daemon=True)
  t.start()
  try:
    while proc.poll() is None:
      time.sleep(1)
  except KeyboardInterrupt:
    print(f"\n  Interrupted — killing winsdksetup...")
    proc.kill()
    proc.wait()
    t.join(timeout=2)
    raise
  proc.wait()
  t.join(timeout=2)
  total_sdk_download += sum(
          f.stat().st_size
          for f in layout_dir.rglob("*")
          if f.is_file()
  )

  ret = proc.returncode
  if ret != 0:
    print(f"  Note: winsdksetup.exe /layout returned exit code {ret} (often normal).")


  found_msis = {p.name: p for p in layout_dir.rglob("*.msi")}
  _layout_total_mb = sum(f.stat().st_size for f in layout_dir.rglob("*") if f.is_file()) >> 20
  print(f"\n  Found {len(found_msis)} MSI(s) in layout folder  ({_layout_total_mb} MB total).")

  if found_msis:
    print(f"  Hashing {len(found_msis)} MSI(s) and comparing against install baseline...")
    _post_layout_manifest = {}
    for _p in sorted(found_msis.values(), key=lambda x: x.name):
      print(f"  {_p.name} ...", end=" ", flush=True)
      _sha = _sha256_file(_p)
      _post_layout_manifest[_p.name] = {"sha256": _sha}
      print("OK")
    _manifest_path = DOWNLOADS / _SDK_MSI_MANIFEST_FILE
    _manifest_path.write_text(json.dumps(_post_layout_manifest, indent=2))

    _sdk_msi_changed = False
    for _name in sdk_packages:
      if _name not in found_msis:
        continue
      _pre_sha = _pre_layout_manifest.get(_name, {}).get("sha256")
      _post_sha = _post_layout_manifest.get(_name, {}).get("sha256")
      if _pre_sha is not None and _pre_sha == _post_sha:
        total_sdk_unchanged += found_msis[_name].stat().st_size
      else:
        _sdk_msi_changed = True
    if not _sdk_msi_changed:
      total_sdk_unchanged = total_sdk_download
    found_msis = {p.name: p for p in layout_dir.rglob("*.msi")}
    for pkg in sorted(sdk_packages):
      if pkg in found_msis:
        msi.append(found_msis[pkg])
    _used_winsdksetup = True

    _skip_msi_unpack = (
      _sdk_binary_ver is not None and
      _sdk_binary_ver == sdk_full_ver and
      not _sdk_msi_changed
    )
  else:
    print("  WARNING: No MSIs found after winsdksetup /layout — falling back to VS manifest.")

if not _used_winsdksetup and not sdk_in_manifest:
  sys.exit(
    f"ERROR: SDK {sdk_ver} is not in the VS manifest and winsdksetup /layout found no MSIs.\n"
    f"Cannot install SDK {sdk_ver} — check your internet connection and try again."
  )

if not _used_winsdksetup:
  with tempfile.TemporaryDirectory(dir=DOWNLOADS) as d:
    sdk_pid = sdk[sdk_ver]
    sdk_pkg = packages[sdk_pid][0]
    sdk_pkg = packages[first(sdk_pkg["dependencies"]).lower()][0]

    cabs = []
    for pkg in sorted(sdk_packages):
      payload = first(sdk_pkg["payloads"], lambda p: p["fileName"] == f"Installers\\{pkg}")
      if payload is None:
        continue
      msi.append(DOWNLOADS / pkg)
      data = download_progress(payload["url"], payload["sha256"], pkg)
      cabs += list(get_msi_cabs(data))

    for pkg in cabs:
      payload = first(sdk_pkg["payloads"], lambda p: p["fileName"] == f"Installers\\{pkg}")
      download_progress(payload["url"], payload["sha256"], pkg)

if _skip_msi_unpack if winsdksetup_url else False:
  print("  SDK already unpacked into output folder — skipping msiexec.")
else:
  print("\nUnpacking msi files...")
  for m in msi:
    subprocess.check_call(f'msiexec.exe /a "{m}" /quiet /qn TARGETDIR="{OUTPUT.resolve()}"')
    stub = OUTPUT / m.name
    if stub.exists():
      stub.unlink()
  if _used_winsdksetup:
    marker_file.write_text(sdk_full_ver)


msvcv = msvc_full_ver

_kits_bin = None
for _kits_ver in ["11", "10"]:
  _candidate = OUTPUT / f"Windows Kits/{_kits_ver}/bin"
  if _candidate.exists():
    _kits_bin = _candidate
    _kits_root = OUTPUT / f"Windows Kits/{_kits_ver}"
    break
if _kits_bin is None:
  sys.exit("ERROR: Could not find Windows Kits bin folder in output directory.")
sdkv = first(_kits_bin.glob("*")).name


print(f"\n{'='*70}")
print(f"Post-install SDK binary version check")
print(f"{'='*70}")

_sdk_bin_x64 = _kits_bin / sdkv / "x64"
_rc_exe      = _sdk_bin_x64 / "rc.exe"

if _rc_exe.exists():
  _rc_ver = _get_file_product_version(_rc_exe)
  if _rc_ver:
    print(f"  rc.exe ProductVersion : {_rc_ver}")
    print(f"  Installer reported    : {sdk_full_ver}")
    if _rc_ver == sdk_full_ver:
      print(f"  ✓ Binary version matches installer version exactly")
    else:
      _rc_parts  = _rc_ver.rsplit(".", 1)
      _sdk_parts = sdk_full_ver.rsplit(".", 1)
      if _rc_parts[0] == _sdk_parts[0]:
        print(f"  ⚠ Binary patch differs from installer ({_rc_ver} vs {sdk_full_ver})")
        print(f"    This usually means Microsoft shipped the same binaries in both")
        print(f"    builds — only installer/package metadata changed, not the tools.")
        print(f"    Your SDK is up-to-date; the binary version is NOT a bug.")
      else:
        print(f"  ✗ MISMATCH — binary version does not match installer!")
        print(f"    Expected : {sdk_full_ver}")
        print(f"    Got      : {_rc_ver}")
        print(f"    The installed SDK may be stale. Delete msvc\\Windows Kits and rerun.")
  else:
    print(f"  ⚠ Could not read version from rc.exe (non-standard binary format)")
else:
  print(f"  ⚠ rc.exe not found at {_rc_exe} — skipping binary version check")

print(f"{'='*70}")


redist = OUTPUT / "VC/Redist"

if redist.exists():
  redistv = first((redist / "MSVC").glob("*")).name
  src = redist / "MSVC" / redistv / "debug_nonredist"
  for target in targets:
    for f in (src / target).glob("**/*.dll"):
      dst = OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{host}" / target
      f.replace(dst / f.name)

  shutil.rmtree(redist)


msdia140dll = {
  "x86": "msdia140.dll",
  "x64": "amd64/msdia140.dll",
  "arm": "arm/msdia140.dll",
  "arm64": "arm64/msdia140.dll",
}

dst = OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{host}"
src = OUTPUT / "DIA%20SDK/bin" / msdia140dll[host]
for target in targets:
  shutil.copyfile(src, dst / target / src.name)

shutil.rmtree(OUTPUT / "DIA%20SDK")


shutil.rmtree(OUTPUT / "Common7", ignore_errors=True)
shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / "Auxiliary", ignore_errors=True)
for target in targets:
  for f in [f"store", "uwp", "enclave", "onecore"]:
    shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / "lib" / target / f, ignore_errors=True)
  shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{host}" / target / "onecore", ignore_errors=True)
for f in ["Catalogs", "DesignTime", f"bin/{sdkv}/chpe", f"Lib/{sdkv}/ucrt_enclave"]:
  shutil.rmtree(_kits_root / f, ignore_errors=True)
for arch in ["x86", "x64", "arm", "arm64"]:
  if arch not in targets:
    shutil.rmtree(_kits_root / "Lib" / sdkv / "ucrt" / arch, ignore_errors=True)
    shutil.rmtree(_kits_root / "Lib" / sdkv / "um" / arch, ignore_errors=True)
  if arch != host:
    shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{arch}", ignore_errors=True)
    shutil.rmtree(_kits_root / "bin" / sdkv / arch, ignore_errors=True)

for target in targets:
  (OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{host}/{target}/vctip.exe").unlink(missing_ok=True)


build = OUTPUT / "VC/Auxiliary/Build"
build.mkdir(parents=True, exist_ok=True)
(build / "vcvarsall.bat").write_text("rem both bat files are here only for nvcc, do not call them manually")
(build / "vcvars64.bat").touch()


_kits_rel = _kits_root.relative_to(OUTPUT)  # e.g. "Windows Kits\10" or "Windows Kits\11"

for target in targets:

  SETUP = fr"""@echo off

set VSCMD_ARG_HOST_ARCH={host}
set VSCMD_ARG_TGT_ARCH={target}

set VCToolsVersion={msvcv}
set WindowsSDKVersion={sdkv}\

set VCToolsInstallDir=%~dp0VC\Tools\MSVC\{msvcv}\
set WindowsSdkBinPath=%~dp0{_kits_rel}\bin\

set PATH=%~dp0VC\Tools\MSVC\{msvcv}\bin\Host{host}\{target};%~dp0{_kits_rel}\bin\{sdkv}\{host};%~dp0{_kits_rel}\bin\{sdkv}\{host}\ucrt;%PATH%
set INCLUDE=%~dp0VC\Tools\MSVC\{msvcv}\include;%~dp0{_kits_rel}\Include\{sdkv}\ucrt;%~dp0{_kits_rel}\Include\{sdkv}\shared;%~dp0{_kits_rel}\Include\{sdkv}\um;%~dp0{_kits_rel}\Include\{sdkv}\winrt;%~dp0{_kits_rel}\Include\{sdkv}\cppwinrt
set LIB=%~dp0VC\Tools\MSVC\{msvcv}\lib\{target};%~dp0{_kits_rel}\Lib\{sdkv}\ucrt\{target};%~dp0{_kits_rel}\Lib\{sdkv}\um\{target}
"""
  (OUTPUT / f"setup_{target}.bat").write_text(SETUP)

print(f"\n{'='*70}")
print(f"Installation Summary")
print(f"{'='*70}")
print(f"MSVC version installed: {msvcv}")
print(f"SDK installer version : {sdk_full_ver}")
print(f"SDK folder version    : {sdkv}  (on-disk folder name, always ends in .0)")
print(f"Packages downloaded: {len(successful_packages)}/{len(msvc_packages)}")
if missing_packages:
  print(f"Packages missing: {len(missing_packages)} ⚠")
  print(f"\nMissing packages:")
  for pkg in missing_packages:
    print(f"  - {pkg}")
else:
  print(f"Packages missing: 0 ✓")
_sdk_changed_mb  = (total_sdk_download - total_sdk_unchanged) >> 20
_sdk_total_mb    = total_sdk_download >> 20
_sdk_reused_mb   = total_sdk_unchanged >> 20
_msvc_download   = total_download >> 20
_msvc_cached     = total_cached >> 20
if _msvc_download == 0 and _msvc_cached > 0:
  print(f"MSVC downloaded  : 0 MB  (all {_msvc_cached} MB unchanged ✓)")
elif _msvc_cached > 0:
  print(f"MSVC downloaded  : {_msvc_download} MB  ({_msvc_cached} MB unchanged)")
else:
  print(f"MSVC downloaded  : {_msvc_download} MB")
if _used_winsdksetup:
  if args.sdk_use_cache:
    print(f"SDK downloaded   : 0 MB  (--sdk-use-cache: local files reused, not server-verified)")
  elif _sdk_changed_mb == 0:
    print(f"SDK downloaded   : {_sdk_total_mb} MB  (all identical to last install ✓)")
  else:
    print(f"SDK downloaded   : {_sdk_total_mb} MB  ({_sdk_changed_mb} MB changed, {_sdk_reused_mb} MB unchanged)")
print(f"{'='*70}")

if missing_packages:
  print(f"\n⚠ WARNING: Toolchain may be incomplete!")
  print(f"This usually means Microsoft is still uploading this version.")
  print(f"The installation will work but some features may be unavailable.")
else:
  print(f"\n✓ Installation complete!")

print(f"\nTo use the toolchain, run: setup_{targets[0]}.bat")
