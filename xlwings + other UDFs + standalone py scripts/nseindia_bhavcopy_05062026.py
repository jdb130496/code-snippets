from seleniumbase import Driver
import os
import time
import glob
from datetime import datetime


def download_nse_bhavcopy_selenium(date_str: str, output_dir: str = r"D:\bhavcopy_data"):
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    date_formatted = date_obj.strftime("%Y%m%d")

    url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_formatted}_F_0000.csv.zip"

    print(f"Downloading bhavcopy for {date_str}...")
    print(f"URL: {url}")

    os.makedirs(output_dir, exist_ok=True)

    driver = Driver(
        browser="chrome",
        binary_location=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        undetectable=True,
        headless=False,
    )

    # Set download directory via CDP — works reliably even in UC mode
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": output_dir,
    })

    try:
        print("Warming up on NSE homepage...")
        driver.get("https://www.nseindia.com")
        time.sleep(5)

        print("Triggering download...")
        driver.get(url)

        deadline = time.time() + 60
        downloaded = None
        while time.time() < deadline:
            files = [
                f for f in glob.glob(os.path.join(output_dir, "*"))
                if not f.endswith(".crdownload") and not f.endswith(".tmp")
            ]
            if files:
                downloaded = max(files, key=os.path.getmtime)
                break
            time.sleep(2)

        if downloaded:
            print(f"Downloaded: {downloaded}")
        else:
            print("Timed out. File may not exist (holiday?) or Akamai still blocking.")

    finally:
        driver.quit()

    return downloaded


if __name__ == "__main__":
    f = download_nse_bhavcopy_selenium("05-06-2026", output_dir=r"D:\bhavcopy_data")
    if f and f.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(f) as z:
            z.extractall(os.path.dirname(f))
            print(f"Extracted: {z.namelist()}")
