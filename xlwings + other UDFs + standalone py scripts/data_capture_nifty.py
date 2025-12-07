from seleniumbase import Driver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import os
import glob
import shutil

if __name__ == '__main__':
    download_folder = "D:\\dev\\downloaded_files"
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    print("Initializing Chrome...")
    
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
    
    driver = Driver(uc=True, headless=False)
    
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": download_folder
        })
    except:
        pass
    
    print(f"Download folder: {download_folder}")
    wait = WebDriverWait(driver, 30)

    try:
        print("Loading NIFTY indices website...")
        driver.get("https://www.niftyindices.com/reports/historical-data")
        time.sleep(5)
        
        nifty_years = list(range(2010, 2025))
        nifty_downloaded_files = []
        
        def wait_for_options(select_id, min_options=2, timeout=10):
            """Wait for dropdown to have options populated"""
            end_time = time.time() + timeout
            while time.time() < end_time:
                try:
                    elem = driver.find_element(By.ID, select_id)
                    select_obj = Select(elem)
                    if len(select_obj.options) >= min_options:
                        return True
                except:
                    pass
                time.sleep(0.3)
            return False
        
        def wait_for_overlay_to_disappear(timeout=15):
            """Wait for any overlay to disappear, or hide it forcefully"""
            try:
                # First, try to find and hide the overlay using JavaScript
                driver.execute_script("""
                    var overlays = document.querySelectorAll('div.overlay1, .overlay');
                    overlays.forEach(function(overlay) {
                        overlay.style.display = 'none';
                        overlay.style.visibility = 'hidden';
                    });
                """)
                time.sleep(0.5)
                
                # Check if overlay still exists and is visible
                end_time = time.time() + timeout
                while time.time() < end_time:
                    try:
                        overlay = driver.find_element(By.CSS_SELECTOR, "div.overlay1")
                        if overlay.is_displayed():
                            # Try to hide it again
                            driver.execute_script("arguments[0].style.display = 'none';", overlay)
                            time.sleep(0.5)
                        else:
                            return True
                    except:
                        # Overlay not found or hidden - good
                        return True
                    time.sleep(0.5)
                
                # If still visible after timeout, force hide it
                print("    ⚠ Overlay persistent, forcing hide...")
                driver.execute_script("""
                    var overlays = document.querySelectorAll('div.overlay1, .overlay, [class*="overlay"]');
                    overlays.forEach(function(overlay) {
                        overlay.remove();
                    });
                """)
                time.sleep(1)
                return True
                
            except Exception as e:
                print(f"    Overlay check error: {e}")
                return True
        
        def set_date_with_jquery(date_input_id, day, month, year):
            """Set date using jQuery datepicker methods"""
            try:
                # Wait for any overlay to disappear first
                wait_for_overlay_to_disappear()
                
                # Show the datepicker using jQuery
                print(f"    Opening datepicker for {date_input_id}...")
                driver.execute_script(f'jQuery("#{date_input_id}").datepicker("show");')
                time.sleep(1.5)
                
                # Wait for datepicker to be visible
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ui-datepicker")))
                time.sleep(0.5)
                
                # Set year first
                print(f"    Setting year: {year}")
                year_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-datepicker-year")))
                Select(year_select).select_by_value(str(year))
                time.sleep(0.5)
                
                # Set month (month value is 0-11 for datepicker)
                print(f"    Setting month: {month}")
                month_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-datepicker-month")))
                Select(month_select).select_by_value(str(month))
                time.sleep(0.5)
                
                # Click day
                print(f"    Setting day: {day}")
                day_xpath = f"//a[contains(@class, 'ui-state-default') and text()='{day}' and not(contains(@class, 'ui-state-disabled'))]"
                day_link = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))
                day_link.click()
                time.sleep(1)
                
                return True
            except Exception as e:
                print(f"    ✗ Error setting date: {e}")
                return False
        
        def download_nifty_year(year, is_first=False):
            """Download NIFTY 50 data for a specific year"""
            # Financial year: April 1 (year) to March 31 (year+1)
            from_date_parts = {'day': 1, 'month': 3, 'year': year}  # April 1 (month 3 = April, 0-indexed)
            to_date_parts = {'day': 31, 'month': 2, 'year': year+1}  # March 31 next year (month 2 = March, 0-indexed)
            
            print(f"\nDownloading NIFTY 50: {year}-{year+1} (Apr 1 {year} to Mar 31 {year+1})")
            
            try:
                if is_first:
                    # Step 1: Select Index Type = "Equity"
                    print("  Step 1: Selecting Index Type = Equity...")
                    wait.until(EC.presence_of_element_located((By.ID, "ddlHistoricaltypee")))
                    time.sleep(2)
                    
                    index_type = Select(driver.find_element(By.ID, "ddlHistoricaltypee"))
                    index_type.select_by_visible_text("Equity")
                    time.sleep(2)
                    
                    # Wait for sub-index dropdown to populate
                    print("  Waiting for Sub-Index dropdown...")
                    if not wait_for_options("ddlHistoricaltypeeSubindex", min_options=2, timeout=10):
                        print("  ⚠ Sub-Index dropdown didn't populate!")
                        return False
                    time.sleep(1)
                    
                    # Step 2: Select Sub-Index = "Broad Market Indices"
                    print("  Step 2: Selecting Sub-Index = Broad Market Indices...")
                    sub_index = Select(driver.find_element(By.ID, "ddlHistoricaltypeeSubindex"))
                    
                    # Print available options for debugging
                    print(f"  Available Sub-Index options: {[opt.text for opt in sub_index.options]}")
                    
                    sub_index.select_by_visible_text("Broad Market Indices")
                    time.sleep(2)
                    
                    # Wait for index dropdown to populate
                    print("  Waiting for Index dropdown...")
                    if not wait_for_options("ddlHistoricaltypeeindex", min_options=2, timeout=10):
                        print("  ⚠ Index dropdown didn't populate!")
                        return False
                    time.sleep(1)
                    
                    # Step 3: Select Index = "NIFTY 50"
                    print("  Step 3: Selecting Index = NIFTY 50...")
                    index_select = Select(driver.find_element(By.ID, "ddlHistoricaltypeeindex"))
                    
                    # Print available options for debugging
                    print(f"  Available Index options: {[opt.text for opt in index_select.options]}")
                    
                    index_select.select_by_visible_text("NIFTY 50")
                    time.sleep(2)
                    
                    print("  ✓ All dropdowns selected successfully!")
                
                # Clean old files
                old_nifty = glob.glob(os.path.join(download_folder, "*NIFTY*.csv"))
                for f in old_nifty:
                    if 'nifty_' not in os.path.basename(f).lower():
                        try:
                            os.remove(f)
                        except:
                            pass
                
                existing_files = set(glob.glob(os.path.join(download_folder, "*.csv")))
                
                # Set FROM date using jQuery
                print(f"  Setting FROM date: Apr 1, {from_date_parts['year']}")
                if not set_date_with_jquery("datepickerFrom", 
                                           from_date_parts['day'], 
                                           from_date_parts['month'], 
                                           from_date_parts['year']):
                    return False
                
                # Set TO date using jQuery
                print(f"  Setting TO date: Mar 31, {to_date_parts['year']}")
                if not set_date_with_jquery("datepickerTo", 
                                           to_date_parts['day'], 
                                           to_date_parts['month'], 
                                           to_date_parts['year']):
                    return False
                
                # Click Submit button
                print("  Clicking Submit...")
                submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "submit_button")))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                time.sleep(0.5)
                submit_btn.click()
                
                # Wait for table to appear with data
                print("    Waiting for data table to load...")
                time.sleep(2)
                
                try:
                    # Wait for the history table to be displayed
                    table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.historyData-show")))
                    
                    # Check if table is actually visible
                    if not table.is_displayed():
                        print("    ⚠ Table exists but not visible, waiting...")
                        time.sleep(3)
                    
                    # Wait for table body to have data rows
                    print("    Checking for data rows in table...")
                    tbody = wait.until(EC.presence_of_element_located((By.ID, "myTable")))
                    
                    # Wait for at least one row to appear
                    max_wait = 15
                    for i in range(max_wait):
                        rows = tbody.find_elements(By.TAG_NAME, "tr")
                        if len(rows) > 0:
                            print(f"    ✓ Table loaded with {len(rows)} rows")
                            break
                        time.sleep(1)
                    else:
                        print("    ⚠ Table body still empty after waiting!")
                        # Try clearing overlay
                        wait_for_overlay_to_disappear()
                        rows = tbody.find_elements(By.TAG_NAME, "tr")
                        if len(rows) == 0:
                            print("  ✗ No data loaded in table!")
                            return False
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  ⚠ Error waiting for table: {e}")
                    # Try to clear overlay and check again
                    wait_for_overlay_to_disappear()
                    time.sleep(2)
                    
                    try:
                        table = driver.find_element(By.CSS_SELECTOR, "table.historyData-show")
                        tbody = driver.find_element(By.ID, "myTable")
                        rows = tbody.find_elements(By.TAG_NAME, "tr")
                        if len(rows) == 0:
                            print("  ✗ Table still has no data!")
                            return False
                        print(f"    ✓ Found table with {len(rows)} rows after retry")
                    except:
                        print("  ✗ Could not find data table!")
                        return False
                
                # Wait for data to load and CSV link to appear
                print("    Checking for export button...")
                try:
                    # Wait up to 10 seconds for the export button
                    export_btn = wait.until(EC.presence_of_element_located((By.ID, "exporthistorical")))
                    
                    # Ensure it's visible and clickable
                    if export_btn.is_displayed():
                        print("    ✓ Export button found and visible")
                    else:
                        print("    ⚠ Export button found but not visible")
                        wait_for_overlay_to_disappear()
                    
                    time.sleep(1)
                except Exception as e:
                    print(f"  ⚠ Export button not found! Error: {e}")
                    wait_for_overlay_to_disappear()
                    try:
                        driver.find_element(By.ID, "exporthistorical")
                        print("    ✓ Export button found after clearing overlay")
                    except:
                        print("  ✗ Export button still not found!")
                        return False
                
                # Click CSV download link using JavaScript to avoid interception
                print("  Downloading CSV...")
                
                # Wait for overlay to disappear before clicking
                wait_for_overlay_to_disappear()
                
                csv_link = driver.find_element(By.ID, "exporthistorical")
                
                # Try JavaScript click first
                try:
                    driver.execute_script("arguments[0].click();", csv_link)
                    print("    Used JavaScript click")
                except:
                    # Fallback to regular click
                    try:
                        csv_link.click()
                        print("    Used regular click")
                    except:
                        print("  ⚠ Could not click download link!")
                        return False
                
                # Wait for download to complete - increased time
                print("    Waiting for download to complete...")
                time.sleep(8)
                
                # Check for new files
                current_files = set(glob.glob(os.path.join(download_folder, "*.csv")))
                new_files = current_files - existing_files
                
                if not new_files:
                    print("    Waiting a bit longer for download...")
                    time.sleep(5)
                    current_files = set(glob.glob(os.path.join(download_folder, "*.csv")))
                    new_files = current_files - existing_files
                
                if new_files:
                    new_file = list(new_files)[0]
                    year_file = os.path.join(download_folder, f"nifty_{year}.csv")
                    
                    if os.path.exists(year_file):
                        os.remove(year_file)
                    
                    shutil.move(new_file, year_file)
                    print(f"  ✓ Downloaded: nifty_{year}.csv")
                    return True
                else:
                    print(f"  ✗ Failed to download: nifty_{year}.csv")
                    return False
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Initial setup - select all dropdowns once
        print("\n" + "="*50)
        print("INITIAL SETUP")
        print("="*50)
        
        # Step 1: Select Index Type = "Equity"
        print("Step 1: Selecting Index Type = Equity...")
        wait.until(EC.presence_of_element_located((By.ID, "ddlHistoricaltypee")))
        time.sleep(2)
        
        index_type = Select(driver.find_element(By.ID, "ddlHistoricaltypee"))
        index_type.select_by_visible_text("Equity")
        time.sleep(2)
        
        # Wait for sub-index dropdown to populate
        print("Waiting for Sub-Index dropdown...")
        if not wait_for_options("ddlHistoricaltypeeSubindex", min_options=2, timeout=10):
            print("⚠ Sub-Index dropdown didn't populate!")
        time.sleep(1)
        
        # Step 2: Select Sub-Index = "Broad Market Indices"
        print("Step 2: Selecting Sub-Index = Broad Market Indices...")
        sub_index = Select(driver.find_element(By.ID, "ddlHistoricaltypeeSubindex"))
        sub_index.select_by_visible_text("Broad Market Indices")
        time.sleep(2)
        
        # Wait for index dropdown to populate
        print("Waiting for Index dropdown...")
        if not wait_for_options("ddlHistoricaltypeeindex", min_options=2, timeout=10):
            print("⚠ Index dropdown didn't populate!")
        time.sleep(1)
        
        # Step 3: Select Index = "NIFTY 50"
        print("Step 3: Selecting Index = NIFTY 50...")
        index_select = Select(driver.find_element(By.ID, "ddlHistoricaltypeeindex"))
        index_select.select_by_visible_text("NIFTY 50")
        time.sleep(2)
        
        print("✓ Setup complete! Starting downloads...")
        print("="*50)
        
        # Download all years WITHOUT reloading page
        for idx, year in enumerate(nifty_years):
            success = download_nifty_year(year, is_first=False)  # Never do first-time setup again
            if success:
                nifty_downloaded_files.append(os.path.join(download_folder, f"nifty_{year}.csv"))
            
            # Extra wait between years to ensure page is ready
            if idx < len(nifty_years) - 1:
                print("  Pausing before next year...")
                time.sleep(3)
        
        # Retry missing years
        expected_nifty = {year: os.path.join(download_folder, f"nifty_{year}.csv") for year in nifty_years}
        missing_nifty = [year for year, filepath in expected_nifty.items() if not os.path.exists(filepath)]
        
        if missing_nifty:
            print(f"\n{'='*50}")
            print(f"Retrying {len(missing_nifty)} missing year(s): {missing_nifty}")
            print(f"{'='*50}")
            
            for year in missing_nifty:
                # For retries, we might need to reload and setup again
                driver.get("https://www.niftyindices.com/reports/historical-data")
                time.sleep(4)
                success = download_nifty_year(year, is_first=True)
                if success:
                    nifty_downloaded_files.append(os.path.join(download_folder, f"nifty_{year}.csv"))
        
        # Combine all files
        if nifty_downloaded_files:
            nifty_data = []
            for nf in nifty_downloaded_files:
                if os.path.exists(nf):
                    try:
                        df = pd.read_csv(nf)
                        nifty_data.append(df)
                        print(f"  Loaded: {os.path.basename(nf)} ({len(df)} rows)")
                    except Exception as e:
                        print(f"  ✗ Error reading {os.path.basename(nf)}: {e}")
            
            if nifty_data:
                combined_nifty = pd.concat(nifty_data, ignore_index=True)
                
                # Sort by date
                date_col = combined_nifty.columns[0]
                try:
                    combined_nifty[date_col] = pd.to_datetime(combined_nifty[date_col], format='%d-%b-%Y', errors='coerce')
                    combined_nifty = combined_nifty.sort_values(by=date_col)
                except:
                    pass
                
                nifty_output = os.path.join(download_folder, 'nifty_15years.csv')
                combined_nifty.to_csv(nifty_output, index=False)
                print(f"\n{'='*50}")
                print(f"✓ NIFTY combined: {len(combined_nifty)} rows -> nifty_15years.csv")
                print(f"{'='*50}")
        else:
            print("\n✗ No files were downloaded successfully")
        
    except Exception as e:
        print(f"\nFatal Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()
