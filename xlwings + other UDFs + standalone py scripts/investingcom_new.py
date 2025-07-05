# Working Investing.com Cloudflare Bypass Solutions
# Based on current GitHub projects and your successful diagnostic script

import pandas as pd
import requests
import cloudscraper
import time
from datetime import datetime
import json

# SOLUTION 1: Enhanced CloudScraper (Your working diagnostic method)
@xw.func
def get_investing_data_enhanced_cloudscraper(investing_id, from_date, to_date):
    """
    Uses your working diagnostic script method with enhanced error handling
    investing_id: 'BO:503205' or similar format found by your diagnostic script
    """
    try:
        from_date_obj = datetime.strptime(from_date, "%d/%m/%Y")
        to_date_obj = datetime.strptime(to_date, "%d/%m/%Y")
        
        # Create enhanced cloudscraper with better headers
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=10  # Add delay to avoid rate limiting
        )
        
        # Add realistic headers
        scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.investing.com/',
            'Origin': 'https://www.investing.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site'
        })
        
        # Use the working URL pattern from your diagnostic script
        timestamp = str(int(time.time()))
        base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        history_url = f"{base_url}/{timestamp}/56/56/23/history"
        
        # Convert to timestamps
        end_time = int(to_date_obj.timestamp())
        start_time = int(from_date_obj.timestamp())
        
        params = {
            'symbol': investing_id,
            'resolution': 'D',  # Daily data
            'from': start_time,
            'to': end_time
        }
        
        response = scraper.get(history_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and data.get('s') == 'ok':
                # Convert TradingView format to Excel-friendly format
                rows = []
                for i in range(len(data['t'])):
                    rows.append([
                        datetime.fromtimestamp(data['t'][i]).strftime('%Y-%m-%d'),  # Date
                        data['o'][i],  # Open
                        data['h'][i],  # High  
                        data['l'][i],  # Low
                        data['c'][i],  # Close
                        data.get('v', [0] * len(data['c']))[i] if data.get('v') else 0  # Volume
                    ])
                
                # Add headers
                headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                rows.insert(0, headers)
                return rows
            else:
                return [["Error: No data returned", f"Status: {data.get('s', 'unknown')}"]]
        else:
            return [["Error: Request failed", f"Status: {response.status_code}"]]
            
    except Exception as e:
        return [[f"Error: {str(e)}"]]

# SOLUTION 2: ScraperAPI Service (Paid but reliable)
@xw.func  
def get_investing_data_scraperapi(investing_id, from_date, to_date, scraperapi_key):
    """
    Use ScraperAPI service to bypass Cloudflare
    Sign up at: https://www.scraperapi.com/ (5000 free calls)
    """
    try:
        from_date_obj = datetime.strptime(from_date, "%d/%m/%Y")
        to_date_obj = datetime.strptime(to_date, "%d/%m/%Y")
        
        # Convert to timestamps
        end_time = int(to_date_obj.timestamp())
        start_time = int(from_date_obj.timestamp())
        
        # Build the Investing.com API URL
        timestamp = str(int(time.time()))
        base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        target_url = f"{base_url}/{timestamp}/56/56/23/history?symbol={investing_id}&resolution=D&from={start_time}&to={end_time}"
        
        # ScraperAPI endpoint
        scraperapi_url = "http://api.scraperapi.com/"
        
        params = {
            'api_key': scraperapi_key,
            'url': target_url,
            'render': 'false',  # Don't need browser rendering for API
            'country_code': 'us'
        }
        
        response = requests.get(scraperapi_url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and data.get('s') == 'ok':
                # Convert to Excel format
                rows = []
                for i in range(len(data['t'])):
                    rows.append([
                        datetime.fromtimestamp(data['t'][i]).strftime('%Y-%m-%d'),
                        data['o'][i],
                        data['h'][i], 
                        data['l'][i],
                        data['c'][i],
                        data.get('v', [0] * len(data['c']))[i] if data.get('v') else 0
                    ])
                
                headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                rows.insert(0, headers)
                return rows
            else:
                return [["Error: No data", f"Status: {data.get('s', 'unknown')}"]]
        else:
            return [["Error: ScraperAPI failed", f"Status: {response.status_code}"]]
            
    except Exception as e:
        return [[f"Error: {str(e)}"]]

# SOLUTION 3: ScrapeOwl Service (Alternative to ScraperAPI)
@xw.func
def get_investing_data_scrapeowl(investing_id, from_date, to_date, scrapeowl_key):
    """
    Use ScrapeOwl service - another Cloudflare bypass service
    Sign up at: https://scrapeowl.com/ 
    """
    try:
        from_date_obj = datetime.strptime(from_date, "%d/%m/%Y")
        to_date_obj = datetime.strptime(to_date, "%d/%m/%Y")
        
        end_time = int(to_date_obj.timestamp())
        start_time = int(from_date_obj.timestamp())
        
        timestamp = str(int(time.time()))
        base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        target_url = f"{base_url}/{timestamp}/56/56/23/history?symbol={investing_id}&resolution=D&from={start_time}&to={end_time}"
        
        scrapeowl_url = "https://api.scrapeowl.com/v1/scrape"
        
        payload = {
            'api_key': scrapeowl_key,
            'url': target_url,
            'elements': [{'select': 'body'}]  # Get full response
        }
        
        response = requests.post(scrapeowl_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            # Parse the scraped content
            if 'data' in result and result['data']:
                # Extract JSON from the response
                content = result['data'][0]['results'][0]['text']
                data = json.loads(content)
                
                if data and data.get('s') == 'ok':
                    rows = []
                    for i in range(len(data['t'])):
                        rows.append([
                            datetime.fromtimestamp(data['t'][i]).strftime('%Y-%m-%d'),
                            data['o'][i],
                            data['h'][i],
                            data['l'][i], 
                            data['c'][i],
                            data.get('v', [0] * len(data['c']))[i] if data.get('v') else 0
                        ])
                    
                    headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    rows.insert(0, headers)
                    return rows
                else:
                    return [["Error: No data", f"Status: {data.get('s', 'unknown')}"]]
        
        return [["Error: ScrapeOwl failed", f"Status: {response.status_code}"]]
            
    except Exception as e:
        return [[f"Error: {str(e)}"]]

# SOLUTION 4: Rotating Proxy with CloudScraper
@xw.func
def get_investing_data_proxy_rotation(investing_id, from_date, to_date):
    """
    Use rotating proxies with CloudScraper
    Note: You'll need to provide your own proxy list
    """
    try:
        from_date_obj = datetime.strptime(from_date, "%d/%m/%Y")
        to_date_obj = datetime.strptime(to_date, "%d/%m/%Y")
        
        # List of proxy servers (you need to get these from proxy providers)
        proxy_list = [
            # Add your proxy servers here
            # Format: {'http': 'http://user:pass@proxy:port', 'https': 'https://user:pass@proxy:port'}
        ]
        
        if not proxy_list:
            return [["Error: No proxies configured. Add proxy servers to proxy_list"]]
        
        for proxy in proxy_list:
            try:
                # Create scraper with proxy
                scraper = cloudscraper.create_scraper()
                scraper.proxies = proxy
                
                timestamp = str(int(time.time()))
                base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
                history_url = f"{base_url}/{timestamp}/56/56/23/history"
                
                end_time = int(to_date_obj.timestamp())
                start_time = int(from_date_obj.timestamp())
                
                params = {
                    'symbol': investing_id,
                    'resolution': 'D',
                    'from': start_time,
                    'to': end_time
                }
                
                response = scraper.get(history_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data and data.get('s') == 'ok':
                        rows = []
                        for i in range(len(data['t'])):
                            rows.append([
                                datetime.fromtimestamp(data['t'][i]).strftime('%Y-%m-%d'),
                                data['o'][i],
                                data['h'][i],
                                data['l'][i],
                                data['c'][i],
                                data.get('v', [0] * len(data['c']))[i] if data.get('v') else 0
                            ])
                        
                        headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                        rows.insert(0, headers)
                        return rows
                
            except Exception as proxy_error:
                continue  # Try next proxy
        
        return [["Error: All proxies failed"]]
            
    except Exception as e:
        return [[f"Error: {str(e)}"]]

# SOLUTION 5: Browser Automation with Undetected Chrome Driver
"""
For the most robust solution, you can use undetected-chromedriver:

pip install undetected-chromedriver selenium

This approach actually runs a real browser and is harder to detect.
"""

def get_investing_data_browser_automation(investing_id, from_date, to_date):
    """
    Use browser automation to bypass Cloudflare (most reliable but slower)
    Requires: pip install undetected-chromedriver selenium
    """
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import json
        
        # Create undetected Chrome driver
        options = uc.ChromeOptions()
        options.add_argument('--headless')  # Run in background
        driver = uc.Chrome(options=options)
        
        from_date_obj = datetime.strptime(from_date, "%d/%m/%Y")
        to_date_obj = datetime.strptime(to_date, "%d/%m/%Y")
        
        end_time = int(to_date_obj.timestamp())
        start_time = int(from_date_obj.timestamp())
        
        timestamp = str(int(time.time()))
        base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        url = f"{base_url}/{timestamp}/56/56/23/history?symbol={investing_id}&resolution=D&from={start_time}&to={end_time}"
        
        driver.get(url)
        
        # Wait for response and get page content
        WebDriverWait(driver, 30).until(
            lambda d: len(d.page_source) > 100
        )
        
        page_content = driver.page_source
        driver.quit()
        
        # Extract JSON from page content
        # This will depend on how the data is returned
        if '{"s":"ok"' in page_content:
            # Extract JSON data
            start_idx = page_content.find('{"s":"ok"')
            end_idx = page_content.find('}', start_idx) + 1
            json_str = page_content[start_idx:end_idx]
            data = json.loads(json_str)
            
            if data and data.get('s') == 'ok':
                rows = []
                for i in range(len(data['t'])):
                    rows.append([
                        datetime.fromtimestamp(data['t'][i]).strftime('%Y-%m-%d'),
                        data['o'][i],
                        data['h'][i],
                        data['l'][i],
                        data['c'][i],
                        data.get('v', [0] * len(data['c']))[i] if data.get('v') else 0
                    ])
                
                headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                rows.insert(0, headers)
                return rows
        
        return [["Error: No data found in browser response"]]
        
    except Exception as e:
        return [[f"Error: {str(e)}"]]

# USAGE RECOMMENDATIONS:

"""
RECOMMENDED USAGE ORDER:

1. FIRST TRY: Enhanced CloudScraper (your working method)
   =get_investing_data_enhanced_cloudscraper("BO:503205", "01/01/2024", "31/12/2024")

2. IF #1 FAILS: ScraperAPI (5000 free calls, then paid)
   =get_investing_data_scraperapi("BO:503205", "01/01/2024", "31/12/2024", "your_scraperapi_key")

3. IF #2 FAILS: Browser automation (most reliable but slower)
   Use the browser automation method

FINDING THE RIGHT INVESTING_ID:
- Run your diagnostic script first to find the correct ID
- Your diagnostic script found working patterns like "BO:503205"
- Use that exact format in these functions

SERVICES TO SIGN UP FOR:
- ScraperAPI: https://www.scraperapi.com/ (5000 free API calls)
- ScrapeOwl: https://scrapeowl.com/ (alternative service)
- Bright Data: https://brightdata.com/ (premium option)

INSTALLATION REQUIREMENTS:
pip install cloudscraper requests pandas
pip install undetected-chromedriver selenium  # For browser automation
"""
