"""
News Cache System - Prevents re-analyzing the same news
Stores analyzed news with timestamps and auto-resets every 24 hours
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional
import hashlib


class NewsCache:
    """
    Cache system for news articles to prevent duplicate analysis
    Features:
    - Stores news article hashes and analysis results
    - Automatically resets every 24 hours
    - Prevents sending same news to Groq API multiple times
    - Sorts news by time (newest first)
    """
    
    CACHE_FILE = 'news_cache.json'
    CACHE_DURATION_HOURS = 24
    
    def __init__(self):
        self.cache_data = {
            'last_reset': datetime.now().isoformat(),
            'analyzed_news': {},  # hash -> {title, analyzed_at, sentiment, reasoning}
            'news_hashes': set()   # Quick lookup set
        }
        self._load_cache()
        self._check_and_reset()
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self.cache_data = {
                        'last_reset': data.get('last_reset', datetime.now().isoformat()),
                        'analyzed_news': data.get('analyzed_news', {}),
                        'news_hashes': set(data.get('news_hashes', []))
                    }
        except Exception as e:
            print(f"Warning: Could not load news cache: {e}")
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            data = {
                'last_reset': self.cache_data['last_reset'],
                'analyzed_news': self.cache_data['analyzed_news'],
                'news_hashes': list(self.cache_data['news_hashes'])
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save news cache: {e}")
    
    def _check_and_reset(self):
        """Check if 24 hours have passed and reset if needed"""
        try:
            last_reset = datetime.fromisoformat(self.cache_data['last_reset'])
            now = datetime.now()
            
            if now - last_reset >= timedelta(hours=self.CACHE_DURATION_HOURS):
                print(f"[CACHE] 24 hours passed, resetting news cache")
                self.reset_cache()
        except Exception as e:
            print(f"Warning: Error checking cache reset: {e}")
    
    def reset_cache(self):
        """Manually reset the cache"""
        self.cache_data = {
            'last_reset': datetime.now().isoformat(),
            'analyzed_news': {},
            'news_hashes': set()
        }
        self._save_cache()
        print("[CACHE] News cache reset successfully")
    
    def _hash_article(self, article: Dict) -> str:
        """
        Generate a unique hash for an article
        Uses title + description to identify duplicates
        """
        title = article.get('title', '').strip().lower()
        desc = article.get('description', '').strip().lower()
        
        # Create hash from title and first 100 chars of description
        content = f"{title}|{desc[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_analyzed(self, article: Dict) -> bool:
        """Check if article has already been analyzed"""
        article_hash = self._hash_article(article)
        return article_hash in self.cache_data['news_hashes']
    
    def get_cached_analysis(self, article: Dict) -> Optional[Dict]:
        """Get cached analysis for an article if it exists"""
        article_hash = self._hash_article(article)
        return self.cache_data['analyzed_news'].get(article_hash)
    
    def add_analysis(self, article: Dict, sentiment_score: float, reasoning: str):
        """
        Add analyzed article to cache
        Stores the analysis to avoid re-analyzing
        """
        article_hash = self._hash_article(article)
        
        self.cache_data['analyzed_news'][article_hash] = {
            'title': article.get('title', '')[:200],
            'analyzed_at': datetime.now().isoformat(),
            'sentiment_score': sentiment_score,
            'reasoning': reasoning[:500]
        }
        
        self.cache_data['news_hashes'].add(article_hash)
        self._save_cache()
    
    def filter_new_articles(self, articles: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter articles into new (not analyzed) and cached (already analyzed)
        Returns: (new_articles, cached_articles_with_analysis)
        """
        new_articles = []
        cached_articles = []
        
        for article in articles:
            if self.is_analyzed(article):
                # Get cached analysis
                cached = self.get_cached_analysis(article)
                if cached:
                    cached_articles.append({
                        'article': article,
                        'sentiment_score': cached['sentiment_score'],
                        'reasoning': cached['reasoning'],
                        'from_cache': True
                    })
            else:
                new_articles.append(article)
        
        return new_articles, cached_articles
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            last_reset = datetime.fromisoformat(self.cache_data['last_reset'])
            age_hours = (datetime.now() - last_reset).total_seconds() / 3600
        except:
            age_hours = 0
        
        return {
            'total_cached': len(self.cache_data['news_hashes']),
            'cache_age_hours': age_hours,
            'will_reset_in_hours': max(0, 24 - age_hours),
            'last_reset': self.cache_data['last_reset']
        }


def sort_articles_by_time(articles: List[Dict]) -> List[Dict]:
    """
    Sort articles by publication time (newest first)
    Handles various date formats from different sources
    """
    def get_article_time(article: Dict) -> datetime:
        """Extract and parse article time"""
        # Try publishedAt first (NewsAPI format)
        pub_date = article.get('publishedAt')
        if pub_date:
            try:
                return datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Try pubDate (RSS format)
        pub_date = article.get('pubDate')
        if pub_date:
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(pub_date)
            except:
                pass
        
        # Default to current time if no date found
        return datetime.now()
    
    try:
        # Sort by time, newest first
        sorted_articles = sorted(articles, key=get_article_time, reverse=True)
        return sorted_articles
    except Exception as e:
        print(f"Warning: Could not sort articles by time: {e}")
        return articles


# Global cache instance
_news_cache = None


def get_news_cache() -> NewsCache:
    """Get the global news cache instance"""
    global _news_cache
    if _news_cache is None:
        _news_cache = NewsCache()
    return _news_cache
