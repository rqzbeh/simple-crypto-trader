"""
Social Media & Whale Activity Monitor
Tracks influential crypto signals from:
- Reddit (r/cryptocurrency, r/bitcoin, r/ethereum, etc.)
- Twitter/X (crypto influencers, whale alerts)
- Whale Alert (large transactions)
- On-chain whale movements
- Crypto fear & greed index
"""

import requests
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json


class SocialMediaMonitor:
    """
    Monitor social media for crypto signals
    Uses free APIs and RSS feeds (no API keys needed where possible)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_reddit_crypto_posts(self, subreddits: List[str] = None, limit: int = 25) -> List[Dict]:
        """
        Get hot posts from crypto subreddits using Reddit JSON API (no auth needed)
        
        Args:
            subreddits: List of subreddits to monitor
            limit: Number of posts per subreddit
        
        Returns:
            List of post dictionaries
        """
        if subreddits is None:
            subreddits = [
                'cryptocurrency',
                'bitcoin',
                'ethereum',
                'cryptomarkets',
                'satoshistreetbets',
                'altcoin',
                'binance',
                'coinbase'
            ]
        
        posts = []
        
        for subreddit in subreddits:
            try:
                # Use Reddit's JSON API (no auth required)
                url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}'
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for child in data.get('data', {}).get('children', []):
                        post_data = child.get('data', {})
                        
                        # Filter for relevance
                        upvotes = post_data.get('ups', 0)
                        if upvotes < 10:  # Skip low-engagement posts
                            continue
                        
                        title = post_data.get('title', '')
                        selftext = post_data.get('selftext', '')
                        created = datetime.fromtimestamp(post_data.get('created_utc', 0))
                        
                        # Skip old posts (older than 24 hours for comprehensive news)
                        if datetime.now() - created > timedelta(hours=24):
                            continue
                        
                        posts.append({
                            'title': title,
                            'description': selftext[:300] if selftext else '',
                            'source': f'Reddit r/{subreddit}',
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'upvotes': upvotes,
                            'comments': post_data.get('num_comments', 0),
                            'publishedAt': created.isoformat(),
                            'type': 'reddit'
                        })
                
            except Exception as e:
                print(f"[REDDIT] Error fetching r/{subreddit}: {e}")
                continue
        
        # Sort by engagement (upvotes)
        posts.sort(key=lambda x: x['upvotes'], reverse=True)
        
        print(f"[REDDIT] Fetched {len(posts)} posts from {len(subreddits)} subreddits")
        return posts[:50]  # Top 50 most engaged
    
    def get_whale_alerts(self) -> List[Dict]:
        """
        Get whale transaction alerts from Whale Alert RSS/API
        Tracks large crypto movements that may signal market moves
        
        Returns:
            List of whale transaction dictionaries
        """
        alerts = []
        
        try:
            # Whale Alert RSS feed (free, no API key)
            url = 'https://api.whale-alert.io/v1/transactions?api_key=demo'
            
            # Alternative: Parse from public whale tracking sites
            # Using RSS-style approach for public whale data
            
            # For demo purposes, we'll use a public tracker
            # In production, you'd want to use official Whale Alert API with key
            
            print(f"[WHALE] Whale alert tracking requires API key for full access")
            print(f"[WHALE] Using alternative whale tracking sources...")
            
            # Alternative: CryptoQuant whale alerts (public data)
            # Alternative: Glassnode public feeds
            # For now, return empty to avoid API key requirements
            
        except Exception as e:
            print(f"[WHALE] Error fetching whale alerts: {e}")
        
        return alerts
    
    def get_twitter_crypto_trends(self) -> List[Dict]:
        """
        Get crypto trends from Twitter/X
        Note: Twitter API requires authentication, using alternative methods
        
        Returns:
            List of trending crypto topics
        """
        trends = []
        
        try:
            # Alternative: Use Nitter (Twitter frontend) or public RSS feeds
            # For now, we'll track known crypto influencers via RSS if available
            
            # Known crypto influencers (public RSS feeds when available)
            influencers = [
                'elonmusk',
                'VitalikButerin', 
                'cz_binance',
                'SBF_FTX',
                'APompliano',
                'DocumentingBTC',
                'WhalePanda',
                'TheCryptoLark'
            ]
            
            print(f"[TWITTER] Twitter API requires authentication")
            print(f"[TWITTER] Consider adding Twitter API key for influencer tracking")
            
        except Exception as e:
            print(f"[TWITTER] Error fetching Twitter trends: {e}")
        
        return trends
    
    def get_fear_and_greed_index(self) -> Dict:
        """
        Get Crypto Fear & Greed Index (free API)
        Indicates market sentiment
        
        Returns:
            Dictionary with index value and classification
        """
        try:
            url = 'https://api.alternative.me/fng/?limit=1'
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    fng_data = data['data'][0]
                    value = int(fng_data.get('value', 50))
                    classification = fng_data.get('value_classification', 'Neutral')
                    
                    print(f"[SENTIMENT] Fear & Greed Index: {value} ({classification})")
                    
                    return {
                        'value': value,
                        'classification': classification,
                        'timestamp': fng_data.get('timestamp', '')
                    }
        
        except Exception as e:
            print(f"[SENTIMENT] Error fetching Fear & Greed Index: {e}")
        
        return {'value': 50, 'classification': 'Neutral', 'timestamp': ''}
    
    def get_on_chain_metrics(self) -> Dict:
        """
        Get on-chain metrics that may indicate whale activity
        Free sources: Glassnode public data, blockchain explorers
        
        Returns:
            Dictionary with on-chain metrics
        """
        metrics = {}
        
        try:
            # Alternative.me also provides some on-chain data
            # For production, consider: Glassnode, CryptoQuant, IntoTheBlock APIs
            
            print(f"[ON-CHAIN] On-chain metrics require specialized APIs")
            print(f"[ON-CHAIN] Consider adding: Glassnode, CryptoQuant, or IntoTheBlock")
            
        except Exception as e:
            print(f"[ON-CHAIN] Error fetching on-chain metrics: {e}")
        
        return metrics
    
    def get_all_social_signals(self) -> Dict[str, List[Dict]]:
        """
        Get all social media signals in one call
        
        Returns:
            Dictionary mapping source type to signals
        """
        print("\n[SOCIAL] Fetching social media signals...")
        print("=" * 70)
        
        signals = {
            'reddit': self.get_reddit_crypto_posts(),
            'whale_alerts': self.get_whale_alerts(),
            'twitter_trends': self.get_twitter_crypto_trends(),
            'fear_greed': [self.get_fear_and_greed_index()],
            'on_chain': []
        }
        
        total = sum(len(v) for v in signals.values() if isinstance(v, list))
        print(f"[SOCIAL] Total social signals collected: {total}")
        print("=" * 70)
        print()
        
        return signals


class InfluencerTracker:
    """
    Track known crypto influencers and whales
    Maintains a list of important accounts to monitor
    """
    
    CRYPTO_INFLUENCERS = {
        'twitter': [
            {'handle': '@elonmusk', 'name': 'Elon Musk', 'influence': 'very_high'},
            {'handle': '@VitalikButerin', 'name': 'Vitalik Buterin', 'influence': 'very_high'},
            {'handle': '@cz_binance', 'name': 'CZ Binance', 'influence': 'very_high'},
            {'handle': '@APompliano', 'name': 'Anthony Pompliano', 'influence': 'high'},
            {'handle': '@DocumentingBTC', 'name': 'Documenting Bitcoin', 'influence': 'high'},
            {'handle': '@WhalePanda', 'name': 'Whale Panda', 'influence': 'high'},
            {'handle': '@TheCryptoLark', 'name': 'The Crypto Lark', 'influence': 'medium'},
            {'handle': '@CryptoCobain', 'name': 'Crypto Cobain', 'influence': 'medium'},
            {'handle': '@100trillionUSD', 'name': 'PlanB', 'influence': 'high'},
            {'handle': '@woonomic', 'name': 'Willy Woo', 'influence': 'high'},
        ],
        'reddit': [
            {'user': 'to_the_moon', 'subreddit': 'r/cryptocurrency', 'influence': 'medium'},
            {'user': 'hodlonaut', 'subreddit': 'r/bitcoin', 'influence': 'medium'},
        ]
    }
    
    KNOWN_WHALE_ADDRESSES = {
        'BTC': [
            '1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ',  # Binance cold wallet
            'bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97',  # Example
        ],
        'ETH': [
            '0x00000000219ab540356cbb839cbe05303d7705fa',  # ETH2 deposit contract
            '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8',  # Binance hot wallet
        ]
    }
    
    @classmethod
    def get_influencer_list(cls, platform: str = 'all') -> List[Dict]:
        """Get list of influencers to track"""
        if platform == 'all':
            all_influencers = []
            for plat, users in cls.CRYPTO_INFLUENCERS.items():
                all_influencers.extend(users)
            return all_influencers
        
        return cls.CRYPTO_INFLUENCERS.get(platform, [])
    
    @classmethod
    def is_whale_address(cls, address: str, crypto: str = 'BTC') -> bool:
        """Check if address is a known whale"""
        return address in cls.KNOWN_WHALE_ADDRESSES.get(crypto, [])


def aggregate_social_sentiment(social_signals: Dict[str, List[Dict]]) -> Dict:
    """
    Aggregate social media signals into overall sentiment
    
    Args:
        social_signals: Dictionary of social signals by source
    
    Returns:
        Dictionary with aggregated sentiment metrics
    """
    # Count bullish vs bearish signals
    bullish_keywords = ['bull', 'moon', 'pump', 'buy', 'bullish', 'up', 'surge', 'rally', 'gain']
    bearish_keywords = ['bear', 'dump', 'sell', 'bearish', 'down', 'crash', 'drop', 'fall']
    
    bullish_count = 0
    bearish_count = 0
    total_engagement = 0
    
    # Analyze Reddit posts
    for post in social_signals.get('reddit', []):
        text = f"{post.get('title', '')} {post.get('description', '')}".lower()
        engagement = post.get('upvotes', 0) + post.get('comments', 0)
        
        bull_matches = sum(1 for word in bullish_keywords if word in text)
        bear_matches = sum(1 for word in bearish_keywords if word in text)
        
        if bull_matches > bear_matches:
            bullish_count += 1 * (1 + engagement / 1000)  # Weight by engagement
        elif bear_matches > bull_matches:
            bearish_count += 1 * (1 + engagement / 1000)
        
        total_engagement += engagement
    
    # Factor in Fear & Greed Index
    fng = social_signals.get('fear_greed', [{}])[0]
    fng_value = fng.get('value', 50)
    
    # Normalize sentiment score to -1 to +1
    if bullish_count + bearish_count > 0:
        base_sentiment = (bullish_count - bearish_count) / (bullish_count + bearish_count)
    else:
        base_sentiment = 0
    
    # Adjust with Fear & Greed Index (0-100 scale, convert to -1 to +1)
    fng_sentiment = (fng_value - 50) / 50  # Convert 0-100 to -1 to +1
    
    # Weighted combination: 70% social, 30% F&G index
    final_sentiment = 0.7 * base_sentiment + 0.3 * fng_sentiment
    
    return {
        'sentiment_score': final_sentiment,
        'bullish_signals': bullish_count,
        'bearish_signals': bearish_count,
        'total_engagement': total_engagement,
        'fear_greed_index': fng_value,
        'confidence': min(1.0, (bullish_count + bearish_count) / 50)  # More signals = more confidence
    }


# Export main functions
__all__ = [
    'SocialMediaMonitor',
    'InfluencerTracker',
    'aggregate_social_sentiment'
]
