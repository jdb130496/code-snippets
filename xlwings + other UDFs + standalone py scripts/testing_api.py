import cloudscraper
import json
import time
import re
from datetime import datetime

class ShreeraamStockFinder:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        
    def search_stock(self, query, limit=30000):
        """Standard search method with detailed response inspection"""
        timestamp = str(int(time.time()))
        search_url = f"{self.base_url}/{timestamp}/56/56/23/search"
        
        params = {
            'limit': limit,
            'query': query,
            'type': 'Stock',
            'exchange': ''
        }
        
        try:
            response = self.scraper.get(search_url, params=params, timeout=30)
            print(f"Search '{query}': Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Raw response: {json.dumps(data, indent=2)}")
                return data
            else:
                print(f"Error: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            return None
    
    def get_historical_data(self, ticker_id, days_back=30):
        """Get historical data using ticker ID"""
        timestamp = str(int(time.time()))
        history_url = f"{self.base_url}/{timestamp}/56/56/23/history"
        
        end_time = int(time.time())
        start_time = end_time - (days_back * 24 * 60 * 60)
        
        params = {
            'symbol': ticker_id,
            'resolution': 'D',
            'from': start_time,
            'to': end_time
        }
        
        try:
            response = self.scraper.get(history_url, params=params, timeout=30)
            print(f"Historical data for {ticker_id}: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Historical response: {json.dumps(data, indent=2)}")
                
                if data and data.get('s') == 'ok':
                    return data
                else:
                    print(f"No historical data: {data.get('s', 'unknown status')}")
                    return None
            else:
                print(f"Historical data error: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"Historical data error for {ticker_id}: {e}")
            return None
    
    def scrape_investing_page_for_ticker_id(self):
        """Scrape the actual Investing.com page for the real ticker ID"""
        print("\n=== SCRAPING INVESTING.COM PAGE FOR TICKER ID ===")
        
        try:
            # The correct page for Shree Ram Urban Infrastructure
            url = "https://www.investing.com/equities/shree-ram-urban-infrastructure-bo"
            response = self.scraper.get(url, timeout=30)
            
            print(f"Page access: Status {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Look for various patterns that might contain the real ticker ID
                patterns = {
                    # Look for data-pair-id in HTML
                    'data-pair-id': r'data-pair-id="([^"]+)"',
                    # Look for pair ID in JavaScript
                    'pair_id_js': r'"pairId":\s*"?([0-9]+)"?',
                    'pair_id_alt': r'"pair_id":\s*"?([0-9]+)"?',
                    # Look for instrument/symbol IDs
                    'instrument_id': r'"instrumentId":\s*"?([0-9]+)"?',
                    'symbol_id': r'"symbolId":\s*"?([0-9]+)"?',
                    # Look for ticker/symbol info
                    'ticker_data': r'"ticker":\s*"([^"]+)"',
                    'symbol_data': r'"symbol":\s*"([^"]+)"',
                    # BSE specific patterns
                    'bse_code': r'BSE[:\s]*([0-9]+)',
                    'stock_code': r'Code[:\s]*([0-9]+)',
                }
                
                found_ids = {}
                for name, pattern in patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Remove duplicates and filter out obviously wrong matches
                        clean_matches = []
                        for match in matches:
                            if match not in clean_matches and match not in ['VIX', 'NVDA', 'US500']:
                                clean_matches.append(match)
                        
                        if clean_matches:
                            found_ids[name] = clean_matches
                            print(f"Found {name}: {clean_matches}")
                
                # Test each found ID
                for id_type, ids in found_ids.items():
                    for ticker_id in ids:
                        print(f"\n--- Testing extracted ID ({id_type}): {ticker_id} ---")
                        
                        # Try both direct ticker and with BSE prefix
                        test_tickers = [ticker_id, f"BSE:{ticker_id}", f"BO:{ticker_id}"]
                        
                        for test_ticker in test_tickers:
                            historical = self.get_historical_data(test_ticker)
                            if historical:
                                print(f"✅ SUCCESS! Working ticker ID: {test_ticker}")
                                return {
                                    'ticker': test_ticker,
                                    'original_id': ticker_id,
                                    'id_type': id_type,
                                    'description': 'Shree Ram Urban Infrastructure Ltd',
                                    'historical_data': historical,
                                    'method': 'page_scraping'
                                }
                
                print("❌ No working ticker IDs found from page scraping")
                return None
            else:
                print(f"❌ Could not access page: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Page scraping failed: {e}")
            return None
    
    def try_known_patterns(self):
        """Try known BSE and ticker patterns for this specific stock"""
        print("\n=== TRYING KNOWN PATTERNS ===")
        
        # Known information about this stock
        known_patterns = [
            # BSE stock code variations
            "503205",
            "BSE:503205", 
            "BO:503205",
            # Ticker variations
            "SHREERAM",
            "BSE:SHREERAM",
            "BO:SHREERAM",
            # Investing.com variations
            "SRAM",
            "BSE:SRAM", 
            "BO:SRAM",
            # Try with different prefixes
            "NSE:SHREERAM",
            "IN:SHREERAM"
        ]
        
        for pattern in known_patterns:
            print(f"\n--- Testing pattern: {pattern} ---")
            
            # First try search to see if it returns the right company
            search_result = self.search_stock(pattern)
            if search_result and isinstance(search_result, list):
                for result in search_result:
                    description = result.get('description', '').lower()
                    if 'shree ram urban infrastructure' in description:
                        print(f"✅ FOUND correct company in search: {result}")
                        ticker_id = result.get('ticker')
                        if ticker_id:
                            historical = self.get_historical_data(ticker_id)
                            if historical:
                                return {
                                    'ticker': ticker_id,
                                    'pattern': pattern,
                                    'description': result.get('description'),
                                    'historical_data': historical,
                                    'method': 'known_patterns',
                                    'search_result': result
                                }
            
            # Then try direct historical data
            historical = self.get_historical_data(pattern)
            if historical:
                print(f"✅ SUCCESS with direct historical data: {pattern}")
                return {
                    'ticker': pattern,
                    'pattern': pattern,
                    'description': 'Shree Ram Urban Infrastructure Ltd (Direct)',
                    'historical_data': historical,
                    'method': 'direct_pattern'
                }
        
        print("❌ No known patterns worked")
        return None
    
    def comprehensive_search(self):
        """Try all methods systematically"""
        print("🔍 COMPREHENSIVE SEARCH FOR SHREE RAM URBAN INFRASTRUCTURE")
        print("=" * 60)
        print("Issue identified: Search API returns SRMA (wrong company) instead of SRAM")
        print("=" * 60)
        
        # Method 1: Try known patterns first
        result = self.try_known_patterns()
        if result:
            return result
        
        # Method 2: Scrape the actual page
        result = self.scrape_investing_page_for_ticker_id()
        if result:
            return result
        
        # Method 3: Try exact company name search
        print("\n=== TRYING EXACT COMPANY NAME ===")
        exact_searches = [
            "Shree Ram Urban Infrastructure",
            "Shree Ram Urban Infrastructure Ltd",
            "SHREE RAM URBAN INFRASTRUCTURE LTD"
        ]
        
        for search_term in exact_searches:
            print(f"\n--- Searching: '{search_term}' ---")
            results = self.search_stock(search_term)
            if results and isinstance(results, list):
                for result in results:
                    description = result.get('description', '').lower()
                    if 'shree ram urban infrastructure' in description:
                        print(f"✅ FOUND exact match: {result}")
                        ticker_id = result.get('ticker')
                        if ticker_id:
                            historical = self.get_historical_data(ticker_id)
                            if historical:
                                return {
                                    'ticker': ticker_id,
                                    'search_term': search_term,
                                    'description': result.get('description'),
                                    'historical_data': historical,
                                    'method': 'exact_search',
                                    'search_result': result
                                }
        
        print("\n❌ All methods failed")
        return None

def main():
    finder = ShreeraamStockFinder()
    
    print("🏢 SHREE RAM URBAN INFRASTRUCTURE TICKER FINDER")
    print("=" * 50)
    print("🚨 DEBUGGING: Search API returns wrong company (SRMA instead of SRAM)")
    print("=" * 50)
    
    result = finder.comprehensive_search()
    
    if result:
        print("\n" + "🎉 SUCCESS!" + " " * 20)
        print("=" * 50)
        
        print(f"Method: {result.get('method')}")
        print(f"Ticker ID: {result.get('ticker')}")
        print(f"Description: {result.get('description')}")
        
        if result.get('search_result'):
            print(f"Full search result: {result['search_result']}")
        
        if result.get('historical_data'):
            historical = result['historical_data']
            print(f"\n📊 HISTORICAL DATA SAMPLE:")
            print(f"Status: {historical.get('s', 'unknown')}")
            if historical.get('c'):  # Close prices
                closes = historical['c'][-3:]  # Last 3 close prices
                print(f"Recent close prices: {closes}")
            if historical.get('t'):  # Timestamps
                timestamps = historical['t'][-3:]
                dates = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d') for ts in timestamps]
                print(f"Recent dates: {dates}")
        
        print(f"\n✅ Use this ticker ID: {result.get('ticker')}")
    else:
        print("\n❌ TICKER NOT FOUND")
        print("\nPossible reasons:")
        print("1. Stock might be delisted/suspended")
        print("2. Different API authentication needed")  
        print("3. Stock only available on BSE direct API")
        print("4. Try manual inspection of network requests on investing.com page")

if __name__ == "__main__":
    main()
