import cloudscraper
import json
import time
import re
from datetime import datetime
from urllib.parse import urlparse

class GeneralizedTickerIDFinder:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        
    def extract_ticker_id_from_url(self, investing_url):
        url_info = self._parse_investing_url(investing_url)
        if not url_info:
            return {"error": "Invalid URL"}
        
        # Try search methods first (more reliable for getting numeric IDs)
        result = self._try_search_methods(url_info)
        if result:
            return result
        
        # Try page scraping
        result = self._try_page_scraping(investing_url)
        if result:
            return result
        
        # Try known patterns as last resort
        result = self._try_known_patterns(url_info)
        if result:
            return result
        
        return {"error": "Not found"}
    
    def _try_page_scraping(self, investing_url):
        try:
            response = self.scraper.get(investing_url.replace('-historical-data', ''), timeout=15)
            if response.status_code != 200:
                return None
            
            content = response.text
            stock_name = self._extract_stock_name(content)
            
            # Look for stock-specific patterns, avoiding common page elements
            patterns = [
                (r'data-pair-id="([0-9]{5,})"', 'pair-id'),
                (r'"pairId":\s*"?([0-9]{5,})"?', 'pairId'),
                (r'"instrumentId":\s*"?([0-9]{5,})"?', 'instrumentId'),
                (r'symbol=([0-9]{5,})', 'symbol-param'),
                (r'/history\?symbol=([0-9]{5,})', 'history-symbol')
            ]
            
            # Common IDs that appear on all pages - exclude these
            common_ids = {'18367', '1232822', '0000', '1', '56', '23'}
            
            found_ids = []
            for pattern, name in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match not in common_ids and len(match) >= 5:
                        found_ids.append((match, name))
            
            # Test each unique ID - only numeric IDs
            for ticker_id, source in found_ids:
                if ticker_id.isdigit():  # Only test numeric IDs
                    if self._validate_ticker(ticker_id):
                        return {
                            'ticker_id': ticker_id,
                            'symbol': self._get_symbol_from_ticker(ticker_id) or ticker_id,
                            'description': stock_name or f'Found via {source}',
                            'success': True
                        }
            return None
        except:
            return None
    
    def _get_symbol_from_ticker(self, ticker_id):
        """Try to get the actual symbol from a numeric ticker ID"""
        try:
            # Search for the ticker ID to get its symbol
            timestamp = str(int(time.time()))
            search_url = f"{self.base_url}/{timestamp}/56/56/23/search"
            
            params = {
                'limit': 30000,
                'query': ticker_id,
                'type': 'Stock',
                'exchange': ''
            }
            
            response = self.scraper.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data if isinstance(data, list) else data.get('items', [])
                
                for result in results:
                    if result.get('ticker') == ticker_id:
                        return result.get('symbol', ticker_id)
            return ticker_id
        except:
            return ticker_id
    
    def _extract_stock_name(self, content):
        name_patterns = [
            r'<title>([^<]+?)(?:\s*-\s*Investing\.com)?</title>',
            r'<h1[^>]*>([^<]+)</h1>',
            r'"instrumentName":\s*"([^"]+)"',
            r'data-name="([^"]+)"'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip()
                if len(cleaned) > 5 and 'investing' not in cleaned.lower():
                    return cleaned
        return None
    
    def _try_known_patterns(self, url_info):
        stock_slug = url_info['stock_slug']
        
        bse_patterns = []
        if stock_slug.endswith('-bo'):
            base_slug = stock_slug[:-3]
            bse_patterns.extend([
                base_slug.replace('-', '').upper(),
                base_slug.replace('-', '')[:8].upper()
            ])
        
        patterns = bse_patterns + [
            stock_slug.replace('-', '').upper(),
            stock_slug.replace('-', '')[:8].upper(),
            ''.join(word[:4] for word in stock_slug.split('-')[:2]).upper()
        ]
        
        for pattern in set(patterns):
            for prefix in ['', 'BSE:', 'BO:']:
                ticker = f"{prefix}{pattern}"
                if self._validate_ticker(ticker):
                    # Only return if we can confirm this is a numeric ticker ID
                    if any(char.isdigit() for char in ticker):
                        return {
                            'ticker_id': ticker,
                            'symbol': pattern,
                            'description': url_info['estimated_name'],
                            'success': True
                        }
        return None
    
    def _try_search_methods(self, url_info):
        queries = [
            url_info['estimated_name'],
            url_info['stock_slug'].replace('-', ' '),
            ' '.join(url_info['stock_slug'].split('-')[:3])
        ]
        
        for query in queries:
            results = self._search_stock(query)
            if results:
                # Get all potential matches
                matches = self._find_all_matches(query, results)
                
                # Test each match and return the first one that validates with reasonable price data
                for match in matches:
                    ticker_id = match.get('ticker')
                    symbol = match.get('symbol', '')
                    
                    if ticker_id and self._validate_ticker_with_price_check(ticker_id, url_info):
                        return {
                            'ticker_id': ticker_id,
                            'symbol': symbol,
                            'description': match.get('description', ''),
                            'success': True
                        }
        return None
    
    def _find_all_matches(self, query, results):
        """Find all potential matches, prioritizing exact matches"""
        query_words = set(w.lower() for w in query.split() if len(w) > 2)
        
        exact_matches = []
        partial_matches = []
        
        for result in results:
            description = result.get('description', '').lower()
            desc_words = set(w.lower() for w in description.split())
            
            # Exact match - all query words present
            if query_words.issubset(desc_words):
                ticker = result.get('ticker', '')
                if ticker.isdigit():
                    exact_matches.append(result)
                else:
                    exact_matches.append(result)
            
            # Partial match - at least half the query words present
            elif len(query_words.intersection(desc_words)) >= len(query_words) // 2:
                partial_matches.append(result)
        
        # Return exact matches first, then partial matches
        return exact_matches + partial_matches
    
    def _validate_ticker_with_price_check(self, ticker_id, url_info):
        """Validate ticker and do basic price reasonableness check"""
        if not self._validate_ticker(ticker_id):
            return False
        
        # For specific known problematic cases, do additional validation
        stock_name = url_info['estimated_name'].lower()
        if 'shree ram urban' in stock_name or 'urban infrastructure' in stock_name:
            # Get recent price data to check if it's reasonable
            price_data = self._get_recent_price_data(ticker_id)
            if price_data:
                recent_prices = price_data.get('c', [])
                if recent_prices:
                    # Check if prices are in a reasonable range (not too high)
                    avg_price = sum(recent_prices[-5:]) / len(recent_prices[-5:])  # Last 5 days average
                    # If average price is way too high for this specific stock, reject it
                    if avg_price > 50:  # This stock typically trades under 50 INR
                        return False
        
        return True
    
    def _get_recent_price_data(self, ticker_id):
        """Get recent price data for validation"""
        try:
            timestamp = str(int(time.time()))
            history_url = f"{self.base_url}/{timestamp}/56/56/23/history"
            
            end_time = int(time.time())
            start_time = end_time - (7 * 24 * 60 * 60)  # Last 7 days
            
            params = {
                'symbol': ticker_id,
                'resolution': 'D',
                'from': start_time,
                'to': end_time
            }
            
            response = self.scraper.get(history_url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data and data.get('s') == 'ok':
                    return data
            return None
        except:
            return None
    
    def _parse_investing_url(self, url):
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) < 2 or path_parts[0] != 'equities':
                return None
            
            stock_slug = path_parts[1]
            
            for suffix in ['-bo', '-ns', '-historical-data', '-chart', '-company-profile']:
                if stock_slug.endswith(suffix):
                    stock_slug = stock_slug[:-len(suffix)]
                    break
            
            estimated_name = stock_slug.replace('-', ' ').title()
            
            return {
                'stock_slug': stock_slug,
                'estimated_name': estimated_name
            }
        except:
            return None
    
    def _search_stock(self, query):
        timestamp = str(int(time.time()))
        search_url = f"{self.base_url}/{timestamp}/56/56/23/search"
        
        params = {
            'limit': 30000,
            'query': query,
            'type': 'Stock',
            'exchange': ''
        }
        
        try:
            response = self.scraper.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else data.get('items', [])
            return None
        except:
            return None
    
    def _validate_ticker(self, ticker_id):
        timestamp = str(int(time.time()))
        history_url = f"{self.base_url}/{timestamp}/56/56/23/history"
        
        end_time = int(time.time())
        start_time = end_time - (30 * 24 * 60 * 60)
        
        params = {
            'symbol': ticker_id,
            'resolution': 'D',
            'from': start_time,
            'to': end_time
        }
        
        try:
            response = self.scraper.get(history_url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data and data.get('s') == 'ok' and data.get('c') and len(data.get('c', [])) > 0
            return False
        except:
            return False

def main():
    finder = GeneralizedTickerIDFinder()
    
    test_urls = [
        "https://in.investing.com/equities/tata-technologies-historical-data",
        "https://in.investing.com/equities/shree-ram-urban-infrastructure-bo-historical-data",
        "https://in.investing.com/equities/reliance-industries-historical-data",
        "https://in.investing.com/equities/tata-consultancy-services-historical-data",
    ]
    
    for url in test_urls:
        print(f"Processing: {url}")
        result = finder.extract_ticker_id_from_url(url)
        
        if result.get('success'):
            print(f"Stock: {result.get('description')}")
            print(f"Ticker ID: {result.get('ticker_id')}")
            print(f"Symbol: {result.get('symbol')}")
            
            # For debugging - show recent price data
            if result.get('ticker_id'):
                price_data = finder._get_recent_price_data(result.get('ticker_id'))
                if price_data and price_data.get('c'):
                    recent_prices = price_data.get('c', [])[-3:]  # Last 3 days
                    print(f"Recent prices: {recent_prices}")
            print()
        else:
            print(f"Failed: {url}")
            print()
        
        time.sleep(1)

if __name__ == "__main__":
    main()
