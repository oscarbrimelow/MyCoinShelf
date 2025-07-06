import os
import requests
from datetime import datetime, timedelta
import json

class GoogleFinancePriceFetcher:
    def __init__(self):
        self.sheet_id = None
        self.api_key = None
        self.last_update = None
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        self.prices = {
            'gold_usd_per_oz': 0,
            'silver_usd_per_oz': 0,
            'gold_zar_per_oz': 0,
            'silver_zar_per_oz': 0,
            'lastUpdate': None
        }
    
    def setup_google_sheets(self, sheet_id, api_key):
        """Setup Google Sheets integration"""
        self.sheet_id = sheet_id
        self.api_key = api_key
        
        # Create the sheet if it doesn't exist
        self._create_price_sheet()
    
    def _create_price_sheet(self):
        """Create a Google Sheet with live price formulas"""
        if not self.sheet_id or not self.api_key:
            return
            
        # This would create a sheet with formulas like:
        # =GOOGLEFINANCE("CURRENCY:USDZAR") for exchange rate
        # =GOOGLEFINANCE("GCUSD") for gold price
        # =GOOGLEFINANCE("SIUSD") for silver price
        
        # For now, we'll use a simpler approach with direct API calls
        pass
    
    def fetch_prices_from_sheets(self):
        """Fetch prices from Google Sheets"""
        if not self.sheet_id or not self.api_key:
            return None
            
        try:
            # Google Sheets API URL
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.sheet_id}/values/Sheet1!A1:D10?key={self.api_key}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            values = data.get('values', [])
            
            # Parse the values to extract prices
            # This depends on how you structure your sheet
            return self._parse_sheet_values(values)
            
        except Exception as e:
            print(f"Error fetching from Google Sheets: {e}")
            return None
    
    def _parse_sheet_values(self, values):
        """Parse Google Sheets values to extract prices"""
        # This is a placeholder - you'd structure your sheet with specific cells
        # containing the GOOGLEFINANCE formulas
        return None

