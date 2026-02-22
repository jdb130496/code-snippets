#!/usr/bin/env python3

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
from pathlib import Path

OUTPUT = Path("msvc")         # output folder
DOWNLOADS = Path("downloads") # temporary download files

# NOTE: not all host & target architecture combinations are supported

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

def download(url):
  with urllib.request.urlopen(url, context=ssl_context) as res:
    return res.read()

total_download = 0

def download_progress(url, check, filename):
  fpath = DOWNLOADS / filename
  if fpath.exists():
    data = fpath.read_bytes()
    if hashlib.sha256(data).hexdigest() == check.lower():
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
      sys.exit(f"Hash mismatch for f{pkg}")
    total_download += len(data)
    return data

# super crappy msi format parser just to find required .cab files
def get_msi_cabs(msi):
  index = 0
  while True:
    index = msi.find(b".cab", index+4)
    if index < 0:
      return
    yield msi[index-32:index+4].decode("ascii")

def first(items, cond = lambda x: True):
  return next((item for item in items if cond(item)), None)


### parse command-line arguments

ap = argparse.ArgumentParser()
ap.add_argument("--show-versions", action="store_true", help="Show available MSVC and Windows SDK versions")
ap.add_argument("--accept-license", action="store_true", help="Automatically accept license")
ap.add_argument("--msvc-version", help="Get specific MSVC version")
ap.add_argument("--sdk-version", help="Get specific Windows SDK version")
ap.add_argument("--vs", default=DEFAULT_VERSION, help=f"Visual Studio version to use for installation", choices=ALL_VERSIONS)
ap.add_argument("--insiders", "--preview", action="store_true", help="Use insiders/preview versions")
ap.add_argument("--target", default=DEFAULT_TARGET, help=f"Target architectures, comma separated ({','.join(ALL_TARGETS)})")
ap.add_argument("--host", default=DEFAULT_HOST, help=f"Host architecture", choices=ALL_HOSTS)
args = ap.parse_args()

host = args.host
targets = args.target.split(',')
for target in targets:
  if target not in ALL_TARGETS:
    sys.exit(f"Unknown {target} target architecture!")


### get main manifest

URL = MANIFEST_URLS[args.vs][args.insiders]

try:
  manifest = json.loads(download(URL))
except urllib.error.URLError as err:
  import ssl
  if isinstance(err.args[0], ssl.SSLCertVerificationError):
    # for more info about Python & issues with Windows certificates see https://stackoverflow.com/a/52074591
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

### download VS manifest

ITEM_NAME = "Microsoft.VisualStudio.Manifests.VisualStudioPreview" if args.insiders else "Microsoft.VisualStudio.Manifests.VisualStudio"

vs = first(manifest["channelItems"], lambda x: x["id"] == ITEM_NAME)
payload = vs["payloads"][0]["url"]

vsmanifest = json.loads(download(payload))


### find MSVC & WinSDK versions

packages = {}
for p in vsmanifest["packages"]:
  packages.setdefault(p["id"].lower(), []).append(p)

msvc = {}
sdk = {}

for pid,p in packages.items():
  if pid.startswith("Microsoft.VC.".lower()) and pid.endswith(".Tools.HostX64.TargetX64.base".lower()):
    pver = ".".join(pid.split(".")[2:4])
    if pver[0].isnumeric():
      msvc[pver] = pid
  elif pid.startswith("Microsoft.VisualStudio.Component.Windows10SDK.".lower()) or \
       pid.startswith("Microsoft.VisualStudio.Component.Windows11SDK.".lower()):
    pver = pid.split(".")[-1]
    if pver.isnumeric():
      sdk[pver] = pid

if args.show_versions:
  print("MSVC versions:", " ".join(sorted(msvc.keys())))
  print("Windows SDK versions:", " ".join(sorted(sdk.keys())))
  sys.exit(0)

msvc_ver = args.msvc_version or max(sorted(msvc.keys()))
sdk_ver = args.sdk_version or max(sorted(sdk.keys()))

# Version cache file — survives across runs so we can fall back if the server
# starts returning a malformed/changed package ID format again.
VERSION_CACHE = DOWNLOADS / "versions.json"

