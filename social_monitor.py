"""
CoinMarketCap Community Analysis Monitor
Uses CoinMarketCap API for market data analysis
Free plan: 10K calls/month, latest data only
"""

import requests
import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time


class CoinMarketCapMonitor:
    """
    Monitor cryptocurrency market data from CoinMarketCap API
    Uses free plan with caching to avoid rate limits
    """

    def __init__(self, api_key: str = "ef534dd08cb04f37b83edd972bc2b6a7"):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Cache settings
        self.cache_file = 'cmc_cache.json'
        self.cache_duration = timedelta(hours=2)  # Cache for 2 hours since script runs every 2h
        self.cache = self._load_cache()

        # Free plan limits us to latest data only
        self.top_cryptos = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LTC', 'MATIC']

    def _load_cache(self) -> Dict:
        """Load cached data from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Check if cache is still valid
                    cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01T00:00:00'))
                    if datetime.now() - cache_time < self.cache_duration:
                        return cache_data
        except Exception as e:
            print(f"[CMC] Error loading cache: {e}")
        return {'timestamp': datetime.now().isoformat(), 'data': {}}

    def _save_cache(self):
        """Save data to cache file"""
        try:
            self.cache['timestamp'] = datetime.now().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"[CMC] Error saving cache: {e}")

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        cache_time = datetime.fromisoformat(self.cache.get('timestamp', '2000-01-01T00:00:00'))
        return datetime.now() - cache_time < self.cache_duration

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with caching"""
        cache_key = f"{endpoint}_{str(params)}"

        # Check cache first
        if self._is_cache_valid() and cache_key in self.cache.get('data', {}):
            print(f"[CMC] Using cached data for {endpoint}")
            return self.cache['data'][cache_key]

        # Make API request
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Cache the response
                if 'data' not in self.cache:
                    self.cache['data'] = {}
                self.cache['data'][cache_key] = data
                self._save_cache()
                print(f"[CMC] Fetched fresh data for {endpoint}")
                return data
            else:
                print(f"[CMC] API Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"[CMC] Request error: {e}")
            return None

    def get_latest_listings(self, limit: int = 100) -> List[Dict]:
        """
        Get latest cryptocurrency listings
        Free plan endpoint

        Args:
            limit: Number of cryptocurrencies to fetch (max 5000)

        Returns:
            List of cryptocurrency data
        """
        params = {
            'start': '1',
            'limit': str(limit),
            'convert': 'USD'
        }

        response = self._make_request('/cryptocurrency/listings/latest', params)

        if response and 'data' in response:
            listings = response['data']
            print(f"[CMC] Retrieved {len(listings)} cryptocurrency listings")
            return listings

        return []

    def get_crypto_quotes(self, symbols: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Get latest quotes for specific cryptocurrencies
        Free plan endpoint

        Args:
            symbols: List of cryptocurrency symbols

        Returns:
            Dictionary mapping symbols to quote data
        """
        if symbols is None:
            symbols = self.top_cryptos

        symbol_string = ','.join(symbols)
        params = {
            'symbol': symbol_string,
            'convert': 'USD'
        }

        response = self._make_request('/cryptocurrency/quotes/latest', params)

        if response and 'data' in response:
            quotes = response['data']
            print(f"[CMC] Retrieved quotes for {len(quotes)} cryptocurrencies")
            return quotes

        return {}

    def get_global_metrics(self) -> Dict:
        """
        Get global cryptocurrency market metrics
        Free plan endpoint

        Returns:
            Global market data
        """
        response = self._make_request('/global-metrics/quotes/latest')

        if response and 'data' in response:
            metrics = response['data']
            print(f"[CMC] Retrieved global market metrics")
            return metrics

        return {}

    def analyze_market_sentiment(self) -> Dict:
        """
        Analyze market data for community sentiment indicators

        Returns:
            Dictionary with sentiment analysis
        """
        listings = self.get_latest_listings(50)  # Top 50 cryptos
        quotes = self.get_crypto_quotes()
        global_metrics = self.get_global_metrics()

        if not listings:
            return {'sentiment_score': 0, 'confidence': 0, 'indicators': {}}

        # Analyze market cap changes (community interest)
        total_market_cap = sum(crypto.get('quote', {}).get('USD', {}).get('market_cap', 0) for crypto in listings)
        total_volume_24h = sum(crypto.get('quote', {}).get('USD', {}).get('volume_24h', 0) for crypto in listings)

        # Calculate average price change percentage
        price_changes = []
        volume_changes = []

        for crypto in listings[:20]:  # Top 20 for detailed analysis
            quote = crypto.get('quote', {}).get('USD', {})
            percent_change_24h = quote.get('percent_change_24h', 0)
            volume_24h = quote.get('volume_24h', 0)
            market_cap = quote.get('market_cap', 0)

            if percent_change_24h != 0:
                price_changes.append(percent_change_24h)

            # Volume relative to market cap (activity indicator)
            if market_cap > 0:
                volume_ratio = volume_24h / market_cap
                volume_changes.append(volume_ratio)

        avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
        avg_volume_ratio = sum(volume_changes) / len(volume_changes) if volume_changes else 0

        # Global metrics analysis
        btc_dominance = global_metrics.get('btc_dominance', 0)
        eth_dominance = global_metrics.get('eth_dominance', 0)
        altcoin_market_cap = global_metrics.get('quote', {}).get('USD', {}).get('altcoin_market_cap', 0)

        # Calculate sentiment score based on multiple factors
        # Price momentum (weighted heavily)
        price_sentiment = max(-1, min(1, avg_price_change / 10))  # Normalize to -1 to 1

        # Volume activity (community engagement)
        volume_sentiment = max(-1, min(1, (avg_volume_ratio - 0.02) / 0.08))  # Normalize based on typical ratios

        # Market cap distribution (diversification vs concentration)
        concentration_score = min(1, btc_dominance / 50)  # Lower concentration = more positive
        market_breadth = 1 - concentration_score

        # Combined sentiment: 50% price, 30% volume, 20% market breadth
        sentiment_score = 0.5 * price_sentiment + 0.3 * volume_sentiment + 0.2 * market_breadth

        # Confidence based on data availability
        data_points = len(price_changes) + len(volume_changes)
        confidence = min(1.0, data_points / 50)  # More data = more confidence

        indicators = {
            'avg_price_change_24h': avg_price_change,
            'avg_volume_ratio': avg_volume_ratio,
            'btc_dominance': btc_dominance,
            'total_market_cap': total_market_cap,
            'total_volume_24h': total_volume_24h,
            'market_breadth_score': market_breadth,
            'data_points_analyzed': data_points
        }

        print(f"[CMC] Market sentiment analysis: {sentiment_score:.3f} (confidence: {confidence:.3f})")

        return {
            'sentiment_score': sentiment_score,
            'confidence': confidence,
            'indicators': indicators,
            'timestamp': datetime.now().isoformat()
        }

    def get_community_signals(self) -> Dict[str, List[Dict]]:
        """
        Get community analysis signals from CoinMarketCap data
        Replaces social media signals with market-based community indicators

        Returns:
            Dictionary with market signals
        """
        print("\n[CMC] Fetching CoinMarketCap community signals...")
        print("=" * 70)

        # Get market data
        listings = self.get_latest_listings(20)  # Top 20 cryptos
        quotes = self.get_crypto_quotes()
        global_metrics = self.get_global_metrics()
        sentiment_analysis = self.analyze_market_sentiment()

        # Convert listings to signal format
        market_signals = []
        for crypto in listings:
            quote = crypto.get('quote', {}).get('USD', {})
            market_signals.append({
                'symbol': crypto.get('symbol', ''),
                'name': crypto.get('name', ''),
                'price': quote.get('price', 0),
                'market_cap': quote.get('market_cap', 0),
                'volume_24h': quote.get('volume_24h', 0),
                'percent_change_24h': quote.get('percent_change_24h', 0),
                'type': 'market_data',
                'timestamp': datetime.now().isoformat()
            })

        # Global metrics as signals
        global_signals = []
        if global_metrics:
            usd_quote = global_metrics.get('quote', {}).get('USD', {})
            global_signals.append({
                'metric': 'total_market_cap',
                'value': usd_quote.get('total_market_cap', 0),
                'type': 'global_metric',
                'timestamp': datetime.now().isoformat()
            })
            global_signals.append({
                'metric': 'btc_dominance',
                'value': global_metrics.get('btc_dominance', 0),
                'type': 'global_metric',
                'timestamp': datetime.now().isoformat()
            })

        signals = {
            'market_data': market_signals,
            'global_metrics': global_signals,
            'sentiment_analysis': [sentiment_analysis],
            'reddit': [],  # Empty for compatibility
            'whale_alerts': [],  # Empty for compatibility
            'twitter_trends': []  # Empty for compatibility
        }

        total = sum(len(v) for v in signals.values() if isinstance(v, list))
        print(f"[CMC] Total community signals collected: {total}")
        print("=" * 70)
        print()

        return signals


    # Alias for backward compatibility
    get_all_social_signals = get_community_signals


# Compatibility aliases for existing code
SocialMediaMonitor = CoinMarketCapMonitor


def aggregate_social_sentiment(signals: Dict[str, List[Dict]]) -> Dict:
    """
    Aggregate market signals into community sentiment score
    Replaces social sentiment with market-based sentiment

    Args:
        signals: Dictionary of market signals

    Returns:
        Dictionary with aggregated sentiment metrics
    """
    sentiment_data = signals.get('sentiment_analysis', [{}])[0]

    if sentiment_data:
        return sentiment_data

    # Fallback if no sentiment analysis
    return {
        'sentiment_score': 0,
        'confidence': 0,
        'indicators': {},
        'timestamp': datetime.now().isoformat()
    }


# Export main functions
__all__ = [
    'CoinMarketCapMonitor',
    'SocialMediaMonitor',  # Alias for compatibility
    'aggregate_social_sentiment'
]
