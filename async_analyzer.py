"""
Async/Multi-threaded Performance Optimization Module
Speeds up parallel operations like:
- Multiple symbol analysis
- News fetching from multiple sources
- Market data fetching
- LLM API calls (when analyzing multiple symbols)
"""

import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable
import time
from functools import wraps


# Global thread pool for CPU-bound tasks
_thread_pool = ThreadPoolExecutor(max_workers=10)


def async_timer(func):
    """Decorator to measure async function execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[PERF] {func.__name__} completed in {elapsed:.2f}s")
        return result
    return wrapper


def thread_timer(func):
    """Decorator to measure threaded function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[PERF] {func.__name__} completed in {elapsed:.2f}s")
        return result
    return wrapper


async def fetch_url_async(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> Optional[str]:
    """
    Async fetch URL with timeout
    Used for parallel RSS feed fetching
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == 200:
                return await response.text()
            return None
    except Exception as e:
        return None


@async_timer
async def fetch_multiple_rss_feeds_async(feed_urls: List[tuple]) -> Dict[str, List[Dict]]:
    """
    Fetch multiple RSS feeds in parallel using async
    Much faster than sequential fetching
    
    Args:
        feed_urls: List of (name, url) tuples
    
    Returns:
        Dictionary mapping feed name to articles
    """
    results = {}
    
    async with aiohttp.ClientSession(headers={'User-Agent': 'CryptoTrader/1.0'}) as session:
        tasks = []
        for name, url in feed_urls:
            tasks.append((name, fetch_url_async(session, url)))
        
        # Fetch all feeds in parallel
        for name, task in zip([n for n, _ in feed_urls], [t for _, t in tasks]):
            content = await task
            if content:
                # Parse RSS (simple regex parsing)
                import re
                items = []
                for block in re.findall(r'<item>(.*?)</item>', content, re.S | re.I):
                    title_m = re.search(r'<title>(.*?)</title>', block, re.S | re.I)
                    desc_m = re.search(r'<description>(.*?)</description>', block, re.S | re.I)
                    title = re.sub('<.*?>', '', title_m.group(1)).strip() if title_m else ''
                    desc = re.sub('<.*?>', '', desc_m.group(1)).strip() if desc_m else ''
                    if title or desc:
                        items.append({'title': title, 'description': desc})
                results[name] = items[:10]  # Limit to 10 per feed
            else:
                results[name] = []
    
    return results


def analyze_symbol_with_threading(
    symbol: str,
    yf_symbol: str,
    articles: List[Dict],
    get_market_data_func: Callable,
    analyze_sentiment_func: Callable,
    calculate_signal_func: Callable
) -> Optional[Dict]:
    """
    Analyze a single symbol (thread-safe wrapper)
    Used by thread pool for parallel symbol analysis
    """
    try:
        symbol_name = yf_symbol.replace('-USD', '')
        
        # Analyze sentiment with AI
        sentiment_score, sentiment_reason = analyze_sentiment_func(articles, symbol_name)
        
        # Skip if AI unavailable
        if sentiment_score is None:
            return None
        
        news_count = len(articles)
        
        # Get market data
        market_data = get_market_data_func(yf_symbol)
        if not market_data:
            return None
        
        # Calculate signal
        signal = calculate_signal_func(sentiment_score, news_count, market_data, symbol_name, articles)
        
        if signal and signal['confidence'] > 0.3:
            # Extract indicator signals for learning
            indicators_signals = {}
            for ind_name, ind_data in market_data['indicators'].items():
                if isinstance(ind_data, dict) and 'signal' in ind_data:
                    indicators_signals[ind_name] = ind_data['signal']
            
            return {
                'symbol': symbol_name,
                'yf_symbol': yf_symbol,
                'signal': signal,
                'sentiment_reason': sentiment_reason,
                'news_count': news_count,
                'indicators': indicators_signals
            }
        
        return None
    
    except Exception as e:
        print(f"[ERROR] Error analyzing {symbol}: {e}")
        return None


@thread_timer
def analyze_multiple_symbols_parallel(
    symbol_articles: Dict[str, List[Dict]],
    get_market_data_func: Callable,
    analyze_sentiment_func: Callable,
    calculate_signal_func: Callable,
    max_workers: int = 8
) -> List[Dict]:
    """
    Analyze multiple symbols in parallel using thread pool
    
    Args:
        symbol_articles: Dict mapping yf_symbol to articles
        get_market_data_func: Function to get market data
        analyze_sentiment_func: Function to analyze sentiment
        calculate_signal_func: Function to calculate trade signal
        max_workers: Maximum parallel workers
    
    Returns:
        List of signal dictionaries
    """
    signals = []
    
    print(f"[PARALLEL] Analyzing {len(symbol_articles)} symbols with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_symbol = {}
        for yf_symbol, articles in symbol_articles.items():
            symbol_name = yf_symbol.replace('-USD', '')
            future = executor.submit(
                analyze_symbol_with_threading,
                symbol_name,
                yf_symbol,
                articles,
                get_market_data_func,
                analyze_sentiment_func,
                calculate_signal_func
            )
            future_to_symbol[future] = symbol_name
        
        # Collect results as they complete
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result:
                    signals.append(result)
                    print(f"  [✓] {symbol}: Signal found (confidence: {result['signal']['confidence']*100:.1f}%)")
                else:
                    print(f"  [○] {symbol}: No strong signal")
            except Exception as e:
                print(f"  [✗] {symbol}: Error - {e}")
    
    return signals


async def async_fetch_and_analyze_news(
    newsapi_client,
    rss_sources: List[tuple],
    cutoff_hours: int = 24  # 24 hours for comprehensive news coverage
) -> List[Dict]:
    """
    Fetch news from all sources in parallel (NewsAPI + RSS feeds)
    Much faster than sequential fetching
    """
    from datetime import datetime, timedelta
    
    articles = []
    cutoff = datetime.now() - timedelta(hours=cutoff_hours)
    
    # Create tasks for parallel execution
    tasks = []
    
    # Task 1: NewsAPI (runs in thread pool since it's blocking)
    async def fetch_newsapi():
        try:
            loop = asyncio.get_event_loop()
            query = 'cryptocurrency OR bitcoin OR ethereum OR crypto OR blockchain OR altcoin'
            resp = await loop.run_in_executor(
                _thread_pool,
                lambda: newsapi_client.get_everything(q=query, language='en', sort_by='publishedAt', page_size=100)
            )
            
            news_articles = []
            for article in resp.get('articles', []):
                pub_date = article.get('publishedAt')
                if pub_date:
                    try:
                        pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        if pub_dt.replace(tzinfo=None) < cutoff:
                            continue
                    except:
                        pass
                news_articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'publishedAt': article.get('publishedAt', '')
                })
            return news_articles
        except Exception as e:
            print(f"[ASYNC] NewsAPI error: {e}")
            return []
    
    # Task 2: RSS feeds (truly async)
    async def fetch_rss():
        rss_results = await fetch_multiple_rss_feeds_async(rss_sources)
        rss_articles = []
        for name, items in rss_results.items():
            for item in items:
                rss_articles.append({
                    'title': item['title'],
                    'description': item['description'],
                    'source': name,
                    'publishedAt': datetime.now().isoformat()
                })
        return rss_articles
    
    # Run both in parallel
    print("[ASYNC] Fetching news from all sources in parallel...")
    start = time.time()
    
    newsapi_task = asyncio.create_task(fetch_newsapi())
    rss_task = asyncio.create_task(fetch_rss())
    
    newsapi_articles = await newsapi_task
    rss_articles = await rss_task
    
    articles = newsapi_articles + rss_articles
    
    elapsed = time.time() - start
    print(f"[ASYNC] Fetched {len(articles)} articles in {elapsed:.2f}s (parallel)")
    
    return articles


def run_async(coro):
    """
    Run async coroutine in sync context
    Helper function to bridge sync/async code
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


# Batch processing for LLM calls
class BatchLLMProcessor:
    """
    Batch multiple LLM requests to reduce latency
    Groups similar requests together
    """
    
    def __init__(self, batch_size: int = 5, wait_time: float = 0.5):
        self.batch_size = batch_size
        self.wait_time = wait_time
        self.queue = []
        self.results = {}
    
    async def add_request(self, request_id: str, llm_client, prompt: str):
        """Add a request to the batch queue"""
        self.queue.append((request_id, llm_client, prompt))
        
        # Process if batch is full
        if len(self.queue) >= self.batch_size:
            await self.process_batch()
        
        return self.results.get(request_id)
    
    async def process_batch(self):
        """Process all queued requests in parallel"""
        if not self.queue:
            return
        
        tasks = []
        for request_id, llm_client, prompt in self.queue:
            tasks.append(self._process_single(request_id, llm_client, prompt))
        
        await asyncio.gather(*tasks)
        self.queue = []
    
    async def _process_single(self, request_id: str, llm_client, prompt: str):
        """Process a single LLM request"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                _thread_pool,
                lambda: llm_client.chat(
                    model_name="qwen2.5:7b",  # Fast analytical model for batch processing
                    prompt=prompt,
                    temperature=0.3,
                    num_predict=200
                )
            )
            self.results[request_id] = response
        except Exception as e:
            self.results[request_id] = None