def load_version_cache():
  if VERSION_CACHE.exists():
    try:
      return json.loads(VERSION_CACHE.read_text())
    except Exception:
      pass
  return {}

def save_version_cache(cache):
  try:
    DOWNLOADS.mkdir(exist_ok=True)
    VERSION_CACHE.write_text(json.dumps(cache, indent=2))
  except Exception as e:
    print(f"WARNING: could not save version cache: {e}")

def is_valid_full_version(ver):
  """A proper MSVC version has 3 or 4 all-numeric segments, e.g. 14.51.36014 or 14.50.35717.0."""
  parts = ver.split(".")
  return len(parts) in (3, 4) and all(p.isnumeric() for p in parts)

def resolve_msvc_full_version(msvc_pid, packages):
  """
  Extract the real 4-part full version for MSVC from the package metadata.
  Prefers the package's 'version' field (reliable), falls back to slicing the
  package ID (which broke when Microsoft changed the ID format in early 2026).
  """
  # Primary: use the 'version' field that Microsoft includes in each package entry
  pkg_entry = first(packages.get(msvc_pid, []))
  if pkg_entry and "version" in pkg_entry:
    ver = pkg_entry["version"]
    if is_valid_full_version(ver):
      return ver
    print(f"WARNING: package 'version' field looks unexpected ({ver!r}), trying ID-based fallback")

  # Fallback: slice the package ID string (the old approach, works when IDs are
  # formatted as microsoft.vc.14.50.35717.0.tools.hostx64.targetx64.base)
  ver_from_id = ".".join(msvc_pid.split(".")[2:6])
  if is_valid_full_version(ver_from_id):
    return ver_from_id

  return None  # both methods failed

if msvc_ver in msvc:
  msvc_pid = msvc[msvc_ver]
  msvc_short_ver = msvc_ver  # 2-part prefix used in package IDs, e.g. "14.51"
  resolved = resolve_msvc_full_version(msvc_pid, packages)

  # Cache key includes the VS channel and short version so different channels
  # don't overwrite each other (e.g. insiders vs stable, 2022 vs 2026).
  cache_key = f"{'insiders' if args.insiders else 'stable'}-{args.vs}-msvc-{msvc_ver}"
  cache = load_version_cache()

  if resolved is None:
    # Server gave us something we can't parse — check the cache for a known-good value
    if cache_key in cache:
      cached = cache[cache_key]
      msvc_ver = cached["msvc_full_ver"]
      msvc_short_ver = cached.get("msvc_short_ver", msvc_short_ver)
      print(f"WARNING: could not determine full MSVC version from server response.")
      print(f"WARNING: falling back to cached version {msvc_ver!r} from a previous successful run.")
    else:
      sys.exit(
        f"ERROR: could not determine a valid MSVC version from the server.\n"
        f"  package ID  : {msvc_pid}\n"
        f"  ID-slice    : {'.'.join(msvc_pid.split('.')[2:6])}\n"
        f"  package ver : {first(packages.get(msvc_pid, []), lambda x: True) and first(packages.get(msvc_pid, [])).get('version', 'N/A')}\n"
        f"No cached version available. Run once with a working server or supply --msvc-version explicitly."
      )
  else:
    msvc_ver = resolved
    # Persist both versions so future runs can fall back if the format breaks again
    cache[cache_key] = {"msvc_full_ver": msvc_ver, "msvc_short_ver": msvc_short_ver, "sdk_ver": sdk_ver}
    save_version_cache(cache)
    print(f"NOTE: resolved MSVC full version: {msvc_ver} (package ID prefix: {msvc_short_ver})")
else:
  sys.exit(f"Unknown MSVC version: f{args.msvc_version}")

if sdk_ver in sdk:
  sdk_pid = sdk[sdk_ver]
else:
  sys.exit(f"Unknown Windows SDK version: f{args.sdk_version}")

print(f"Downloading MSVC v{msvc_ver} and Windows SDK v{sdk_ver}")


### agree to license

tools = first(manifest["channelItems"], lambda x: x["id"] == "Microsoft.VisualStudio.Product.BuildTools")
resource = first(tools["localizedResources"], lambda x: x["language"] == "en-us")
license = resource["license"]

