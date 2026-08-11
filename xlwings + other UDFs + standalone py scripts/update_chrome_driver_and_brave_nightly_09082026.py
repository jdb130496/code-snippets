import requests
import zipfile
import os
import shutil
import sys
import psutil
import subprocess
import time
from pathlib import Path
from packaging.version import Version

# ── CONFIG ─────────────────────────────────────────────────────────────────
PORTABLE_DIR      = r"D:\Programs\brave"
DOWNLOAD_DIR      = r"D:\Programs\brave\_update_tmp"
CHROMEDRIVER_DIR  = r"D:\Programs\brave\chromedriver"
VERSION_FILE      = os.path.join(PORTABLE_DIR, "brave_portable_version.txt")
BRAVE_EXE         = os.path.join(PORTABLE_DIR, "brave.exe")

GITHUB_RELEASES_API = "https://api.github.com/repos/brave/brave-browser/releases?per_page=20"
CFT_API             = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
ASSET_SUFFIX        = "win32-x64.zip"
# ───────────────────────────────────────────────────────────────────────────


def get_current_version():
    if os.path.exists(VERSION_FILE):
        return Path(VERSION_FILE).read_text().strip()
    subdirs = [
        d for d in os.listdir(PORTABLE_DIR)
        if os.path.isdir(os.path.join(PORTABLE_DIR, d))
        and d.replace(".", "").isdigit()
        and not d.startswith("_")
    ]
    if subdirs:
        detected = sorted(subdirs, key=lambda x: Version(x))[-1]
        print(f"Auto-detected installed version from folder: {detected}")
        return detected
    return None


def save_current_version(version):
    Path(VERSION_FILE).write_text(version)


def brave_version_to_comparable(v):
    """Extract last 3 parts: '151.1.95.52' → '1.95.52'"""
    parts = v.lstrip("v").split(".")
    return ".".join(parts[-3:])


def get_chromium_major():
    subdirs = [
        d for d in os.listdir(PORTABLE_DIR)
        if os.path.isdir(os.path.join(PORTABLE_DIR, d))
        and d.replace(".", "").isdigit()
        and not d.startswith("_")
    ]
    if not subdirs:
        raise RuntimeError("Could not find versioned subfolder in portable Brave dir")
    latest_folder = sorted(subdirs, key=lambda x: Version(x))[-1]
    major = latest_folder.split(".")[0]
    print(f"Detected Brave folder: {latest_folder} → Chromium major: {major}")
    return major


def get_latest_nightly():
    """Query GitHub releases API directly — always up to date."""
    print("Fetching latest Brave Nightly from GitHub releases API...")
    headers = {"Accept": "application/vnd.github+json"}
    r = requests.get(GITHUB_RELEASES_API, headers=headers, timeout=30)
    r.raise_for_status()
    releases = r.json()

    nightlies = [
        rel for rel in releases
        if rel.get("prerelease") and
        "nightly" in rel.get("name", "").lower()
    ]
    if not nightlies:
        print("No nightly releases found.")
        return None, None, None

    latest = nightlies[0]  # GitHub returns newest first
    tag    = latest["tag_name"]
    assets = latest.get("assets", [])

    win_zip = next(
        (a for a in assets
         if a["name"].endswith(ASSET_SUFFIX)
         and "origin" not in a["name"]),
        None
    )
    if not win_zip:
        print("Windows x64 ZIP not found in latest release assets.")
        return None, None, None

    print(f"Found: {latest['name']} → {win_zip['name']}")
    return tag, win_zip["browser_download_url"], win_zip["name"]


def kill_brave():
    """Kill only portable Brave processes — never touches installed Brave."""
    if len(PORTABLE_DIR) < 10:
        print("PORTABLE_DIR too short — skipping kill for safety.")
        return

    answer = input("\nThis will close all portable Brave windows. Continue? (y/n): ").strip().lower()
    if answer != "y":
        print("Skipping Brave kill — locked files may cause update to fail.")
        return

    killed = []
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            exe = proc.info["exe"]
            if not exe:
                continue
            if os.path.normcase(exe).startswith(os.path.normcase(PORTABLE_DIR)):
                proc.kill()
                killed.append(exe)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        print(f"Killed {len(killed)} portable Brave process(es) from {PORTABLE_DIR}")
        time.sleep(2)
    else:
        print("No portable Brave processes found running.")


def get_chromedriver_url(major):
    print(f"Querying Chrome for Testing API for Chromium {major}...")
    r = requests.get(CFT_API, timeout=30)
    r.raise_for_status()
    data = r.json()

    matches = [
        v for v in data["versions"]
        if v["version"].startswith(f"{major}.")
        and any(
            d["platform"] == "win64"
            for d in v.get("downloads", {}).get("chromedriver", [])
        )
    ]
    if not matches:
        raise RuntimeError(f"No chromedriver found for Chromium {major}")

    latest = sorted(matches, key=lambda x: Version(x["version"]))[-1]
    url = next(
        d["url"] for d in latest["downloads"]["chromedriver"]
        if d["platform"] == "win64"
    )
    print(f"Found chromedriver {latest['version']}")
    return latest["version"], url


