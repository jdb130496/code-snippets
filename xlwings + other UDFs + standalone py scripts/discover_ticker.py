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
        
        search_queries = [
            url_info['estimated_name'],
            url_info['stock_slug'].replace('-', ' '),
            ' '.join(url_info['stock_slug'].split('-')[:3]),
            ' '.join(url_info['stock_slug'].split('-')[:2])
        ]
        
        for query in search_queries:
            results = self._search_stock(query)
            if results:
                best_match = self._find_best_match(query, results)
                if best_match:
                    ticker_id = best_match.get('ticker')
                    if ticker_id and self._validate_ticker(ticker_id):
                        return {
                            'ticker_id': ticker_id,
                            'symbol': best_match.get('symbol', ''),
                            'description': best_match.get('description', ''),
                            'success': True
                        }
        
        return {"error": "Not found"}
    
    def _find_best_match(self, query, results):
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        if not query_words:
            return None
        
        for result in results:
            description = result.get('description', '').lower()
            desc_words = [w.lower() for w in description.split()]
            
            exact_matches = sum(1 for word in query_words if word in desc_words)
            
            if exact_matches == len(query_words):
                return result
            
            if len(query_words) >= 3 and exact_matches >= len(query_words) - 1:
                missing_words = [w for w in query_words if w not in desc_words]
                if missing_words:
                    missing_word = missing_words[0]
                    if any(missing_word in desc_word for desc_word in desc_words):
                        return result
        
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
            response = self.scraper.get(search_url, params=params, timeout=30)
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
            response = self.scraper.get(history_url, params=params, timeout=30)
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
        result = finder.extract_ticker_id_from_url(url)
        
        if result.get('success'):
            print(f"Stock: {result.get('description')}")
            print(f"Ticker ID: {result.get('ticker_id')}")
            print(f"Symbol: {result.get('symbol')}")
            print()
        else:
            print(f"Failed: {url}")
            print()
        
        time.sleep(1)

if __name__ == "__main__":
    main()
