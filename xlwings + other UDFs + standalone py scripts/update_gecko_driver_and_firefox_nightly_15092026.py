import requests
import zipfile
import os
import shutil
import subprocess
import sys
import psutil
import time
from pathlib import Path
from packaging.version import Version

# ── CONFIG ─────────────────────────────────────────────────────────────────
PORTABLE_DIR      = r"D:\Programs\firefox"
USERDATA_DIR      = r"D:\Programs\firefox-userdata"   # ← outside firefox\
DOWNLOAD_DIR      = r"D:\Programs\firefox\_update_tmp"
GECKODRIVER_DIR   = r"D:\Programs\firefox\geckodriver"
VERSION_FILE      = os.path.join(PORTABLE_DIR, "firefox_portable_version.txt")
BUILD_ID_FILE     = os.path.join(PORTABLE_DIR, "firefox_build_id.txt")
FIREFOX_EXE       = os.path.join(PORTABLE_DIR, "firefox.exe")
ARIA2C_PATH       = r"D:\Programs\msys64\ucrt64\bin\aria2c.exe"

FIREFOX_VERSIONS_API = "https://product-details.mozilla.org/1.0/firefox_versions.json"
NIGHTLY_BASE_URL     = "https://download.cdn.mozilla.net/pub/firefox/nightly/latest-mozilla-central"
GECKODRIVER_API      = "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
# ───────────────────────────────────────────────────────────────────────────

def warp_connect():
    subprocess.run(["warp-cli", "connect"], capture_output=True)
    print("WARP connected.")
    time.sleep(3)

def warp_disconnect():
    subprocess.run(["warp-cli", "disconnect"], capture_output=True)
    print("WARP disconnected.")

def get_aria2c():
    """Resolve aria2c: prefer known ucrt64 location, fall back to PATH."""
    if os.path.exists(ARIA2C_PATH):
        return ARIA2C_PATH
    return shutil.which("aria2c")


def download_file(url, filename):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    out_path = os.path.join(DOWNLOAD_DIR, filename)
    aria2c_log = os.path.join(PORTABLE_DIR, "aria2c_last_download.log")
    aria2c_control = out_path + ".aria2"

    aria2c = get_aria2c()
    if aria2c:
        if os.path.exists(aria2c_control):
            print(f"Resuming previous incomplete download of {filename}...")
        else:
            print(f"Downloading {filename} via aria2c (4 connections)...")

        proc = None
        try:
            proc = subprocess.Popen([
                aria2c,
                "--split=4",
                "--max-connection-per-server=4",
                "--min-split-size=10M",
                "--file-allocation=none",
                "--uri-selector=adaptive",
                "--stream-piece-selector=inorder",
                "--max-tries=5",
                "--retry-wait=3",
                "--timeout=30",
                "--connect-timeout=10",
                "--log", aria2c_log,
                "--log-level=notice",
                "--dir", DOWNLOAD_DIR,
                "--out", filename,
                "--console-log-level=notice",
                "--summary-interval=5",
                url
            ])
            proc.wait()
            returncode = proc.returncode
        except KeyboardInterrupt:
            if proc:
                proc.terminate()
                proc.wait()
            print("\nDownload cancelled — partial file kept for resume on next run.")
            raise

        if returncode == 0:
            if os.path.exists(aria2c_control):
                os.remove(aria2c_control)
            print("Download complete.")
            return out_path

        print(f"aria2c failed (exit {returncode}) — falling back to requests...")

    # Fallback: requests streaming download (no resume support)
    if os.path.exists(out_path):
        print(f"Removing partial file from previous run: {filename}")
        os.remove(out_path)

    print(f"Downloading {filename} via requests...")
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\r  {pct}%  ({downloaded/1024/1024:.1f} MB / {total/1024/1024:.1f} MB)", end="")
    except KeyboardInterrupt:
        print("\nDownload cancelled — removing partial file.")
        if os.path.exists(out_path):
            os.remove(out_path)
        raise

    print("\nDownload complete.")
    return out_path

