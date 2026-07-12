from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
import time
import glob
import shutil
import tempfile
from datetime import datetime


def find_browser_binary():
    """Locate the REAL Chrome/Chromium/Brave ELF binary on Linux.

    Deliberately bypasses shell wrapper scripts (e.g. Debian/Fedora's
    brave-browser-nightly wrapper), since wrappers that redirect stdout
    via process substitution and run the real binary as a non-exec'd
    child (swallowing its exit code) can break chromedriver's automation
    handshake, causing it to hang waiting for a DevTools response that
    never arrives.
    """
    direct_paths = [
        "/opt/brave.com/brave-nightly/brave",
        "/opt/brave.com/brave/brave",
        "/opt/brave.com/brave-beta/brave",
        "/opt/google/chrome/chrome",
        "/usr/lib64/chromium-browser/chromium-browser",
        "/usr/lib/chromium-browser/chromium-browser",
    ]
    for path in direct_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    candidates = [
        "brave-browser",
        "brave-browser-stable",
        "brave",
        "google-chrome",
        "google-chrome-stable",
        "chromium-browser",
        "chromium",
        "chrome",
    ]
    for name in candidates:
        path = shutil.which(name)
        if path:
            return path
    return None


def find_chromedriver_binary():
    """Locate the chromedriver/uc_driver binary already downloaded by seleniumbase."""
    search_dirs = [
        os.path.expanduser(
            "~/.local/lib/python3.15/site-packages/seleniumbase/drivers/brave_drivers"
        ),
        os.path.expanduser(
            "~/.local/lib/python3.15/site-packages/seleniumbase/drivers"
        ),
    ]
    for d in search_dirs:
        for name in ("uc_driver", "chromedriver"):
            candidate = os.path.join(d, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    # Fall back to PATH
    return shutil.which("chromedriver")


def download_nse_bhavcopy_selenium(date_str: str, output_dir: str = os.path.expanduser("~/bhavcopy_data")):
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    date_formatted = date_obj.strftime("%Y%m%d")

    url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_formatted}_F_0000.csv.zip"

    print(f"Downloading bhavcopy for {date_str}...")
    print(f"URL: {url}")

    os.makedirs(output_dir, exist_ok=True)

    for stray in glob.glob(os.path.join(output_dir, "*.crdownload")):
        try:
            os.remove(stray)
            print(f"Removed stray leftover file: {stray}")
        except OSError as e:
            print(f"Could not remove {stray}: {e}")

    binary_location = find_browser_binary()
    if not binary_location:
        raise RuntimeError("Could not find a Chrome/Chromium/Brave binary.")
    print(f"Using browser binary: {binary_location}")

    chromedriver_path = find_chromedriver_binary()
    if not chromedriver_path:
        raise RuntimeError(
            "Could not find chromedriver/uc_driver. Run once with seleniumbase's "
            "Driver() first so it downloads one, or install chromedriver manually."
        )
    print(f"Using chromedriver: {chromedriver_path}")

    user_data_dir = tempfile.mkdtemp(prefix="nse_brave_profile_")

    options = webdriver.ChromeOptions()
    options.binary_location = binary_location
    options.add_argument("--no-sandbox")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    # --test-type=webdriver crashes this Brave Nightly build with SIGTRAP
    # (Trace/breakpoint trap) on Fedora Rawhide; exclude it explicitly.
    options.add_experimental_option("excludeSwitches", ["enable-automation", "test-type"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {
        "download.default_directory": output_dir,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
    })

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    # Set download directory via CDP as well, for extra reliability
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": output_dir,
    })

    downloaded = None
    try:
        print("Warming up on NSE homepage...")
        driver.get("https://www.nseindia.com")
        time.sleep(5)

        existing_files = set(glob.glob(os.path.join(output_dir, "*")))

        print("Triggering download...")
        driver.get(url)

        deadline = time.time() + 60
        while time.time() < deadline:
            current_files = set(glob.glob(os.path.join(output_dir, "*")))
            new_files = [
                f for f in (current_files - existing_files)
                if not f.endswith(".crdownload") and not f.endswith(".tmp")
            ]
            new_files = [f for f in new_files if date_formatted in os.path.basename(f)]
            if new_files:
                downloaded = max(new_files, key=os.path.getmtime)
                break
            time.sleep(2)

        if downloaded:
            print(f"Downloaded: {downloaded}")
        else:
            print("Timed out. File may not exist (holiday?) or Akamai still blocking.")

    finally:
        driver.quit()
        shutil.rmtree(user_data_dir, ignore_errors=True)
        for stray in glob.glob(os.path.join(output_dir, "*.crdownload")):
            try:
                os.remove(stray)
                print(f"Removed stray leftover file: {stray}")
            except OSError as e:
                print(f"Could not remove {stray}: {e}")

    return downloaded


if __name__ == "__main__":
    f = download_nse_bhavcopy_selenium("03-07-2026", output_dir=os.path.expanduser("~/bhavcopy_data"))
    if f and f.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(f) as z:
            z.extractall(os.path.dirname(f))
            print(f"Extracted: {z.namelist()}")
