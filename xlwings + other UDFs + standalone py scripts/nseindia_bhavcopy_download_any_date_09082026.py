from curl_cffi import requests as cffi_requests
import os
import zipfile
from datetime import datetime

# ── CONFIG ─────────────────────────────────────────────────────────────────
OUTPUT_DIR = r"D:\bhavcopy_data"
# ───────────────────────────────────────────────────────────────────────────


def download_nse_bhavcopy(date_str: str, output_dir: str = OUTPUT_DIR):
    """
    Download NSE CM Bhavcopy ZIP using curl-cffi Chrome impersonation.
    No Selenium, no browser needed — bypasses Akamai cleanly.
    Args:
        date_str: Date in DD-MM-YYYY format e.g. '07-08-2026'
    """
    date_obj       = datetime.strptime(date_str, "%d-%m-%Y")
    date_formatted = date_obj.strftime("%Y%m%d")

    archive_url = (
        f"https://nsearchives.nseindia.com/content/cm/"
        f"BhavCopy_NSE_CM_0_0_0_{date_formatted}_F_0000.csv.zip"
    )

    print(f"Downloading bhavcopy for {date_str}...")
    print(f"URL: {archive_url}")

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Hit NSE homepage first to get session cookies — same as warming up
    session = cffi_requests.Session(impersonate="chrome")
    print("Warming up session on NSE homepage...")
    session.get("https://www.nseindia.com", timeout=30)

    # Step 2: Hit market data page to build Akamai session tokens
    print("Building session cookies...")
    session.get(
        "https://www.nseindia.com/market-data/live-equity-market",
        timeout=30
    )

    # Step 3: Download the archive directly
    print("Fetching bhavcopy archive...")
    headers = {
        "Referer": "https://www.nseindia.com/",
        "Accept": "application/zip, application/octet-stream, */*",
    }
    response = session.get(archive_url, headers=headers, timeout=60)

    if response.status_code == 404:
        print(f"404 — No bhavcopy for {date_str} (holiday or weekend).")
        return None
    elif response.status_code != 200:
        print(f"Failed — HTTP {response.status_code}")
        return None

    # Save ZIP
    filename = f"BhavCopy_NSE_CM_0_0_0_{date_formatted}_F_0000.csv.zip"
    zip_path = os.path.join(output_dir, filename)
    with open(zip_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded: {zip_path}")
    return zip_path


def main():
    import sys
    date_str = sys.argv[1] if len(sys.argv) > 1 else "06-08-2026"

    f = download_nse_bhavcopy(date_str, output_dir=OUTPUT_DIR)

    if f and f.endswith(".zip"):
        print(f"\nExtracting {f}...")
        with zipfile.ZipFile(f) as z:
            z.extractall(os.path.dirname(f))
            print(f"Extracted: {z.namelist()}")
    elif f:
        print(f"Downloaded (not a zip): {f}")
    else:
        print("Download failed — nothing to extract.")


if __name__ == "__main__":
    main()