def get_current_version():
    if os.path.exists(VERSION_FILE):
        return Path(VERSION_FILE).read_text().strip()
    # Fallback: read version from application.ini inside the install dir
    app_ini = os.path.join(PORTABLE_DIR, "application.ini")
    if os.path.exists(app_ini):
        for line in Path(app_ini).read_text().splitlines():
            if line.lower().startswith("version="):
                detected = line.split("=", 1)[1].strip()
                print(f"Auto-detected installed version from application.ini: {detected}")
                return detected
    return None


def save_current_version(version):
    Path(VERSION_FILE).write_text(version)


def get_current_build_id():
    """Read the last-installed build ID (e.g. 20260915093012)."""
    if os.path.exists(BUILD_ID_FILE):
        return Path(BUILD_ID_FILE).read_text().strip()
    return None


def save_build_id(build_id):
    Path(BUILD_ID_FILE).write_text(build_id)


def get_latest_nightly():
    """
    Query Mozilla API for version, then fetch buildhub.json for the exact
    build ID. Build ID looks like 20260915093012 — changes every daily build,
    even when the version string stays the same (e.g. 158.0a1).
    """
    print("Fetching latest Firefox Nightly version from Mozilla API...")
    r = requests.get(FIREFOX_VERSIONS_API, timeout=30)
    r.raise_for_status()
    data = r.json()
    version = data.get("FIREFOX_NIGHTLY")
    if not version:
        raise RuntimeError("Could not find FIREFOX_NIGHTLY in Mozilla versions API")
    print(f"Latest Nightly version: {version}")

    # Fetch build ID from buildhub.json
    buildhub_url = f"{NIGHTLY_BASE_URL}/firefox-{version}.en-US.win64.buildhub.json"
    print("Fetching build ID from buildhub.json...")
    r2 = requests.get(buildhub_url, timeout=30)
    r2.raise_for_status()
    build_id = r2.json().get("build", {}).get("id")
    if not build_id:
        raise RuntimeError("Could not find build ID in buildhub.json")
    print(f"Latest build ID       : {build_id}  ({build_id[:8]})")

    filename = f"firefox-{version}.en-US.win64.zip"
    url = f"{NIGHTLY_BASE_URL}/{filename}"
    return version, build_id, url, filename


