from seleniumbase import Driver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import numpy as np
import os
import glob
import shutil

def wait_for_download_complete(download_folder, default_download, existing_files, timeout=15):
    """
    Simple wait for download - just wait 5 seconds and check for NEW csv files
    existing_files: set of files that existed BEFORE clicking download
    """
    print(f"    Waiting for download...")
    
    # Wait 5 seconds for download to complete
    time.sleep(5)
    
    # Check for any NEW CSV files (files that didn't exist before)
    current_files = set(glob.glob(os.path.join(download_folder, "*.csv")))
    new_files = current_files - existing_files
    
    if new_files:
        new_file = list(new_files)[0]
        if os.path.getsize(new_file) > 100:
            print(f"    ✓ Downloaded: {os.path.basename(new_file)}")
            return new_file
    
    # Also check default Downloads folder
    default_files = set(glob.glob(os.path.join(default_download, "*RSYSTEMS*.csv")))
    if default_files:
        newest = max(default_files, key=os.path.getctime)
        if os.path.getsize(newest) > 100:
            print(f"    ✓ File found in default Downloads, moving...")
            target_file = os.path.join(download_folder, os.path.basename(newest))
            shutil.move(newest, target_file)
            return target_file
    
    # If not found after 5 seconds, wait a bit more and check again
    print(f"    File not found yet, waiting 5 more seconds...")
    time.sleep(5)
    
    current_files = set(glob.glob(os.path.join(download_folder, "*.csv")))
    new_files = current_files - existing_files
    
    if new_files:
        new_file = list(new_files)[0]
        if os.path.getsize(new_file) > 100:
            print(f"    ✓ Downloaded: {os.path.basename(new_file)}")
            return new_file
    
    # Final debug output
    print(f"    ✗ File not found after {timeout}s")
    print(f"    Files in target folder: {[os.path.basename(f) for f in glob.glob(os.path.join(download_folder, '*.csv'))[:5]]}")
    return None