if not args.accept_license:
  accept = input(f"Do you accept Visual Studio license at {license} [Y/N] ? ")
  if not accept or accept[0].lower() != "y":
    sys.exit(0)

OUTPUT.mkdir(exist_ok=True)
DOWNLOADS.mkdir(exist_ok=True)


### download MSVC

# msvc_short_ver is the 2-part prefix used in package IDs (e.g. "14.51").
# msvc_ver is the full resolved version used for folder paths (e.g. "14.51.36014").
# These are the same on older manifests where the full version is in the package ID,
# but differ on newer manifests (VS 2026 insiders) where IDs use only the short prefix.

msvc_packages = [
  f"microsoft.visualcpp.dia.sdk",
  f"microsoft.vc.{msvc_short_ver}.crt.headers.base",
  f"microsoft.vc.{msvc_short_ver}.crt.source.base",
  f"microsoft.vc.{msvc_short_ver}.asan.headers.base",
  f"microsoft.vc.{msvc_short_ver}.pgo.headers.base",
]

for target in targets:
  msvc_packages += [
    f"microsoft.vc.{msvc_short_ver}.tools.host{host}.target{target}.base",
    f"microsoft.vc.{msvc_short_ver}.tools.host{host}.target{target}.res.base",
    f"microsoft.vc.{msvc_short_ver}.crt.{target}.desktop.base",
    f"microsoft.vc.{msvc_short_ver}.crt.{target}.store.base",
    f"microsoft.vc.{msvc_short_ver}.premium.tools.host{host}.target{target}.base",
    f"microsoft.vc.{msvc_short_ver}.pgo.{target}.base",
  ]
  if target in ["x86", "x64"]:
    msvc_packages += [f"microsoft.vc.{msvc_short_ver}.asan.{target}.base"]

  redist_suffix = ".onecore.desktop" if target == "arm" else ""
  redist_pkg = f"microsoft.vc.{msvc_short_ver}.crt.redist.{target}{redist_suffix}.base"
  if redist_pkg not in packages:
    redist_name = f"microsoft.visualcpp.crt.redist.{target}{redist_suffix}"
    redist = first(packages[redist_name])
    redist_pkg = first(redist["dependencies"], lambda dep: dep.endswith(".base")).lower()
  msvc_packages += [redist_pkg]

for pkg in sorted(msvc_packages):
  if pkg not in packages:
    print(f"\r{pkg} ... !!! MISSING !!!")
    continue
  p = first(packages[pkg], lambda p: p.get("language") in (None, "en-US"))
  for payload in p["payloads"]:
    filename = payload["fileName"]
    download_progress(payload["url"], payload["sha256"], filename)
    with zipfile.ZipFile(DOWNLOADS / filename) as z:
      for name in z.namelist():
        if name.startswith("Contents/"):
          out = OUTPUT / Path(name).relative_to("Contents")
          out.parent.mkdir(parents=True, exist_ok=True)
          out.write_bytes(z.read(name))


### download Windows SDK

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

with tempfile.TemporaryDirectory(dir=DOWNLOADS) as d:
  dst = Path(d)

  sdk_pkg = packages[sdk_pid][0]
  sdk_pkg = packages[first(sdk_pkg["dependencies"]).lower()][0]

  msi = []
  cabs = []

  # download msi files
  for pkg in sorted(sdk_packages):
    payload = first(sdk_pkg["payloads"], lambda p: p["fileName"] == f"Installers\\{pkg}")
    if payload is None:
      continue
    msi.append(DOWNLOADS / pkg)
    data = download_progress(payload["url"], payload["sha256"], pkg)
    cabs += list(get_msi_cabs(data))

  # download .cab files
  for pkg in cabs:
    payload = first(sdk_pkg["payloads"], lambda p: p["fileName"] == f"Installers\\{pkg}")
    download_progress(payload["url"], payload["sha256"], pkg)

  print("Unpacking msi files...")

  # run msi installers
  for m in msi:
    subprocess.check_call(f'msiexec.exe /a "{m}" /quiet /qn TARGETDIR="{OUTPUT.resolve()}"')
    (OUTPUT / m.name).unlink()