def get_geckodriver_url():
    print("Querying GitHub for latest geckodriver release...")
    headers = {"Accept": "application/vnd.github+json"}
    r = requests.get(GECKODRIVER_API, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    version = data["tag_name"]
    win_zip = next(
        (a for a in data["assets"] if a["name"].endswith("win64.zip")),
        None
    )
    if not win_zip:
        raise RuntimeError("win64 geckodriver ZIP not found in latest release")
    print(f"Found geckodriver {version}")
    return version, win_zip["browser_download_url"], win_zip["name"]


def ensure_geckodriver():
    version, url, filename = get_geckodriver_url()

    version_file = os.path.join(GECKODRIVER_DIR, "version.txt")
    exe_path     = os.path.join(GECKODRIVER_DIR, "geckodriver.exe")

    if os.path.exists(version_file) and os.path.exists(exe_path):
        installed = open(version_file).read().strip()
        if installed == version:
            print(f"Geckodriver {version} already up to date — skipping download.")
            return

    print(f"Downloading geckodriver {version}...")
    os.makedirs(GECKODRIVER_DIR, exist_ok=True)

    # Geckodriver is tiny (~5 MB) — skip aria2c, use requests directly
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    zip_path = os.path.join(GECKODRIVER_DIR, "geckodriver.zip")
    with open(zip_path, "wb") as f:
        f.write(r.content)

    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if member.endswith("geckodriver.exe"):
                with z.open(member) as src, open(exe_path, "wb") as dst:
                    dst.write(src.read())
                break

    os.remove(zip_path)
    open(version_file, "w").write(version)
    print(f"Geckodriver {version} ready at {exe_path}")


def kill_firefox():
    """Kill only portable Firefox processes."""
    if len(PORTABLE_DIR) < 10:
        print("PORTABLE_DIR too short — skipping kill for safety.")
        return

    answer = input("\nThis will close all portable Firefox windows. Continue? (y/n): ").strip().lower()
    if answer != "y":
        print("Skipping Firefox kill — locked files may cause update to fail.")
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
        print(f"Killed {len(killed)} portable Firefox process(es) from {PORTABLE_DIR}")
        time.sleep(2)
    else:
        print("No portable Firefox processes found running.")

def extract(zip_path):
    r"""Firefox ZIP extracts to firefox\ one level up — UserData is outside so safe."""
    parent = os.path.dirname(PORTABLE_DIR)   # D:\Programs
    print(f"Extracting to {parent}...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(parent)
    print("Extraction complete.")

def write_user_js():
    user_js_path = os.path.join(USERDATA_DIR, "user.js")

    if os.path.exists(user_js_path):
        print("user.js already exists — skipping.")
        return

    content = r"""// Tampermonkey - pre-grant permissions
user_pref("extensions.webextensions.restrictedDomains", "");
user_pref("extensions.autoDisableScopes", 0);
user_pref("extensions.enabledScopes", 15);
user_pref("privacy.file_unique_origin", false);
user_pref("dom.events.asyncClipboard.clipboardItem", true);
user_pref("dom.events.asyncClipboard.read", true);
user_pref("extensions.permissions.notification.timeout", 0);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("breakpad.reportURL", "");
user_pref("browser.tabs.crashReporting.sendReport", false);
user_pref("browser.cache.disk.parent_directory", "D:\\Programs\\firefox-userdata\\cache");
"""
    Path(USERDATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(user_js_path).write_text(content)
    print(f"user.js written to {USERDATA_DIR}")

def create_start_menu_shortcut():
    ps_script = r"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Firefox Nightly Portable.lnk")
$Shortcut.TargetPath = "D:\Programs\firefox\firefox.exe"
$Shortcut.Arguments = "--profile `"D:\Programs\firefox-userdata`""
$Shortcut.WorkingDirectory = "D:\Programs\firefox"
$Shortcut.IconLocation = "D:\Programs\firefox\firefox.exe,0"
$Shortcut.Description = "Firefox Nightly Portable"
$Shortcut.Save()
"""
    subprocess.run(["powershell", "-Command", ps_script], check=True)
    print("Start Menu shortcut recreated.")
    
def main():
    print("=== Firefox Nightly Portable Updater ===\n")

    aria2c = get_aria2c()
    if aria2c:
        print(f"aria2c found: {aria2c}")
    else:
        print("aria2c not found — will use requests for Firefox download.")

    print("\n--- Geckodriver Check ---")
    try:
        ensure_geckodriver()
    except Exception as e:
        print(f"Warning: Could not update geckodriver: {e}")

    print("\n--- Firefox Nightly Check ---")
    current_version  = get_current_version()
    current_build_id = get_current_build_id()
    print(f"Current version  : {current_version  or 'unknown'}")
    print(f"Current build ID : {current_build_id or 'unknown'}")

    try:
        latest_version, latest_build_id, url, filename = get_latest_nightly()
    except Exception as e:
        print(f"Could not determine latest version: {e}")
        sys.exit(1)

    print(f"Latest version   : {latest_version}")
    print(f"Latest build ID  : {latest_build_id}")

    if current_build_id and current_build_id == latest_build_id:
        print("Firefox Nightly already up to date (build ID matches).")
    else:
        print(f"\nNew Firefox build available: {latest_version} (build {latest_build_id})")
        kill_firefox()
        warp_connect()                          # ← WARP on, just before download
        try:
            zip_path = download_file(url, filename)
            extract(zip_path)
            save_current_version(latest_version)
            save_build_id(latest_build_id)
            os.makedirs(USERDATA_DIR, exist_ok=True)
            print(f"UserData folder ensured: {USERDATA_DIR}")
            write_user_js()
            create_start_menu_shortcut()
            print(f"\nFirefox Nightly updated to {latest_version} (build {latest_build_id})")
        finally:
            warp_disconnect()                   # ← WARP off, always runs
            if os.path.exists(DOWNLOAD_DIR):
                shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
                print("Cleaned up temp download folder.")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
