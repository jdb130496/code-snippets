import pandas as pd
from datetime import datetime
import requests
import cloudscraper
import json
import time
import re

class StockIDFinder:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.tvc_base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        self.api_base_url = "http://api.scraperlink.com/investpy/"
        self.email = "asharindani51@gmail.com"
        
    def search_tvc_stocks(self, query, limit=30000):
        """Search using TVC API to find potential matches"""
        timestamp = str(int(time.time()))
        search_url = f"{self.tvc_base_url}/{timestamp}/56/56/23/search"
        
        params = {
            'limit': limit,
            'query': query,
            'type': 'Stock',
            'exchange': ''
        }
        
        try:
            response = self.scraper.get(search_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"TVC Search error: {e}")
            return None
    
    def scrape_investing_page_for_ids(self, company_url):
        """Scrape investing.com page to extract various IDs"""
        try:
            response = self.scraper.get(company_url, timeout=30)
            if response.status_code != 200:
                return None
                
            content = response.text
            
            # Patterns to find different types of IDs
            patterns = {
                'tvc_ticker': r'"pair_id":\s*"?([0-9]+)"?',
                'investing_id': r'"curr_id":\s*"?([0-9]+)"?',
                'pair_id': r'data-pair-id="([^"]+)"',
                'instrument_id': r'"instrumentId":\s*"?([0-9]+)"?',
                'symbol_id': r'"symbolId":\s*"?([0-9]+)"?',
                'bse_code': r'BSE[:\s]*([0-9]+)',
                'nse_code': r'NSE[:\s]*([0-9]+)',
            }
            
            found_ids = {}
            for name, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Remove duplicates
                    unique_matches = list(set(matches))
                    found_ids[name] = unique_matches
            
            return found_ids
            
        except Exception as e:
            print(f"Page scraping error: {e}")
            return None
    
    def test_investing_api_id(self, investing_id, test_days=7):
        """Test if an investing ID works with your API"""
        try:
            # Use recent dates for testing
            end_date = datetime.now()
            start_date = datetime.now().replace(day=1)  # Start of current month
            
            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")
            
            # Construct URL like your original function
            url = f'{self.api_base_url}?email={self.email}&url=https%3A%2F%2Fapi.investing.com%2Fapi%2Ffinancialdata%2Fhistorical%2F{investing_id}%3Fstart-date%3D{from_date}%26end-date%3D{to_date}%26time-frame%3DDaily%26add-missing-rows%3Dfalse'
            
            print(f"Testing investing ID: {investing_id}")
            print(f"URL: {url}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                try:
                    json_output = response.json()
                    if 'data' in json_output and json_output['data']:
                        print(f"✅ SUCCESS! ID {investing_id} returned {len(json_output['data'])} records")
                        
                        # Show sample data
                        sample_data = json_output['data'][:3]  # First 3 records
                        for i, record in enumerate(sample_data):
                            print(f"   Record {i+1}: Date={record.get('rowDate', 'N/A')}, Close={record.get('last_close', 'N/A')}")
                        
                        return True, json_output
                    else:
                        print(f"❌ ID {investing_id}: No data returned")
                        return False, None
                except json.JSONDecodeError:
                    print(f"❌ ID {investing_id}: Invalid JSON response")
                    return False, None
            else:
                print(f"❌ ID {investing_id}: HTTP {response.status_code}")
                return False, None
                
        except Exception as e:
            print(f"❌ ID {investing_id}: Error - {e}")
            return False, None
    
    def find_stock_id(self, company_name, company_url=None):
        """Main function to find working stock ID"""
        print(f"🔍 SEARCHING FOR: {company_name}")
        print("=" * 60)
        
        working_ids = []
        
        # Method 1: Try TVC search first
        print("\n=== METHOD 1: TVC SEARCH ===")
        search_terms = [
            company_name,
            company_name.replace(" ", ""),
            company_name.split()[0],  # First word
            company_name.split()[-1], # Last word
        ]
        
        for term in search_terms:
            print(f"\nSearching TVC for: '{term}'")
            results = self.search_tvc_stocks(term)
            if results and isinstance(results, list):
                for result in results:
                    description = result.get('description', '').lower()
                    if any(word.lower() in description for word in company_name.split()):
                        print(f"Found potential match: {result}")
                        ticker_id = result.get('ticker')
                        if ticker_id:
                            # Test this as investing ID
                            success, data = self.test_investing_api_id(ticker_id)
                            if success:
                                working_ids.append({
                                    'id': ticker_id,
                                    'method': 'TVC Search',
                                    'description': result.get('description'),
                                    'source': f"Search term: {term}"
                                })
        
        # Method 2: Page scraping if URL provided
        if company_url:
            print(f"\n=== METHOD 2: PAGE SCRAPING ===")
            print(f"Scraping: {company_url}")
            
            scraped_ids = self.scrape_investing_page_for_ids(company_url)
            if scraped_ids:
                print("Found IDs from page:")
                for id_type, ids in scraped_ids.items():
                    print(f"  {id_type}: {ids}")
                
                # Test each found ID
                all_ids_to_test = []
                for id_type, ids in scraped_ids.items():
                    for id_val in ids:
                        all_ids_to_test.append((id_val, id_type))
                
                for id_val, id_type in all_ids_to_test:
                    success, data = self.test_investing_api_id(id_val)
                    if success:
                        working_ids.append({
                            'id': id_val,
                            'method': 'Page Scraping',
                            'description': f'From {id_type}',
                            'source': company_url
                        })
        
        # Method 3: Try common ID patterns
        print(f"\n=== METHOD 3: COMMON PATTERNS ===")
        if company_url and 'investing.com/equities/' in company_url:
            # Extract potential stock codes from URL
            url_parts = company_url.split('/')
            if len(url_parts) > 0:
                stock_slug = url_parts[-1]
                print(f"Testing URL-based patterns for: {stock_slug}")
                
                # Try different variations
                test_patterns = [
                    stock_slug.replace('-', ''),
                    stock_slug.upper(),
                    stock_slug.lower(),
                ]
                
                for pattern in test_patterns:
                    if pattern.isdigit():  # Only test numeric patterns
                        success, data = self.test_investing_api_id(pattern)
                        if success:
                            working_ids.append({
                                'id': pattern,
                                'method': 'URL Pattern',
                                'description': f'Derived from URL slug: {stock_slug}',
                                'source': company_url
                            })
        
        # Show results
        print(f"\n{'🎉 RESULTS' if working_ids else '❌ NO RESULTS'}")
        print("=" * 60)
        
        if working_ids:
            print(f"Found {len(working_ids)} working ID(s):")
            for i, result in enumerate(working_ids, 1):
                print(f"\n{i}. INVESTING ID: {result['id']}")
                print(f"   Method: {result['method']}")
                print(f"   Description: {result['description']}")
                print(f"   Source: {result['source']}")
                print(f"   ✅ Use this ID in your get_url_data_id_new() function")
            
            # Show the best recommendation
            best_id = working_ids[0]['id']
            print(f"\n🎯 RECOMMENDED ID: {best_id}")
            print(f"📋 Copy this ID and use it in your Excel function:")
            print(f"   =get_url_data_id_new(\"{best_id}\", \"01/01/2024\", \"31/12/2024\")")
            
        else:
            print("No working IDs found. Possible reasons:")
            print("1. Stock might be delisted or suspended")
            print("2. Different API authentication needed")
            print("3. Try manual inspection of the investing.com page")
            print("4. The stock might not be available through this API")
        
        return working_ids

# Your original function (unchanged)
def get_url_data_id_new(investingid, from_date, to_date):
    # Convert date strings to the required format
    from_date = datetime.strptime(from_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    to_date = datetime.strptime(to_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    # Construct the URL
    url = f'http://api.scraperlink.com/investpy/?email=asharindani51@gmail.com&url=https%3A%2F%2Fapi.investing.com%2Fapi%2Ffinancialdata%2Fhistorical%2F{investingid}%3Fstart-date%3D{from_date}%26end-date%3D{to_date}%26time-frame%3DDaily%26add-missing-rows%3Dfalse'
    # Fetch data from the API
    response = requests.get(url)
    json_output = response.json()
    data_list = json_output['data']
    # Convert data_list into a pandas dataframe
    df = pd.DataFrame(data_list)
    # Remove commas from integer and float columns
    int_float_columns = ['last_close','last_open','last_max','last_min','change_precent','last_closeRaw', 'last_openRaw', 'last_maxRaw', 'last_minRaw', 'change_precentRaw']
    for col in int_float_columns:
        df[col] = df[col].astype(str).str.replace(',', '').astype('float')
    # Format columns
    df['direction_color'] = df['direction_color'].astype(str)
    df['rowDate'] = pd.to_datetime(df['rowDate'], format='%b %d, %Y').apply(lambda x: x.date())
    df['rowDateTimestamp'] = pd.to_datetime(df['rowDateTimestamp']).apply(lambda x: x.date())
    # Create a matrix (list of lists) from the dataframe
    matrix = df.values.tolist()
    # Add headers at the beginning of the list
    headers = df.columns.tolist()
    matrix.insert(0, headers)
    return matrix

# Example usage
if __name__ == "__main__":
    finder = StockIDFinder()
    
    # Example 1: Search for Shree Ram Urban Infrastructure
    print("EXAMPLE 1: Shree Ram Urban Infrastructure")
    results = finder.find_stock_id(
        company_name="Shree Ram Urban Infrastructure",
        company_url="https://www.investing.com/equities/shree-ram-urban-infrastructure-bo"
    )
    
    print("\n" + "="*80 + "\n")
    
    # Example 2: Search for any other company
    print("EXAMPLE 2: Tata Technologies")
    results = finder.find_stock_id(
        company_name="Tata Technologies",
        company_url="https://www.investing.com/equities/tata-technologies"
    )
    
    # You can add more examples here
    print("\n" + "="*80)
    print("💡 USAGE INSTRUCTIONS:")
    print("1. Run this script")
    print("2. Copy the recommended INVESTING ID from the output")
    print("3. Use that ID in your get_url_data_id_new() function")
    print("4. Example: get_url_data_id_new('123456', '01/01/2024', '31/12/2024')")