### versions

msvcv = first((OUTPUT / "VC/Tools/MSVC").glob("*")).name
sdkv = first((OUTPUT / "Windows Kits/10/bin").glob("*")).name


# place debug CRT runtime files into MSVC bin folder (not what real Visual Studio installer does... but is reasonable)
# NOTE: these are Target architecture, not Host architecture binaries

redist = OUTPUT / "VC/Redist"

if redist.exists():
  redistv = first((redist / "MSVC").glob("*")).name
  src = redist / "MSVC" / redistv / "debug_nonredist"
  for target in targets:
    for f in (src / target).glob("**/*.dll"):
      dst = OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{host}" / target
      f.replace(dst / f.name)

  shutil.rmtree(redist)


# copy msdia140.dll file into MSVC bin folder
# NOTE: this is meant only for development - always Host architecture, even when placed into all Target architecture folders

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


### cleanup

shutil.rmtree(OUTPUT / "Common7", ignore_errors=True)
shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / "Auxiliary", ignore_errors=True)
for target in targets:
  for f in [f"store", "uwp", "enclave", "onecore"]:
    shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / "lib" / target / f, ignore_errors=True)
  shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{host}" / target / "onecore", ignore_errors=True)
for f in ["Catalogs", "DesignTime", f"bin/{sdkv}/chpe", f"Lib/{sdkv}/ucrt_enclave"]:
  shutil.rmtree(OUTPUT / "Windows Kits/10" / f, ignore_errors=True)
for arch in ["x86", "x64", "arm", "arm64"]:
  if arch not in targets:
    shutil.rmtree(OUTPUT / "Windows Kits/10/Lib" / sdkv / "ucrt" / arch, ignore_errors=True)
    shutil.rmtree(OUTPUT / "Windows Kits/10/Lib" / sdkv / "um" / arch, ignore_errors=True)
  if arch != host:
    shutil.rmtree(OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{arch}", ignore_errors=True)
    shutil.rmtree(OUTPUT / "Windows Kits/10/bin" / sdkv / arch, ignore_errors=True)

# executable that is collecting & sending telemetry every time cl/link runs
for target in targets:
  (OUTPUT / "VC/Tools/MSVC" / msvcv / f"bin/Host{host}/{target}/vctip.exe").unlink(missing_ok=True)


# extra files for nvcc
build = OUTPUT / "VC/Auxiliary/Build"
build.mkdir(parents=True, exist_ok=True)
(build / "vcvarsall.bat").write_text("rem both bat files are here only for nvcc, do not call them manually")
(build / "vcvars64.bat").touch()

### setup.bat

for target in targets:

  SETUP = fr"""@echo off

set VSCMD_ARG_HOST_ARCH={host}
set VSCMD_ARG_TGT_ARCH={target}

set VCToolsVersion={msvcv}
set WindowsSDKVersion={sdkv}\

set VCToolsInstallDir=%~dp0VC\Tools\MSVC\{msvcv}\
set WindowsSdkBinPath=%~dp0Windows Kits\10\bin\

set PATH=%~dp0VC\Tools\MSVC\{msvcv}\bin\Host{host}\{target};%~dp0Windows Kits\10\bin\{sdkv}\{host};%~dp0Windows Kits\10\bin\{sdkv}\{host}\ucrt;%PATH%
set INCLUDE=%~dp0VC\Tools\MSVC\{msvcv}\include;%~dp0Windows Kits\10\Include\{sdkv}\ucrt;%~dp0Windows Kits\10\Include\{sdkv}\shared;%~dp0Windows Kits\10\Include\{sdkv}\um;%~dp0Windows Kits\10\Include\{sdkv}\winrt;%~dp0Windows Kits\10\Include\{sdkv}\cppwinrt
set LIB=%~dp0VC\Tools\MSVC\{msvcv}\lib\{target};%~dp0Windows Kits\10\Lib\{sdkv}\ucrt\{target};%~dp0Windows Kits\10\Lib\{sdkv}\um\{target}
"""
  (OUTPUT / f"setup_{target}.bat").write_text(SETUP)

print(f"Total downloaded: {total_download>>20} MB")
print("Done!")