# Alternative: Direct API approach using reliable sources
class ReliablePriceFetcher:
    def __init__(self):
        self.last_update = None
        self.cache_duration = timedelta(minutes=30)  # Cache for 30 minutes
        self.prices = {
            'gold_usd_per_oz': 0,
            'silver_usd_per_oz': 0,
            'gold_zar_per_oz': 0,
            'silver_zar_per_oz': 0,
            'lastUpdate': None
        }
    
    def fetch_prices(self):
        """Fetch prices from multiple reliable sources"""
        if self._is_cache_valid():
            return self.prices
        
        try:
            # Try multiple sources for redundancy
            prices = self._fetch_from_alpha_vantage()
            if not prices:
                prices = self._fetch_from_finnhub()
            if not prices:
                prices = self._fetch_from_yahoo_finance()
            
            if prices:
                self.prices.update(prices)
                self.prices['lastUpdate'] = datetime.now().isoformat()
                self.last_update = datetime.now()
                
                # Save to file for persistence
                self._save_prices()
            
            return self.prices
            
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return self._load_cached_prices()
    
    def _fetch_from_alpha_vantage(self):
        """Fetch from Alpha Vantage API (free tier available)"""
        try:
            # You'd need to get a free API key from https://www.alphavantage.co/
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                return None
            
            # Gold price
            gold_url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAU&to_currency=USD&apikey={api_key}"
            gold_response = requests.get(gold_url, timeout=10)
            gold_data = gold_response.json()
            
            # Silver price (using XAG)
            silver_url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAG&to_currency=USD&apikey={api_key}"
            silver_response = requests.get(silver_url, timeout=10)
            silver_data = silver_response.json()
            
            # USD to ZAR exchange rate
            zar_url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=ZAR&apikey={api_key}"
            zar_response = requests.get(zar_url, timeout=10)
            zar_data = zar_response.json()
            
            if (gold_data.get('Realtime Currency Exchange Rate') and 
                silver_data.get('Realtime Currency Exchange Rate') and
                zar_data.get('Realtime Currency Exchange Rate')):
                
                gold_usd = float(gold_data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
                silver_usd = float(silver_data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
                usd_zar_rate = float(zar_data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
                
                return {
                    'gold_usd_per_oz': gold_usd,
                    'silver_usd_per_oz': silver_usd,
                    'gold_zar_per_oz': gold_usd * usd_zar_rate,
                    'silver_zar_per_oz': silver_usd * usd_zar_rate
                }
            
        except Exception as e:
            print(f"Alpha Vantage error: {e}")
        
        return None
    
    def _fetch_from_finnhub(self):
        """Fetch from Finnhub API (free tier available)"""
        try:
            api_key = os.getenv('FINNHUB_API_KEY')
            if not api_key:
                return None
            
            # Finnhub provides forex and commodity data
            # This is a simplified version - you'd need to check their specific endpoints
            headers = {'X-Finnhub-Token': api_key}
            
            # Get gold and silver prices (symbols may vary)
            # You'd need to check Finnhub's documentation for exact symbols
            
        except Exception as e:
            print(f"Finnhub error: {e}")
        
        return None
    
    def _fetch_from_yahoo_finance(self):
        """Fetch from Yahoo Finance (more reliable than some APIs)"""
        try:
            # Yahoo Finance symbols for gold and silver
            symbols = {
                'gold': 'GC=F',  # Gold futures
                'silver': 'SI=F',  # Silver futures
                'usd_zar': 'USDZAR=X'  # USD to ZAR
            }
            
            prices = {}
            
            for metal, symbol in symbols.items():
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if data.get('chart', {}).get('result'):
                    result = data['chart']['result'][0]
                    if result.get('meta', {}).get('regularMarketPrice'):
                        prices[metal] = result['meta']['regularMarketPrice']
            
            if len(prices) == 3:  # All prices fetched
                return {
                    'gold_usd_per_oz': prices['gold'],
                    'silver_usd_per_oz': prices['silver'],
                    'gold_zar_per_oz': prices['gold'] * prices['usd_zar'],
                    'silver_zar_per_oz': prices['silver'] * prices['usd_zar']
                }
            
        except Exception as e:
            print(f"Yahoo Finance error: {e}")
        
        return None
    
    def _is_cache_valid(self):
        """Check if cached prices are still valid"""
        if not self.last_update:
            return False
        return datetime.now() - self.last_update < self.cache_duration
    
    def _save_prices(self):
        """Save prices to a local file for persistence"""
        try:
            with open('cached_prices.json', 'w') as f:
                json.dump(self.prices, f)
        except Exception as e:
            print(f"Error saving prices: {e}")
    
    def _load_cached_prices(self):
        """Load prices from local cache file"""
        try:
            with open('cached_prices.json', 'r') as f:
                cached = json.load(f)
                self.prices.update(cached)
                return self.prices
        except Exception as e:
            print(f"Error loading cached prices: {e}")
            return self.prices

# Simple web scraping approach (fallback)
class WebScraperPriceFetcher:
    def __init__(self):
        self.last_update = None
        self.cache_duration = timedelta(hours=2)  # Cache for 2 hours
        self.prices = {
            'gold_usd_per_oz': 0,
            'silver_usd_per_oz': 0,
            'gold_zar_per_oz': 0,
            'silver_zar_per_oz': 0,
            'lastUpdate': None
        }
    
    def fetch_prices(self):
        """Scrape prices from reliable websites"""
        if self._is_cache_valid():
            return self.prices
        
        try:
            # This would use requests + BeautifulSoup to scrape
            # from sites like kitco.com, goldprice.org, etc.
            # For now, this is a placeholder
            
            # Example structure:
            # import requests
            # from bs4 import BeautifulSoup
            # 
            # url = "https://www.kitco.com/gold-price-today-usa/"
            # response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            # soup = BeautifulSoup(response.content, 'html.parser')
            # price_element = soup.find('span', {'class': 'price'})
            # price = float(price_element.text.replace('$', '').replace(',', ''))
            
            pass
            
        except Exception as e:
            print(f"Web scraping error: {e}")
        
        return self.prices
    
    def _is_cache_valid(self):
        if not self.last_update:
            return False
        return datetime.now() - self.last_update < self.cache_duration

# Main price fetcher that tries multiple sources
class MainPriceFetcher:
    def __init__(self):
        self.reliable_fetcher = ReliablePriceFetcher()
        self.web_scraper = WebScraperPriceFetcher()
        self.google_finance = GoogleFinancePriceFetcher()
    
    def get_prices(self):
        """Get prices from the most reliable available source"""
        
        # Try reliable APIs first
        prices = self.reliable_fetcher.fetch_prices()
        if prices and prices['gold_usd_per_oz'] > 0:
            return prices
        
        # Fallback to web scraping
        prices = self.web_scraper.fetch_prices()
        if prices and prices['gold_usd_per_oz'] > 0:
            return prices
        
        # Return cached prices if available
        return self.reliable_fetcher.prices

# Global instance
price_fetcher = MainPriceFetcher() 
