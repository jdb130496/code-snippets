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
      sys.exit(f"Hash mismatch for {filename}")
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


### Analyze package availability for all versions

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
    # Define all expected package patterns
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
    
    # Count available packages
    available = 0
    for pattern in expected_patterns:
      if pattern in packages:
        available += 1
    
    if available > best_available:
      best_available = available
      best_version_str = ver_str
      
      # Get full version from metadata
      sample_pkg = f"microsoft.vc.{ver_str}.tools.host{host}.target{targets[0]}.base"
      if sample_pkg in packages:
        pkg_data = first(packages[sample_pkg])
        if pkg_data and "version" in pkg_data:
          best_full_version = pkg_data["version"]
  
  if best_full_version is None:
    best_full_version = best_version_str
  
  total_expected = len(expected_patterns)
  
  return (best_available, total_expected, best_version_str, best_full_version)


### Select best version based on package availability

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

# Select version with most packages available (prioritizing newer versions)
if args.msvc_version:
  if args.msvc_version not in msvc:
    sys.exit(f"ERROR: MSVC version {args.msvc_version} not found")
  selected_short_ver = args.msvc_version
else:
  # Find version with most packages, prefer newer if tied
  best_ver = None
  best_count = -1
  
  for ver in sorted(version_analysis.keys(), reverse=True):  # Newest first
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

sdk_ver = args.sdk_version or max(sorted(sdk.keys()))

if sdk_ver in sdk:
  sdk_pid = sdk[sdk_ver]
else:
  sys.exit(f"Unknown Windows SDK version: {args.sdk_version}")


### agree to license

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


### download MSVC

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

print(f"\n{'='*70}")
print(f"Downloading MSVC v{msvc_full_ver} packages...")
print(f"{'='*70}\n")

for pkg in sorted(msvc_packages):
  if pkg not in packages:
    print(f"⚠ {pkg} ... MISSING")
    missing_packages.append(pkg)
    continue
  
  p = first(packages[pkg], lambda p: p.get("language") in (None, "en-US"))
  if not p:
    print(f"⚠ {pkg} ... NO SUITABLE LANGUAGE")
    missing_packages.append(pkg)
    continue
  
  for payload in p["payloads"]:
    filename = payload["fileName"]
    download_progress(payload["url"], payload["sha256"], filename)
    with zipfile.ZipFile(DOWNLOADS / filename) as z:
      for name in z.namelist():
        if name.startswith("Contents/"):
          out = OUTPUT / Path(name).relative_to("Contents")
          out.parent.mkdir(parents=True, exist_ok=True)
          out.write_bytes(z.read(name))
  
  successful_packages.append(pkg)


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

print(f"\n{'='*70}")
print(f"Downloading Windows SDK v{sdk_ver} packages...")
print(f"{'='*70}\n")

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

  print("\nUnpacking msi files...")

  # run msi installers
  for m in msi:
    subprocess.check_call(f'msiexec.exe /a "{m}" /quiet /qn TARGETDIR="{OUTPUT.resolve()}"')
    (OUTPUT / m.name).unlink()


### Get the actual installed version (use the one we just downloaded)

# The full version folder name should match what we downloaded
msvcv = msvc_full_ver
sdkv = first((OUTPUT / "Windows Kits/10/bin").glob("*")).name


# place debug CRT runtime files into MSVC bin folder
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

print(f"\n{'='*70}")
print(f"Installation Summary")
print(f"{'='*70}")
print(f"MSVC version installed: {msvcv}")
print(f"SDK version installed: {sdkv}")
print(f"Packages downloaded: {len(successful_packages)}/{len(msvc_packages)}")
if missing_packages:
  print(f"Packages missing: {len(missing_packages)} ⚠")
  print(f"\nMissing packages:")
  for pkg in missing_packages:
    print(f"  - {pkg}")
else:
  print(f"Packages missing: 0 ✓")
print(f"Total downloaded: {total_download>>20} MB")
print(f"{'='*70}")

if missing_packages:
  print(f"\n⚠ WARNING: Toolchain may be incomplete!")
  print(f"This usually means Microsoft is still uploading this version.")
  print(f"The installation will work but some features may be unavailable.")
else:
  print(f"\n✓ Installation complete!")

print(f"\nTo use the toolchain, run: setup_{targets[0]}.bat")