def download_year(driver, wait, download_folder, default_download, year, is_first_iteration=False):
    """
    Download data for a specific year
    Returns True if successful, False otherwise
    """
    from_date = f"01-04-{year}"
    to_date = f"31-03-{year+1}"
    
    print(f"\n{'='*60}")
    print(f"Downloading year {year}: {from_date} to {to_date}")
    print(f"{'='*60}")
    
    try:
        # Clean up old downloads (but not our renamed files)
        old_downloads = glob.glob(os.path.join(download_folder, "*-TO-*RSYSTEMS*.csv"))
        for f in old_downloads:
            try:
                os.remove(f)
                print(f"  → Cleaned up old download: {os.path.basename(f)}")
            except:
                pass
        
        # Track existing files BEFORE clicking download
        existing_files = set(glob.glob(os.path.join(download_folder, "*.csv")))
        
        if is_first_iteration:
            print("First iteration - setting up symbol and custom date range...")
            time.sleep(2)
            
            print("  → Finding symbol input...")
            symbol_input = wait.until(EC.presence_of_element_located((By.ID, "hsa-symbol")))
            print("  ✓ Symbol input found")
            
            time.sleep(2)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", symbol_input)
            time.sleep(2)
            driver.execute_script("arguments[0].focus();", symbol_input)
            time.sleep(1)
            driver.execute_script("arguments[0].value = '';", symbol_input)
            time.sleep(1)
            
            symbol = 'RSYSTEMS'
            print(f"  → Typing symbol: {symbol}")
            for char in symbol:
                driver.execute_script(f"arguments[0].value += '{char}';", symbol_input)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", symbol_input)
                time.sleep(0.7)
            
            time.sleep(3)
            print("  → Selecting from dropdown...")
            symbol_input.send_keys(Keys.ARROW_DOWN)
            time.sleep(1)
            symbol_input.send_keys(Keys.ENTER)
            time.sleep(2)
            print("  ✓ Symbol selected")
            
            print("  → Clicking Custom button...")
            custom_button = wait.until(EC.element_to_be_clickable((By.ID, "custom")))
            time.sleep(1)
            driver.execute_script("arguments[0].click();", custom_button)
            time.sleep(1)
            print("  ✓ Custom button clicked")
        
        print("  → Setting FROM date...")
        from_date_input = wait.until(EC.presence_of_element_located((By.ID, "pbc-startDate")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", from_date_input)
        time.sleep(1)
        driver.execute_script("arguments[0].focus();", from_date_input)
        time.sleep(1)
        driver.execute_script("arguments[0].removeAttribute('readonly');", from_date_input)
        time.sleep(1)
        driver.execute_script("arguments[0].value = '';", from_date_input)
        time.sleep(1)
        driver.execute_script(f"arguments[0].value = '{from_date}';", from_date_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", from_date_input)
        time.sleep(1)
        print(f"  ✓ FROM date set to: {from_date}")
        
        print("  → Setting TO date...")
        to_date_input = driver.find_element(By.ID, "pbc-endDate")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", to_date_input)
        time.sleep(1)
        driver.execute_script("arguments[0].focus();", to_date_input)
        time.sleep(1)
        driver.execute_script("arguments[0].removeAttribute('readonly');", to_date_input)
        time.sleep(1)
        driver.execute_script("arguments[0].value = '';", to_date_input)
        time.sleep(1)
        driver.execute_script(f"arguments[0].value = '{to_date}';", to_date_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", to_date_input)
        time.sleep(1)
        print(f"  ✓ TO date set to: {to_date}")
        
        driver.execute_script("document.activeElement.blur();")
        time.sleep(1)
        
        print("  → Looking for GO button...")
        go_button = None
        selectors = [
            "button.filterbtn",
            "button[type='button'].filterbtn",
            "//button[contains(text(), 'GO')]",
            "//button[@class='filterbtn']"
        ]
        
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    go_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    go_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                print(f"  ✓ GO button found with selector: {selector}")
                break
            except:
                continue
        
        if not go_button:
            print("  ✗ GO button not found with any selector!")
            raise Exception("GO button not found")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", go_button)
        time.sleep(1)
        
        print("  → Clicking GO button...")
        try:
            driver.uc_click("button.filterbtn", reconnect_time=2)
        except:
            driver.execute_script("arguments[0].click();", go_button)
        
        time.sleep(3)
        print("  ✓ GO button clicked")
        
        print("  → Looking for Download link...")
        download_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[download='equity-derivatives.csv']")))
        print("  ✓ Download link found")
        
        download_url = download_link.get_attribute('href')
        print(f"    Download URL: {download_url[:80]}...")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_link)
        time.sleep(1)
        
        print("  → Clicking Download link...")
        try:
            driver.uc_click("a[download='equity-derivatives.csv']", reconnect_time=2)
            print("    Used UC click")
        except:
            try:
                driver.execute_script("arguments[0].click();", download_link)
                print("    Used JavaScript click")
            except:
                print("    Using direct download via URL...")
                driver.execute_script(f"window.location.href = '{download_url}';")
        
        time.sleep(2)
        print("  ✓ Download initiated")
        
        # Wait for download to complete
        downloaded_file = wait_for_download_complete(download_folder, default_download, existing_files, timeout=15)
        
        if downloaded_file and os.path.exists(downloaded_file):
            # Rename to year-specific file
            year_file = os.path.join(download_folder, f"rsystems_{year}.csv")
            shutil.move(downloaded_file, year_file)
            print(f"  ✓✓ Downloaded and saved: rsystems_{year}.csv")
            return True
        else:
            print(f"  ✗ Download failed for {year}")
            print(f"    Checked folders:")
            print(f"      - {download_folder}")
            print(f"      - {default_download}")
            driver.save_screenshot(os.path.join(download_folder, f"error_download_{year}.png"))
            return False
        
    except Exception as year_error:
        print(f"\n✗✗ Error downloading {year}: {year_error}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot(os.path.join(download_folder, f"error_year_{year}.png"))
        return False


if __name__ == '__main__':
    download_folder = "D:\\dev\\downloaded_files"
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    print("Initializing Chrome with SeleniumBase UC Mode...")
    
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = Driver(uc=True, headless=False, chromium_arg=" ".join([
        f"--prefs={prefs}",
        f"--download-directory={download_folder}"
    ]))
    
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": download_folder
        })
    except:
        print("  Warning: Could not set CDP download behavior")
    
    print("Chrome started successfully!")
    print(f"Download folder: {download_folder}")
    
    wait = WebDriverWait(driver, 20)
    actions = ActionChains(driver)
    default_download = os.path.join(os.path.expanduser("~"), "Downloads")

    try:
        print("Loading NSE India website...")
        driver.uc_open_with_reconnect("https://www.nseindia.com/report-detail/eq_security", reconnect_time=5)
        time.sleep(3)
        print("Page loaded successfully!")
        
        years = list(range(2010, 2025))
        downloaded_files = []
        
        # First pass - download all years
        for idx, year in enumerate(years):
            success = download_year(driver, wait, download_folder, default_download, year, is_first_iteration=(idx == 0))
            if success:
                year_file = os.path.join(download_folder, f"rsystems_{year}.csv")
                downloaded_files.append(year_file)
            time.sleep(2)
        
        # Check for missing years
        expected_files = {year: os.path.join(download_folder, f"rsystems_{year}.csv") for year in years}
        missing_years = [year for year, filepath in expected_files.items() if not os.path.exists(filepath)]
        
        if missing_years:
            print(f"\n{'='*60}")
            print(f"RETRY: {len(missing_years)} missing year(s) detected: {missing_years}")
            print(f"{'='*60}")
            print("Retrying missing years...")
            
            for year in missing_years:
                print(f"\nRetrying year {year}...")
                time.sleep(3)  # Extra wait before retry
                success = download_year(driver, wait, download_folder, default_download, year, is_first_iteration=False)
                if success:
                    year_file = os.path.join(download_folder, f"rsystems_{year}.csv")
                    downloaded_files.append(year_file)
                time.sleep(2)
        
        # Final check
        final_missing = [year for year, filepath in expected_files.items() if not os.path.exists(filepath)]
        if final_missing:
            print(f"\n⚠ WARNING: Still missing {len(final_missing)} year(s) after retry: {final_missing}")
        
        print("\n" + "="*60)
        print("Processing downloaded files...")
        print("="*60)
        
        all_data = []
        for year_file in downloaded_files:
            if os.path.exists(year_file):
                df = pd.read_csv(year_file)
                all_data.append(df)
                print(f"  ✓ Processed: {os.path.basename(year_file)}")
        
        if len(all_data) > 0:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values(by=combined_df.columns[0])
            output_file = os.path.join(download_folder, 'rsystems_15years.csv')
            combined_df.to_csv(output_file, index=False)
            print(f"\n✓✓ Combined CSV saved: {len(combined_df)} rows")
            print(f"    Total files downloaded: {len(downloaded_files)} out of {len(years)}")
            print(f"    Saved to: {output_file}")
        else:
            print("\n✗ No data collected")
            raise Exception("No data files were downloaded")
        
        # Check if nifty_15years.csv exists before trying to read it
        nifty_file = os.path.join(download_folder, 'nifty_15years.csv')
        if not os.path.exists(nifty_file):
            print(f"\n⚠ WARNING: {nifty_file} not found!")
            print("Please ensure nifty_15years.csv is in the download folder before running analysis.")
            print("Skipping analysis section...")
            print(f"\n✓ RSYSTEMS data successfully saved to: {output_file}")
        else:
            # Analysis section - only runs if nifty file exists
            print("\n" + "="*60)
            print("Running Analysis...")
            print("="*60)
            
            stock_df = pd.read_csv(os.path.join(download_folder, 'rsystems_15years.csv'))
            nifty_df = pd.read_csv(nifty_file)
            
            stock_df.columns = stock_df.columns.str.lower().str.strip()
            nifty_df.columns = nifty_df.columns.str.lower().str.strip()
            
            #stock_df['date'] = pd.to_datetime(stock_df['date'], format='%d-%b-%Y')
            #nifty_df['date'] = pd.to_datetime(nifty_df['date'], format='%d-%b-%Y')
            # Handle potential date format differences
            stock_df['date'] = pd.to_datetime(stock_df['date'], format='mixed', dayfirst=True)
            nifty_df['date'] = pd.to_datetime(nifty_df['date'], format='mixed', dayfirst=True)
            
            #for col in ['open price', 'high price', 'low price', 'close price']:
                #stock_df[col] = stock_df[col].replace(',', '', regex=True).astype(float)
            #for col in ['open price', 'high price', 'low price', 'close price']:
                #nifty_df[col] = nifty_df[col].replace(',', '', regex=True).astype(float)
            # Convert stock price columns
            for col in ['open price', 'high price', 'low price', 'close price']:
                stock_df[col] = stock_df[col].replace(',', '', regex=True).astype(float)

            # Convert nifty price columns (different column names)
            for col in ['open', 'high', 'low', 'close']:
                nifty_df[col] = nifty_df[col].replace(',', '', regex=True).astype(float)

            # Rename nifty columns to match stock format for easier processing
            nifty_df = nifty_df.rename(columns={'open': 'open price','high': 'high price', 'low': 'low price','close': 'close price'})
            stock_df['avg_price'] = (stock_df['open price'] + stock_df['high price'] + stock_df['low price'] + stock_df['close price']) / 4
            nifty_df['avg_price'] = (nifty_df['open price'] + nifty_df['high price'] + nifty_df['low price'] + nifty_df['close price']) / 4
            
            stock_df['returns'] = (stock_df['avg_price'] / stock_df['avg_price'].shift(1)) - 1
            nifty_df['returns'] = (nifty_df['avg_price'] / nifty_df['avg_price'].shift(1)) - 1
            
            stock_df = stock_df.dropna()
            nifty_df = nifty_df.dropna()
            
            blocks = [
                ('2011-04-01', '2016-03-31'),
                ('2012-04-01', '2017-03-31'),
                ('2013-04-01', '2018-03-31'),
                ('2014-04-01', '2019-03-31'),
                ('2015-04-01', '2020-03-31')
            ]
            
            results = []
            total_beats = 0
            cov_values = []
            
            for start, end in blocks:
                stock_block = stock_df[(stock_df['date'] >= start) & (stock_df['date'] <= end)]
                nifty_block = nifty_df[(nifty_df['date'] >= start) & (nifty_df['date'] <= end)]
                
                stock_mean_return = stock_block['returns'].mean() * 252 * 100
                nifty_mean_return = nifty_block['returns'].mean() * 252 * 100
                
                stock_std = stock_block['returns'].std() * np.sqrt(252) * 100
                stock_cov = stock_std / abs(stock_mean_return) if stock_mean_return != 0 else np.inf
                
                beats_nifty = 1 if stock_mean_return > nifty_mean_return else 0
                
                results.append({
                    'stock_return': stock_mean_return,
                    'nifty_return': nifty_mean_return,
                    'stock_volatility': stock_std,
                    'cov': stock_cov,
                    'beats_nifty': beats_nifty
                })
                
                total_beats += beats_nifty
                cov_values.append(stock_cov)
            
            probability = total_beats / len(blocks)
            avg_cov = np.mean([c for c in cov_values if c != np.inf])
            final_score = probability * avg_cov
            
            print(f"\n{'='*60}")
            print("FINAL RESULTS")
            print(f"{'='*60}")
            print(f"Probability: {probability:.2f}")
            print(f"Average COV: {avg_cov:.4f}")
            print(f"Final Score: {final_score:.4f}")
            
            for i, block in enumerate(results):
                print(f"\nBlock {i+1}: Stock={block['stock_return']:.2f}% Nifty={block['nifty_return']:.2f}% Beats={'Yes' if block['beats_nifty'] else 'No'} COV={block['cov']:.4f}")

    except Exception as e:
        print(f"\n✗✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()
