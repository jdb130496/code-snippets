import cloudscraper
import time
from urllib.parse import urlparse

class GeneralizedTickerIDFinder:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.base_url = "https://tvc4.investing.com/b12dcd570c91a748a3b7dd4a7ee79167"
        
    def extract_ticker_id_from_url(self, investing_url):
        url_info = self._parse_investing_url(investing_url)
        if not url_info:
            return {"error": "Invalid URL"}
        
        stock_slug = url_info['stock_slug']
        estimated_name = url_info['estimated_name']
        
        queries = [
            'Shree Ram Urban Infrastructure',
            'SHREERAM',
            'SRAM',
            '503205',
            'Shree Ram Urban Infrastructure Ltd'
        ]
        
        for query in queries:
            results = self._search_stock(query)
            if results:
                for result in results:
                    ticker_id = result.get('ticker')
                    symbol = result.get('symbol', '')
                    description = result.get('description', '')
                    
                    if ticker_id and symbol:
                        desc_lower = description.lower()
                        if ('shree' in desc_lower and 'ram' in desc_lower and 'urban' in desc_lower) or symbol.upper() == 'SRAM':
                            if self._validate_ticker(ticker_id):
                                return {
                                    'ticker_id': ticker_id,
                                    'symbol': symbol,
                                    'description': description,
                                    'success': True
                                }
        
        return {"error": "Not found"}
    
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

    def _get_recent_price_data(self, ticker_id):
        try:
            timestamp = str(int(time.time()))
            history_url = f"{self.base_url}/{timestamp}/56/56/23/history"
            
            end_time = int(time.time())
            start_time = end_time - (7 * 24 * 60 * 60)
            
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

def main():
    finder = GeneralizedTickerIDFinder()
    
    test_urls = [
        "https://in.investing.com/equities/shree-ram-urban-infrastructure-bo-historical-data",
    ]
    
    for url in test_urls:
        result = finder.extract_ticker_id_from_url(url)
        
        if result.get('success'):
            print(f"Stock: {result.get('description')}")
            print(f"Ticker ID: {result.get('ticker_id')}")
            print(f"Symbol: {result.get('symbol')}")
            
            if result.get('ticker_id'):
                price_data = finder._get_recent_price_data(result.get('ticker_id'))
                if price_data and price_data.get('c'):
                    recent_prices = price_data.get('c', [])[-3:]
                    print(f"Recent prices: {recent_prices}")
        else:
            print(f"Failed: {url}")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