def ensure_chromedriver():
    major = get_chromium_major()
    version, url = get_chromedriver_url(major)

    version_file = os.path.join(CHROMEDRIVER_DIR, "version.txt")
    exe_path     = os.path.join(CHROMEDRIVER_DIR, "chromedriver.exe")

    if os.path.exists(version_file) and os.path.exists(exe_path):
        installed = open(version_file).read().strip()
        if installed == version:
            print(f"Chromedriver {version} already up to date — skipping download.")
            return

    print(f"Downloading chromedriver {version}...")
    os.makedirs(CHROMEDRIVER_DIR, exist_ok=True)

    r = requests.get(url, timeout=60)
    r.raise_for_status()
    zip_path = os.path.join(CHROMEDRIVER_DIR, "chromedriver.zip")
    with open(zip_path, "wb") as f:
        f.write(r.content)

    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if member.endswith("chromedriver.exe"):
                with z.open(member) as src, open(exe_path, "wb") as dst:
                    dst.write(src.read())
                break

    os.remove(zip_path)
    open(version_file, "w").write(version)
    print(f"Chromedriver {version} ready at {exe_path}")


def get_chromium_version_from_zip(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        folders = set()
        for name in z.namelist():
            parts = name.split("/")
            if len(parts) > 1 and parts[0].replace(".", "").isdigit():
                folders.add(parts[0])
    return sorted(folders, key=lambda x: Version(x))[-1] if folders else None


def remove_old_version_folder(new_version_folder):
    for entry in os.listdir(PORTABLE_DIR):
        full = os.path.join(PORTABLE_DIR, entry)
        if (os.path.isdir(full)
                and entry.replace(".", "").isdigit()
                and not entry.startswith("_")
                and entry != new_version_folder):
            print(f"Removing old version folder: {entry}")
            shutil.rmtree(full)


def download_file(url, filename):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    zip_path = os.path.join(DOWNLOAD_DIR, filename)
    print(f"Downloading {filename}...")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  {pct}%  ({downloaded/1024/1024:.1f} MB / {total/1024/1024:.1f} MB)", end="")
    print("\nDownload complete.")
    return zip_path


def extract(zip_path, new_ver_folder):
    remove_old_version_folder(new_ver_folder)
    print(f"Extracting to {PORTABLE_DIR}...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(PORTABLE_DIR)


def create_start_menu_shortcut():
    ps_script = r"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Brave Nightly Portable.lnk")
$Shortcut.TargetPath = "D:\Programs\brave\brave.exe"
$Shortcut.Arguments = "--user-data-dir=`"D:\Programs\brave\UserData`""
$Shortcut.WorkingDirectory = "D:\Programs\brave"
$Shortcut.IconLocation = "D:\Programs\brave\brave.exe,0"
$Shortcut.Description = "Brave Nightly Portable"
$Shortcut.Save()
"""
    subprocess.run(["powershell", "-Command", ps_script], check=True)
    print("Start Menu shortcut recreated.")


def main():
    print("=== Brave Nightly Portable Updater ===\n")

    print("--- Chromedriver Check ---")
    try:
        ensure_chromedriver()
    except Exception as e:
        print(f"Warning: Could not update chromedriver: {e}")

    print("\n--- Brave Nightly Check ---")
    current = get_current_version()
    print(f"Current version : {current or 'unknown'}")

    tag, url, filename = get_latest_nightly()
    if not tag:
        print("Could not determine latest version.")
        sys.exit(1)

    print(f"Latest nightly  : {tag}")

    current_core = brave_version_to_comparable(current or "0.0.0")
    tag_core     = brave_version_to_comparable(tag)
    print(f"Comparing: installed={current_core}  github={tag_core}")

    if Version(current_core) >= Version(tag_core):
        print("Brave already up to date.")
    else:
        print(f"\nNew Brave version available: {tag}")
        kill_brave()
        try:
            zip_path = download_file(url, filename)
            new_ver_folder = get_chromium_version_from_zip(zip_path)
            print(f"New version folder in ZIP: {new_ver_folder}")
            extract(zip_path, new_ver_folder)
            save_current_version(new_ver_folder or tag)
            create_start_menu_shortcut()
            print(f"\nBrave updated to {tag}")
        finally:
            if os.path.exists(DOWNLOAD_DIR):
                shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
                print("Cleaned up temp download folder.")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
