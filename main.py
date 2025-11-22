#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Crypto Trader - NEWS-DRIVEN Cryptocurrency Trading Signal Generator

[TARGET] PRIMARY APPROACH: NEWS TRADING (85-100%)
- News sentiment and AI analysis are the MAIN signal sources (85-90%)
- Technical indicators serve as FILTERS ONLY (10-15%)
- Technicals used for: entry price, stop loss, take profit, leverage calculation
- Trade based on market psychology, news events, and AI reasoning
- Technicals validate/filter out bad setups, not generate signals

Built for 24/7 crypto markets with SHORT-TERM trades (2 hours max duration)
"""

import os
import sys
import re
import json
import math
import time
import logging
import logging.handlers
import requests
from datetime import datetime, timedelta
import pytz
from functools import lru_cache
from newsapi import NewsApiClient
import yfinance as yf
import pandas as pd
import numpy as np

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup comprehensive logging
def setup_logging():
    """Setup comprehensive logging with file rotation and console output"""
    # Create logs directory
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # File handler with rotation (10MB, keep 5 files)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'crypto_trader.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Error file handler (separate file for errors)
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'crypto_trader_errors.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    # Suppress noisy third-party logs
    logging.getLogger('yfinance').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    return logger

# Initialize logging
logger = setup_logging()

# Import candlestick pattern analyzer and LLM analyzer
from candlestick_analyzer import get_all_candlestick_indicators
from llm_analyzer import CryptoMarketAnalyzer
from news_cache import get_news_cache, sort_articles_by_time
from social_monitor import SocialMediaMonitor, aggregate_social_sentiment
from async_analyzer import analyze_multiple_symbols_parallel

# Import configuration
from config import (
    TARGET_RR_RATIO,
    MIN_STOP_PCT,
    MAX_STOP_PCT,
    MIN_TP_PCT,
    MAX_TP_PCT,
    TRADE_DURATION_HOURS,
    MIN_LEVERAGE,
    MAX_LEVERAGE_CRYPTO,
    EXPECTED_RETURN_PER_SENTIMENT,
    NEWS_IMPACT_MULTIPLIER,
    MAX_NEWS_BONUS,
    LOW_MONEY_MODE,
    DAILY_RISK_LIMIT,
    MAX_LEVERAGE_STOCK,
    INDICATOR_WEIGHTS,
    ML_ENABLED,
    ML_MODEL_FILE,
    ML_SCALER_FILE,
    ML_MIN_CONFIDENCE,
    ML_RETRAIN_THRESHOLD,
    TRADE_LOG_FILE,
    DAILY_RISK_FILE,
    ATR_STOP_MULTIPLIER,
    REALISTIC_MOVEMENT_ATR_MULT,
    TP_REALISTIC_CAP_MULT,
    BASE_TECH_RETURN_MULT,
    TP_CAP_BASE,
    ML_CONF_BLEND_HEURISTIC_WEIGHT,
    ML_CONF_BLEND_MODEL_WEIGHT,
    ML_LEVERAGE_LOW_PROB_FACTOR,
    ML_LEVERAGE_HIGH_PROB_INCREMENT,
    apply_trade_bounds
)

try:
    from predictor import ProbabilityPredictor
    predictor_available = True
except ImportError:
    predictor_available = False

# Try to import optional components
try:
    from multi_provider_llm import MultiProviderLLMClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: MultiProviderLLMClient not available.")

try:
    from ensemble_learning import EnsembleSignalGenerator
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False

try:
    from symbol_strategies import SymbolStrategyManager
    SYMBOL_STRATEGIES_AVAILABLE = True
except ImportError:
    SYMBOL_STRATEGIES_AVAILABLE = False

try:
    from backtesting import Backtester
    BACKTESTING_AVAILABLE = True
except ImportError:
    BACKTESTING_AVAILABLE = False

try:
    from real_time_monitor import TradeMonitor
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    import pandas as pd
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: ML libraries not available. Install scikit-learn, numpy, pandas, joblib")

# Configure logging
logging.getLogger('yfinance').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# ==================== CONFIGURATION ====================

# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not NEWS_API_KEY:
    logger.warning('NEWS_API_KEY not set. Running in demo news mode (no live articles).')
    NEWS_API_KEY = None  # Explicitly mark missing
    newsapi = None
else:
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Initialize multi-provider LLM client if available
if LLM_AVAILABLE:
    try:
        llm_client = MultiProviderLLMClient()
        market_analyzer = CryptoMarketAnalyzer(llm_client)
    except Exception as e:
        print(f"Warning: Could not initialize LLM client: {e}")
        llm_client = None
        market_analyzer = CryptoMarketAnalyzer(None)
else:
    llm_client = None
    market_analyzer = CryptoMarketAnalyzer(None)

probability_predictor = ProbabilityPredictor(llm_client=llm_client) if ML_ENABLED and predictor_available else None

print("=" * 70)
print("SIMPLE CRYPTO TRADER - AI-Powered Signal Generator")
print("=" * 70)
print(f"NEWS_API: {'OK' if NEWS_API_KEY else 'MISSING'}")
if LLM_AVAILABLE and llm_client:
    # Show budget status
    budget_status = llm_client.get_budget_status()
    providers_list = ', '.join([v['provider'] for v in budget_status.values()])
    print(f"LLM_API: OK ({providers_list})")
else:
    print("LLM_API: Not Available")
print(f"TELEGRAM: {'OK' if TELEGRAM_BOT_TOKEN else 'DISABLED'}")
print(f"ML Support: {'OK' if ML_AVAILABLE else 'DISABLED'}")

# Initialize enhancement modules
ensemble_generator = EnsembleSignalGenerator(market_analyzer) if ENSEMBLE_AVAILABLE else None
symbol_strategy_mgr = SymbolStrategyManager() if SYMBOL_STRATEGIES_AVAILABLE else None
backtester = Backtester() if BACKTESTING_AVAILABLE else None
trade_monitor = TradeMonitor() if MONITOR_AVAILABLE else None

print(f"Ensemble Voting: {'✓' if ENSEMBLE_AVAILABLE else '✗'}")
print(f"Symbol Strategies: {'✓' if SYMBOL_STRATEGIES_AVAILABLE else '✗'}")
print(f"Backtesting: {'✓' if BACKTESTING_AVAILABLE else '✗'}")
print(f"Real-Time Monitor: {'✓' if MONITOR_AVAILABLE else '✗'}")
print("=" * 70)

# Crypto Symbol Mappings
CRYPTO_SYMBOL_MAP = {
    # Top 50 Cryptocurrencies by Market Cap
    'BTC': 'BTC-USD', 'BITCOIN': 'BTC-USD',
    'ETH': 'ETH-USD', 'ETHEREUM': 'ETH-USD',
    'BNB': 'BNB-USD', 'BINANCE': 'BNB-USD',
    'XRP': 'XRP-USD', 'RIPPLE': 'XRP-USD',
    'ADA': 'ADA-USD', 'CARDANO': 'ADA-USD',
    'SOL': 'SOL-USD', 'SOLANA': 'SOL-USD',
    'DOGE': 'DOGE-USD', 'DOGECOIN': 'DOGE-USD',
    'DOT': 'DOT-USD', 'POLKADOT': 'DOT-USD',
    'MATIC': 'MATIC-USD', 'POLYGON': 'MATIC-USD',
    'LTC': 'LTC-USD', 'LITECOIN': 'LTC-USD',
    'AVAX': 'AVAX-USD', 'AVALANCHE': 'AVAX-USD',
    'LINK': 'LINK-USD', 'CHAINLINK': 'LINK-USD',
    'UNI': 'UNI-USD', 'UNISWAP': 'UNI-USD',
    'ATOM': 'ATOM-USD', 'COSMOS': 'ATOM-USD',
    'XLM': 'XLM-USD', 'STELLAR': 'XLM-USD',
    'ALGO': 'ALGO-USD', 'ALGORAND': 'ALGO-USD',
    'VET': 'VET-USD', 'VECHAIN': 'VET-USD',
    'FIL': 'FIL-USD', 'FILECOIN': 'FIL-USD',
    'TRX': 'TRX-USD', 'TRON': 'TRX-USD',
    'ETC': 'ETC-USD', 'ETHEREUMCLASSIC': 'ETC-USD',
    'AAVE': 'AAVE-USD',
    'MKR': 'MKR-USD', 'MAKER': 'MKR-USD',
    'COMP': 'COMP-USD', 'COMPOUND': 'COMP-USD',
    'SUSHI': 'SUSHI-USD',
    'YFI': 'YFI-USD', 'YEARN': 'YFI-USD',
    'SNX': 'SNX-USD', 'SYNTHETIX': 'SNX-USD',
    'SHIB': 'SHIB-USD', 'SHIBA': 'SHIB-USD',
    'NEAR': 'NEAR-USD',
    'FLOW': 'FLOW-USD',
    'MANA': 'MANA-USD', 'DECENTRALAND': 'MANA-USD',
    'SAND': 'SAND-USD',
    'AXS': 'AXS-USD', 'AXIE': 'AXS-USD',
    'CHZ': 'CHZ-USD', 'CHILIZ': 'CHZ-USD',
    'ENJ': 'ENJ-USD', 'ENJIN': 'ENJ-USD',
    'BAT': 'BAT-USD',
    'ZRX': 'ZRX-USD',
    'LRC': 'LRC-USD', 'LOOPRING': 'LRC-USD',
    'IMX': 'IMX-USD',
    'APE': 'APE-USD', 'APECOIN': 'APE-USD',
    'OP': 'OP-USD', 'OPTIMISM': 'OP-USD',
    'ARB': 'ARB-USD', 'ARBITRUM': 'ARB-USD',
    'PEPE': 'PEPE-USD',
    'FLOKI': 'FLOKI-USD',
}

# Default symbols to always analyze (Most liquid and tradeable cryptos as of 2025)
# Removed: MATIC (became POL/delisted on some exchanges)
DEFAULT_SYMBOLS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'DOT']

# Crypto News Sources (Optimized for speed and reliability)
# Removed slow/unreliable sources, kept only high-quality feeds
CRYPTO_NEWS_SOURCES = [
    # Tier 1 - Major, reliable sources (fast and authoritative)
    ('CoinDesk', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
    ('Cointelegraph', 'https://cointelegraph.com/rss'),
    ('The Block', 'https://www.theblock.co/rss.xml'),
    ('Decrypt', 'https://decrypt.co/feed'),
    ('Bitcoin Magazine', 'https://bitcoinmagazine.com/feed'),
    
    # Tier 2 - Quality sources with good coverage
    ('CryptoSlate', 'https://cryptoslate.com/feed/'),
    ('BeInCrypto', 'https://beincrypto.com/feed/'),
    ('U.Today', 'https://u.today/rss'),
    ('NewsBTC', 'https://www.newsbtc.com/feed/'),
    ('Bitcoinist', 'https://bitcoinist.com/feed/'),
    
    # Tier 3 - Additional coverage for completeness
    ('CryptoPotato', 'https://cryptopotato.com/feed/'),
    ('CryptoNews', 'https://cryptonews.com/news/feed/'),
]

# ==================== ALL PARAMETERS NOW IN config.py ====================
# Risk Management, News Parameters, ML Config, etc. are imported from config.py
# This keeps the code clean and allows easy optimization

# Update ML_ENABLED based on actual availability
if not ML_AVAILABLE:
    ML_ENABLED = False

# ==================== UTILITY FUNCTIONS ====================

def send_telegram_message(message):
    """Send notification via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")

def fetch_rss_feed(url, timeout=10):
    """Fetch and parse RSS feed"""
    try:
        resp = requests.get(url, timeout=timeout, headers={'User-Agent': 'CryptoTrader/1.0'})
        items = []
        for block in re.findall(r'<item>(.*?)</item>', resp.text, re.S | re.I):
            title_m = re.search(r'<title>(.*?)</title>', block, re.S | re.I)
            desc_m = re.search(r'<description>(.*?)</description>', block, re.S | re.I)
            title = re.sub('<.*?>', '', title_m.group(1)).strip() if title_m else ''
            desc = re.sub('<.*?>', '', desc_m.group(1)).strip() if desc_m else ''
            if title or desc:
                items.append({'title': title, 'description': desc})
        return items
    except Exception as e:
        return []

def get_crypto_news():
    """Fetch cryptocurrency news or return demo placeholders if API key missing."""
    cutoff = datetime.now() - timedelta(hours=24)
    articles = []
    if NEWS_API_KEY and newsapi:
        try:
            query = 'cryptocurrency OR bitcoin OR ethereum OR crypto OR blockchain OR altcoin'
            resp = newsapi.get_everything(q=query, language='en', sort_by='publishedAt', page_size=100)
            for article in resp.get('articles', []):
                pub_date = article.get('publishedAt')
                if pub_date:
                    try:
                        pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        if pub_dt.replace(tzinfo=None) < cutoff:
                            continue
                    except:
                        pass
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'publishedAt': article.get('publishedAt', '')
                })
        except Exception as e:
            logger.warning(f"NewsAPI error: {e}")
    else:
        # Demo mode articles (static examples) - add more variety
        now = datetime.now().isoformat()
        articles = [
            {'title': 'Bitcoin institutional accumulation continues', 'description': 'Major funds increase BTC positions amid macro uncertainty', 'source': 'DEMO', 'publishedAt': now},
            {'title': 'Ethereum upgrade successful', 'description': 'Network efficiency improves, gas costs reduced significantly', 'source': 'DEMO', 'publishedAt': now},
            {'title': 'Solana ecosystem expands rapidly', 'description': 'New dApps launch, trading volume hits new highs', 'source': 'DEMO', 'publishedAt': now},
            {'title': 'XRP gains regulatory clarity', 'description': 'Court ruling provides positive outlook for cross-border payments', 'source': 'DEMO', 'publishedAt': now},
            {'title': 'Cardano development milestone reached', 'description': 'Smart contract upgrades roll out successfully', 'source': 'DEMO', 'publishedAt': now},
            {'title': 'BNB utility expands across chains', 'description': 'New partnerships announced for DeFi integration', 'source': 'DEMO', 'publishedAt': now},
            {'title': 'Avalanche sees increased developer activity', 'description': 'Subnet deployments surge as ecosystem grows', 'source': 'DEMO', 'publishedAt': now},
            {'title': 'Dogecoin merchant adoption rises', 'description': 'Payment integrations expand to major retailers', 'source': 'DEMO', 'publishedAt': now},
        ]
        print(f"[DEMO] Using {len(articles)} demo news articles")
    
    # RSS Feeds (only if not demo mode)
    if NEWS_API_KEY:
        for name, url in CRYPTO_NEWS_SOURCES:
            items = fetch_rss_feed(url)
            for item in items[:15]:  # Limit to 15 most recent per source
                articles.append({
                    'title': item['title'],
                    'description': item['description'],
                    'source': name,
                    'publishedAt': datetime.now().isoformat()
                })
    
    # Basic sorting (demo or real)
    articles = sort_articles_by_time(articles)
    print(f"Fetched {len(articles)} news articles ({'demo' if not NEWS_API_KEY else 'live'})")
    return articles

def extract_crypto_symbols(text):
    """Extract cryptocurrency symbols from text"""
    text_upper = text.upper()
    found = set()
    
    # Check all known symbols and aliases
    for symbol, yf_symbol in CRYPTO_SYMBOL_MAP.items():
        if re.search(r'\b' + re.escape(symbol) + r'\b', text_upper):
            found.add(yf_symbol)
    
    # Check for $SYMBOL patterns
    for match in re.findall(r'\$([A-Z]{2,6})\b', text_upper):
        if match in CRYPTO_SYMBOL_MAP:
            found.add(CRYPTO_SYMBOL_MAP[match])
    
    return list(found)

def analyze_sentiment_with_llm(articles, symbol=''):
    """
    Analyze sentiment using LLM7.io LLM ONLY (no fallback to rule-based sentiment)
    If LLM is unavailable, returns None to indicate no trade should be made
    """
    if not llm_client:
        print("[AI] No LLM client available - cannot generate signals")
        return None, "AI unavailable - no trade signals"
    
    if not articles:
        print("[AI] No articles provided - cannot generate signals")
        return None, "No articles available"
    
    # Get news cache
    news_cache = get_news_cache()
    
    # Filter articles: separate new from cached
    new_articles, cached_articles = news_cache.filter_new_articles(articles[:10])
    
    # If we have cached articles, use them
    if cached_articles:
        print(f"[CACHE] Using {len(cached_articles)} cached AI analyses (saving API calls)")
    
    # Check if we have ANY articles to work with
    if not new_articles and not cached_articles:
        print("[AI] No new or cached articles to analyze")
        return None, "No news articles available"
    
    # If ONLY cached articles and NO new articles, just use cached results
    if not new_articles and cached_articles:
        all_scores = [cached['sentiment_score'] for cached in cached_articles]
        all_reasons = [cached['reasoning'] for cached in cached_articles]
        avg_score = sum(all_scores) / len(all_scores)
        combined_reason = " | ".join(all_reasons[:3])
        return avg_score, combined_reason
    
    all_scores = []
    all_reasons = []
    
    # Add cached results
    for cached in cached_articles:
        all_scores.append(cached['sentiment_score'])
        all_reasons.append(cached['reasoning'])
    
    # Analyze new articles if any
    if new_articles:
        print(f"[AI] Analyzing {len(new_articles)} new articles with Multi-Provider LLM")
        
        # Prepare article summaries for NEW articles only
        article_texts = []
        for i, article in enumerate(new_articles, 1):
            title = article.get('title', '')
            desc = article.get('description', '')
            article_texts.append(f"{i}. {title}\n   {desc[:200]}")
        
        combined_text = "\n".join(article_texts)
        
        # Optimized prompt for better sentiment analysis with gpt-5o-mini/bidara
        prompt = f"""You are a cryptocurrency market analyst. Analyze these recent news articles about {symbol if symbol else 'the crypto market'}.

NEWS ARTICLES:
{combined_text}

TASK: Provide a precise sentiment analysis with clear reasoning.

SENTIMENT SCORE: Rate from -1.0 (very bearish) to +1.0 (very bullish)
- Consider: price movement catalysts, adoption news, regulatory impact, market sentiment
- Negative events (hacks, bans, crashes): -0.7 to -1.0
- Slightly negative: -0.3 to -0.6
- Neutral: -0.2 to +0.2
- Slightly positive: +0.3 to +0.6
- Very positive (major adoption, breakthroughs): +0.7 to +1.0

REASONING: Explain in 2-3 clear sentences why this score is appropriate.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
SCORE: [single number between -1.0 and 1.0]
REASON: [your 2-3 sentence explanation]"""
        
        try:
            # Use multi-provider LLM with automatic failover
            # Temperature 0.7 is built into the client (balanced between creativity and consistency)
            result = llm_client.chat(
                messages=[
                    {"role": "system", "content": "You are a cryptocurrency market sentiment analyzer. Analyze news and provide sentiment scores from -100 (very bearish) to +100 (very bullish)."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Check if result is None
            if result is None:
                print("[AI] No response from LLM - cannot generate signals")
                # Don't cache errors - return None to skip this symbol
                return None, "AI failed to respond"
            
            # Parse response
            score_match = re.search(r'SCORE:\s*([-+]?[0-9]*\.?[0-9]+)', result)
            reason_match = re.search(r'REASON:\s*(.+)', result, re.S)
            
            if not score_match:
                print("[AI] Could not parse AI response - cannot generate signals")
                print(f"[DEBUG] Response was: {result[:200]}")
                # Don't cache parse errors - return None to skip this symbol
                return None, "AI response parse error"
            
            score = float(score_match.group(1))
            reason = reason_match.group(1).strip() if reason_match else result
            
            # Clamp score
            score = max(-1.0, min(1.0, score))
            reason = reason[:200]
            
            # ONLY cache successful analysis (not errors)
            for article in new_articles:
                news_cache.add_analysis(article, score, reason)
            
            all_scores.append(score)
            all_reasons.append(reason)
        
        except Exception as e:
            error_msg = str(e)
            if '403' in error_msg or 'Forbidden' in error_msg:
                logger.error(f"AI API access denied - check rate limits: {e}")
            else:
                logger.error(f"AI analysis error: {e}")
            logger.warning("AI unavailable - cannot generate trade signals")
            # Don't cache errors - return None
            return None, "AI unavailable"
    
    # Combine all scores (cached + new)
    if all_scores:
        news_sentiment = sum(all_scores) / len(all_scores)
        combined_reason = " | ".join(all_reasons[:3])  # Top 3 reasons
        
        # Get social media sentiment
        try:
            social_monitor = SocialMediaMonitor()
            social_signals = social_monitor.get_all_social_signals()
            social_sentiment_data = aggregate_social_sentiment(social_signals)
            social_sentiment = social_sentiment_data['sentiment_score']
            
            print(f"[SOCIAL] News sentiment: {news_sentiment:.3f}, Social sentiment: {social_sentiment:.3f}")
            
            # Combine sentiments: 70% news, 30% social (as per system design)
            combined_sentiment = 0.7 * news_sentiment + 0.3 * social_sentiment
            
            # Update reasoning to include social sentiment
            social_reason = f"Social sentiment: {social_sentiment:.3f} (F&G: {social_sentiment_data.get('fear_greed_index', 'N/A')})"
            combined_reason = f"{combined_reason} | {social_reason}"
            
            return combined_sentiment, combined_reason
            
        except Exception as e:
            print(f"[SOCIAL] Error getting social sentiment: {e}")
            print("[SOCIAL] Falling back to news-only sentiment")
            # Fall back to news-only sentiment if social fails
            return news_sentiment, combined_reason
    
    # Should not reach here, but handle edge case
    print("[AI] No AI analysis results available")
    return None, "No AI analysis available"

@lru_cache(maxsize=200)
def get_market_data(symbol, period='30d', interval='1h'):
    """
    Fetch market data and calculate candlestick pattern analysis
    Optimized for 2-hour trading timeframe:
    - 1h candles: Yahoo Finance doesn't support 2h, using 1h for short-term pattern detection
    - 30 days history: ~720 candles for reliable pattern analysis
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty or len(df) < 50:  # Need at least 50 candles for patterns
            return None
        
        close = df['Close']
        current_price = float(close.iloc[-1])
        
        # Calculate volatility (annualized for 1h candles)
        returns = close.pct_change()
        # 1h candles = 24 periods per day, 365 days
        volatility = float(returns.std() * np.sqrt(24 * 365))
        
        # Get candlestick pattern analysis (FREE, no API calls)
        indicators = get_all_candlestick_indicators(df)
        
        # Extract ATR percentage for stop loss calculations
        atr_pct = indicators['atr']['percent']
        
        return {
            'price': current_price,
            'volatility': volatility,
            'atr_pct': atr_pct,
            'indicators': indicators
        }
    
    except Exception as e:
        print(f"Market data error for {symbol}: {e}")
        return None

def calculate_trade_signal(sentiment_score, news_count, market_data, symbol='', news_articles=None):
    """
    Enhanced trading signal calculation using:
    1. News sentiment analysis (PRIMARY - 85-90%)
    2. LLM reasoning (PRIMARY - adaptive, qualitative)
    3. Candlestick patterns (FILTER ONLY - 10-15% + execution levels)
    
    Candlestick patterns are used to:
    - Filter out bad setups (contradiction check)
    - Calculate entry price, stop loss, take profit
    - Determine optimal leverage
    """
    if not market_data:
        return None
    
    price = market_data['price']
    indicators = market_data['indicators']
    # Get adaptive parameters (single retrieval)
    adaptive_params = market_analyzer.get_adjusted_parameters() if market_analyzer else {
        'expected_return_per_sentiment': EXPECTED_RETURN_PER_SENTIMENT,
        'news_impact_multiplier': NEWS_IMPACT_MULTIPLIER,
        'max_news_bonus': MAX_NEWS_BONUS,
        'confidence_threshold': 0.3,
        'risk_multiplier': 1.0,
        'dynamic_max_leverage': MAX_LEVERAGE_CRYPTO
    }

    dynamic_expected = adaptive_params.get('expected_return_per_sentiment', EXPECTED_RETURN_PER_SENTIMENT)
    expected_return = sentiment_score * dynamic_expected

    # News volume bonus (adaptive)
    dynamic_news_mult = adaptive_params.get('news_impact_multiplier', NEWS_IMPACT_MULTIPLIER)
    dynamic_news_cap = adaptive_params.get('max_news_bonus', MAX_NEWS_BONUS)
    news_bonus = min(news_count * dynamic_news_mult, dynamic_news_cap)
    expected_return += news_bonus if sentiment_score > 0 else -news_bonus
    
    # Candlestick pattern score (weighted combination with dynamic optimization)
    tech_score = 0
    total_weight = 0
    
    for indicator, weight in INDICATOR_WEIGHTS.items():
        if indicator in indicators and 'signal' in indicators[indicator]:
            # Apply dynamic weight multiplier from learning system
            weight_multiplier = market_analyzer.get_indicator_weight_multiplier(indicator) if market_analyzer else 1.0
            adjusted_weight = weight * weight_multiplier
            
            tech_score += indicators[indicator]['signal'] * adjusted_weight
            total_weight += adjusted_weight
    
    tech_score_normalized = tech_score / total_weight if total_weight > 0 else 0
    
    # Get LLM analysis if available
    llm_analysis = None
    if market_analyzer and news_articles:
        sentiment_data = {'score': sentiment_score, 'count': news_count}
        llm_analysis = market_analyzer.analyze_with_llm(
            symbol, market_data, sentiment_data, news_articles
        )
    
    # Combine all analyses
    combined = market_analyzer.combine_analyses(
        tech_score_normalized, 
        sentiment_score, 
        llm_analysis
    ) if market_analyzer else {
        'final_score': (sentiment_score + tech_score_normalized) / 2,
        'confidence': abs((sentiment_score + tech_score_normalized) / 2),
        'method': 'basic'
    }
    
    # Check confidence threshold (adaptive)
    if combined['confidence'] < adaptive_params['confidence_threshold']:
        return None
    
    # Determine direction
    direction = combined['direction']
    if direction == 'NEUTRAL':
        return None
    
    # Adjust expected return based on LLM if available
    if llm_analysis and llm_analysis.get('llm_available'):
        # LLM provides additional context
        expected_return *= (1 + abs(tech_score_normalized) * BASE_TECH_RETURN_MULT)
        if combined.get('agreement_boost'):
            expected_return *= (1 + BASE_TECH_RETURN_MULT)  # Boost when all methods agree
    else:
        expected_return *= (1 + abs(tech_score_normalized) * BASE_TECH_RETURN_MULT)
    
    # Calculate stop loss with adaptive risk (optimized for 2h SHORT-TERM trades)
    # Use ATR as primary method with reasonable bounds for short-term trading
    atr_stop = market_data['atr_pct'] * ATR_STOP_MULTIPLIER
    
    # Ensure stop loss is tight for short-term trades
    # For 2h crypto trades: 0.8% min, 2.5% max
    stop_pct = max(MIN_STOP_PCT, min(atr_stop, MAX_STOP_PCT))
    
    # Apply adaptive risk adjustment from learning system
    stop_pct *= adaptive_params['risk_multiplier']
    
    # NEW: Apply SL adjustment from learning system
    # If SL is hit too often, widen it. If rarely hit, can tighten it.
    sl_adjustment = adaptive_params.get('sl_adjustment_factor', 1.0)
    stop_pct *= sl_adjustment
    
    # Final validation: ensure stop is within acceptable range for SHORT-TERM trades
    stop_pct = max(MIN_STOP_PCT, min(stop_pct, MAX_STOP_PCT))
    
    # Calculate take profit - TARGET 1:3 MINIMUM R/R (can be higher for strong signals)
    # Expected profit is driven by news/sentiment (PRIMARY signal source)
    expected_profit = abs(expected_return)
    
    # NEW: Apply TP adjustment factor from learning system
    # If system learned that TPs are too far, reduce them
    tp_adjustment = adaptive_params.get('tp_adjustment_factor', 1.0)
    expected_profit *= tp_adjustment
    
    # Consider recent actual price movements (use ATR as proxy for realistic movement)
    # For 2h timeframe, typical movements are 1-3x ATR
    realistic_movement = market_data['atr_pct'] * REALISTIC_MOVEMENT_ATR_MULT
    if expected_profit > realistic_movement * TP_REALISTIC_CAP_MULT:
        expected_profit = realistic_movement * TP_REALISTIC_CAP_MULT
    
    min_profit_for_target_rr = stop_pct * TARGET_RR_RATIO  # 1:3 minimum
    
    # Ensure we meet MINIMUM R/R ratio (but allow higher if signal is strong)
    if expected_profit < min_profit_for_target_rr:
        expected_profit = min_profit_for_target_rr  # Enforce 1:3 minimum only if below
    
    # Cap maximum take profit to be realistic for 2h SHORT-TERM trades
    # Max 5% BUT must respect minimum R/R ratio
    # If stop loss is high (e.g., 2.5%), we need higher TP to maintain 3:1 R/R (7.5%)
    # Strong signals can aim for higher R/R (4:1, 5:1, even 6:1)
    max_tp_cap = max(TP_CAP_BASE, min_profit_for_target_rr)
    expected_profit = min(expected_profit, max_tp_cap)
    
    # Risk/Reward ratio (will be >= 3:1, can be much higher)
    rr_ratio = expected_profit / stop_pct if stop_pct > 0 else 0

    # Unified bounds enforcement (final pass before probability blending)
    stop_pct, expected_profit, rr_ratio = apply_trade_bounds(stop_pct, expected_profit)

    # Predictor-based probability (local ML or AI fallback)
    if probability_predictor and combined.get('ml_probability') is None:
        prelim_signal = {
            'sentiment_score': sentiment_score,
            'technical_score': tech_score_normalized,
            'confidence': combined['confidence'],
            'rr_ratio': rr_ratio,
            'stop_pct': stop_pct,
            'expected_profit_pct': expected_profit,
            'leverage': 0
        }
        ml_prob = probability_predictor.get_probability(prelim_signal)
        if ml_prob is not None:
            combined['ml_probability'] = ml_prob
            combined['confidence'] = (combined['confidence'] * ML_CONF_BLEND_HEURISTIC_WEIGHT) + (ml_prob * ML_CONF_BLEND_MODEL_WEIGHT)
            if ml_prob < ML_MIN_CONFIDENCE:
                return None
    
    # Skip trades that don't meet minimum R/R (should rarely happen after apply_trade_bounds)
    if rr_ratio < TARGET_RR_RATIO:
        return None
    
    # Leverage recommendation - Optimized for 2h timeframe
    # Formula: Use R/R ratio + confidence to determine leverage
    confidence_factor = combined['confidence']  # 0 to 1
    
    # Base leverage from R/R: Higher R/R = can use more leverage
    base_leverage = min(
        math.floor(rr_ratio + (confidence_factor * 5)),  # Add up to 5x based on confidence
        adaptive_params.get('dynamic_max_leverage', MAX_LEVERAGE_CRYPTO)
    )
    
    # Reduce if LLM flags high risk
    if llm_analysis and llm_analysis.get('risk') == 'HIGH':
        base_leverage = max(2, base_leverage // 2)  # Halve but minimum 2x
    
    leverage = max(2, base_leverage)  # Minimum 2x leverage (2h timeframe allows this)

    # Final leverage modulation by ML probability if present
    if probability_predictor and combined.get('ml_probability') is not None:
        ml_prob_final = combined['ml_probability']
        if ml_prob_final < 0.5:
            leverage = max(2, math.floor(leverage * ML_LEVERAGE_LOW_PROB_FACTOR))
        elif ml_prob_final > 0.7:
            leverage = min(adaptive_params.get('dynamic_max_leverage', MAX_LEVERAGE_CRYPTO), leverage + ML_LEVERAGE_HIGH_PROB_INCREMENT)
    
    # NEW: Apply entry adjustment from learning system
    # If entries not being reached, move entry closer to current price
    entry_adjustment = adaptive_params.get('entry_adjustment_factor', 1.0)
    
    # Calculate prices with entry adjustment
    # Entry adjustment < 1.0 means move entry closer to current price
    # Entry adjustment = 1.0 means use current price as entry (no adjustment needed for limit orders)
    # For market orders, we use current price. For limit orders, we'd adjust based on support/resistance
    # Since we're using current price as entry, we document this for future enhancement
    entry_price = price  # Using current market price as entry
    
    if direction == 'LONG':
        stop_loss = entry_price * (1 - stop_pct)
        take_profit = entry_price * (1 + expected_profit)
    else:
        stop_loss = entry_price * (1 + stop_pct)
        take_profit = entry_price * (1 - expected_profit)
    
    return {
        'direction': direction,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'stop_pct': stop_pct,
        'expected_profit_pct': expected_profit,
        'rr_ratio': rr_ratio,
        'leverage': leverage,
        'sentiment_score': sentiment_score,
        'technical_score': tech_score_normalized,
        'combined_score': combined['final_score'],
        'confidence': combined['confidence'],
        'method': combined.get('method', 'basic'),
        'llm_reasoning': combined.get('llm_reasoning', ''),
        'llm_risk': combined.get('llm_risk', 'UNKNOWN'),
        'adaptive_threshold': adaptive_params['confidence_threshold'],
        'tp_adjustment': tp_adjustment  # Store for learning
    }

def log_trade(symbol, signal, sentiment_reason='', indicators_data=None):
    """Log trade to file with indicator signals for learning"""
    if not signal:
        return
    
    trade_entry = {
        'timestamp': datetime.now(pytz.UTC).isoformat(),
        'symbol': symbol,
        'direction': signal['direction'],
        'entry_price': signal['entry_price'],
        'stop_loss': signal['stop_loss'],
        'take_profit': signal['take_profit'],
        'leverage': signal['leverage'],
        'rr_ratio': signal['rr_ratio'],
        'confidence': signal['confidence'],
        'sentiment_score': signal['sentiment_score'],
        'technical_score': signal['technical_score'],
        'sentiment_reason': sentiment_reason,
        'status': 'open',
        'check_time': (datetime.now(pytz.UTC) + timedelta(hours=2)).isoformat(),  # 2h trade duration
        'indicators': indicators_data  # Store for learning
    }
    
    # Load existing logs
    try:
        with open(TRADE_LOG_FILE, 'r') as f:
            logs = json.load(f)
    except:
        logs = []
    
    logs.append(trade_entry)
    
    # Save logs
    with open(TRADE_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def check_daily_risk():
    """Check if daily risk limit has been reached"""
    try:
        with open(DAILY_RISK_FILE, 'r') as f:
            risk_data = json.load(f)
            today = datetime.now().date().isoformat()
            if risk_data.get('date') == today:
                    adaptive_limit = None
                    try:
                        if market_analyzer:
                            adaptive_limit = market_analyzer.get_adjusted_parameters().get('daily_risk_limit')
                    except Exception:
                        adaptive_limit = None
                    limit_to_use = adaptive_limit if adaptive_limit is not None else DAILY_RISK_LIMIT
                    return risk_data.get('loss_pct', 0) >= limit_to_use
    except:
        pass
    return False

def get_current_price_robust(symbol):
    """
    Get current price using multiple fallback sources
    Priority: Yahoo Finance -> CoinGecko API -> Return None
    """
    # First try Yahoo Finance
    try:
        yf_symbol = CRYPTO_SYMBOL_MAP.get(symbol, f"{symbol}-USD")
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(period='1d', interval='1h')
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception:
        pass
    
    # Fallback to CoinGecko API (free, no auth required)
    try:
        # Map symbol to CoinGecko ID
        coingecko_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'BNB': 'binancecoin',
            'ADA': 'cardano',
            'XRP': 'ripple',
            'SOL': 'solana',
            'DOT': 'polkadot',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'LTC': 'litecoin',
            'MATIC': 'matic-network',
            'SHIB': 'shiba-inu',
            'FLOW': 'flow',
            'NEAR': 'near'
        }
        
        cg_id = coingecko_ids.get(symbol.upper())
        if cg_id:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if cg_id in data and 'usd' in data[cg_id]:
                    return float(data[cg_id]['usd'])
    except Exception:
        pass
    
    return None

def check_trade_outcomes():
    """
    Check open trades and verify if predictions were correct
    Updates learning system with actual outcomes
    
    NOW ENHANCED WITH SMART QUEUING:
    - Checks trades at 2h intervals (when script runs)
    - If entry NOT reached yet → keep in queue
    - If entry reached but no TP/SL hit yet → keep in queue
    - ONLY trains on completed trades (TP or SL hit)
    - Maximum 2h wait time before final check
    """
    print("[DEBUG] Starting trade outcome check...")
    try:
        with open(TRADE_LOG_FILE, 'r') as f:
            logs = json.load(f)
        print(f"[DEBUG] Loaded {len(logs)} trades from log file")
    except FileNotFoundError:
        print(f"[DEBUG] No trade log file found at {TRADE_LOG_FILE}")
        return
    except Exception as e:
        print(f"[DEBUG] Error loading trade log: {e}")
        return
    
    now = datetime.now(pytz.UTC)
    updated = False
    verified_count = 0
    queued_count = 0
    
    for trade in logs:
        if trade.get('status') not in ['open', 'queued']:
            continue
        
        # Get entry time and check time
        if 'check_time' not in trade or 'timestamp' not in trade:
            continue
        
        entry_time = datetime.fromisoformat(trade['timestamp'])
        max_check_time = datetime.fromisoformat(trade['check_time'])
        
        # Calculate how long the trade has been running
        time_elapsed = (now - entry_time).total_seconds() / 3600  # hours
        
        # Don't check too early (wait at least 2 hours)
        if time_elapsed < 2.0:
            continue
        
        # Fetch INTRADAY price history to track actual movements
        symbol = trade['symbol']
        yf_symbol = CRYPTO_SYMBOL_MAP.get(symbol, f"{symbol}-USD")
        
        try:
            ticker = yf.Ticker(yf_symbol)
            # Fetch 5 days of 1h data to ensure we have the entry time window
            intraday_data = ticker.history(period='5d', interval='1h')
            
            if intraday_data.empty:
                # Yahoo Finance failed, try robust price fetching
                current_price = get_current_price_robust(symbol)
                if current_price is None:
                    continue  # Skip this trade if no price data available
                # For fallback, assume entry was reached and use current price for high/low
                entry_reached = True
                high_price = current_price
                low_price = current_price
                trade_window = None  # No historical data available
            else:
                # Get the time window for the trade (from entry time to now)
                trade_window = intraday_data[
                    (intraday_data.index >= entry_time) & 
                    (intraday_data.index <= now)
                ]
                
                if trade_window.empty:
                    # Fallback to single point check if no intraday data
                    current_data = ticker.history(period='1d', interval='1h')
                    if current_data.empty:
                        # Try robust fetching as last resort
                        current_price = get_current_price_robust(symbol)
                        if current_price is None:
                            continue
                        entry_reached = True
                        high_price = current_price
                        low_price = current_price
                        trade_window = None
                    else:
                        current_price = float(current_data['Close'].iloc[-1])
                        entry_reached = True  # Assume entry reached if no data
                        high_price = current_price
                        low_price = current_price
                        trade_window = None
                else:
                    current_price = float(trade_window['Close'].iloc[-1])
                    high_price = float(trade_window['High'].max())
                    low_price = float(trade_window['Low'].min())
                    
                    # Check if entry price was actually reached
                    entry_price = trade['entry_price']
                    direction = trade['direction']
                    
                    if direction == 'LONG':
                        # For LONG, entry needs to be reached from above (price needs to dip to/below entry)
                        entry_reached = low_price <= entry_price
                    else:  # SHORT
                        # For SHORT, entry needs to be reached from below (price needs to rise to/above entry)
                        entry_reached = high_price >= entry_price
            
            entry_price = trade['entry_price']
            direction = trade['direction']
            stop_loss = trade['stop_loss']
            take_profit = trade['take_profit']
            
            # SMART QUEUING SYSTEM:
            # 1. If entry NOT reached yet
            if not entry_reached:
                # Check if max time (2h) has elapsed
                if time_elapsed >= 2.0:
                    # Max time reached, entry never filled
                    trade['status'] = 'entry_not_reached'
                    trade['exit_price'] = current_price
                    trade['actual_profit'] = 0
                    trade['verified_at'] = now.isoformat()
                    trade['failure_reason'] = 'entry_not_reached'
                    trade['high_price'] = high_price
                    trade['low_price'] = low_price
                    
                    # Feed to learning system
                    if market_analyzer and trade.get('indicators'):
                        trade_result = {
                            'profit': 0,
                            'indicators': trade['indicators'],
                            'symbol': symbol,
                            'direction': direction,
                            'confidence': trade.get('confidence', 0),
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'entry_reached': False,
                            'failure_reason': 'entry_not_reached',
                            'high_price': high_price,
                            'low_price': low_price,
                            'tp_distance': 0,
                            'actual_movement': 0,
                            'hit_tp': False,
                            'hit_sl': False
                        }
                        market_analyzer.learn_from_trade(trade_result)
                    
                    verified_count += 1
                    updated = True
                else:
                    # Still waiting for entry, keep in queue
                    trade['status'] = 'queued'
                    trade['last_check'] = now.isoformat()
                    queued_count += 1
                    updated = True
                
                continue
            
            # 2. Entry WAS reached - check if SL or TP were hit during the window
            if direction == 'LONG':
                sl_hit_during_window = low_price <= stop_loss
                tp_hit_during_window = high_price >= take_profit
            else:  # SHORT
                sl_hit_during_window = high_price >= stop_loss
                tp_hit_during_window = low_price <= take_profit
            
            # 3. Check if trade is COMPLETED (TP or SL hit)
            trade_completed = sl_hit_during_window or tp_hit_during_window
            
            if not trade_completed:
                # Entry reached but trade still in progress
                if time_elapsed >= 2.0:
                    # Max time reached (2h), close at current price
                    if direction == 'LONG':
                        price_change = (current_price - entry_price) / entry_price
                    else:  # SHORT
                        price_change = (entry_price - current_price) / entry_price
                    
                    actual_profit = price_change * trade.get('leverage', 1)
                    trade['status'] = 'checked'
                    trade['exit_price'] = current_price
                    
                    # Determine failure reason if losing
                    if actual_profit < 0:
                        failure_reason = 'wrong_direction'
                    else:
                        failure_reason = 'tp_not_reached'
                    
                    trade['actual_profit'] = actual_profit
                    trade['verified_at'] = now.isoformat()
                    trade['failure_reason'] = failure_reason
                    trade['high_price'] = high_price
                    trade['low_price'] = low_price
                    trade['entry_reached'] = True
                    
                    # Train on this partial result
                    should_train = True
                else:
                    # Still in progress, keep in queue
                    trade['status'] = 'queued'
                    trade['last_check'] = now.isoformat()
                    queued_count += 1
                    updated = True
                    continue
            else:
                # Trade COMPLETED - calculate final result
                should_train = True
                
                if sl_hit_during_window:
                    # Stop loss was hit
                    actual_profit = -(abs(stop_loss - entry_price) / entry_price) * trade.get('leverage', 1)
                    if direction == 'SHORT':
                        actual_profit = -actual_profit
                    trade['status'] = 'stopped'
                    trade['exit_price'] = stop_loss
                    failure_reason = 'sl_hit'
                elif tp_hit_during_window:
                    # Take profit was hit
                    actual_profit = (abs(take_profit - entry_price) / entry_price) * trade.get('leverage', 1)
                    if direction == 'SHORT':
                        actual_profit = -actual_profit
                    trade['status'] = 'completed'
                    trade['exit_price'] = take_profit
                    failure_reason = None  # Success!
            
            # Only proceed with training if trade is completed or max time reached
            if should_train:
                trade['actual_profit'] = actual_profit
                trade['verified_at'] = now.isoformat()
                trade['failure_reason'] = failure_reason
                trade['high_price'] = high_price
                trade['low_price'] = low_price
                trade['entry_reached'] = True
                
                # Calculate precision metrics for learning
                # Enhanced: Track TP distance vs actual movement, including high/low reached
                tp_price = take_profit
                if direction == 'LONG':
                    tp_distance = (tp_price - entry_price) / entry_price
                    actual_movement = (current_price - entry_price) / entry_price
                    max_favorable_move = (high_price - entry_price) / entry_price
                else:  # SHORT
                    tp_distance = (entry_price - tp_price) / entry_price
                    actual_movement = (entry_price - current_price) / entry_price
                    max_favorable_move = (entry_price - low_price) / entry_price
                
                # Feed to learning system with enhanced precision data
                if market_analyzer and trade.get('indicators'):
                    trade_result = {
                        'profit': actual_profit,
                        'indicators': trade['indicators'],
                        'symbol': symbol,
                        'direction': direction,
                        'confidence': trade.get('confidence', 0),
                        'entry_price': entry_price,
                        'exit_price': trade['exit_price'],
                        # Enhanced precision tracking
                        'entry_reached': True,
                        'tp_distance': tp_distance,  # How far TP was set
                        'actual_movement': actual_movement,  # How far price moved at check time
                        'max_favorable_move': max_favorable_move,  # Best price reached in our direction
                    'hit_tp': tp_hit_during_window,  # Did it reach TP during window?
                    'hit_sl': sl_hit_during_window,  # Did it hit SL during window?
                    'failure_reason': failure_reason,  # Why did it fail (if it did)?
                    'high_price': high_price,
                    'low_price': low_price
                }
                market_analyzer.learn_from_trade(trade_result)
            
            verified_count += 1
            updated = True
            
        except Exception as e:
            print(f"Error verifying {symbol}: {e}")
            continue
    
    # Save updated logs
    if updated:
        with open(TRADE_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
        
        if verified_count > 0:
            print(f"\n[OK] Verified {verified_count} trade outcomes and updated learning system")
        if queued_count > 0:
            print(f"[⏳] {queued_count} trades still in queue (waiting for entry or completion)")
        if verified_count > 0 or queued_count > 0:
            print()

def format_trade_message(symbol, signal, sentiment_reason='', signal_number=None):
    """Format trade signal for output - NEWS-DRIVEN system (compact and beautiful)"""
    
    # Direction emoji
    direction_emoji = '📈' if signal['direction'] == 'LONG' else '📉'
    direction_text = 'LONG (BUY)' if signal['direction'] == 'LONG' else 'SHORT (SELL)'
    
    # R/R quality indicator
    if signal['rr_ratio'] >= 5:
        rr_quality = '🔥 EXCELLENT'
    elif signal['rr_ratio'] >= 3:
        rr_quality = '✨ GREAT'
    else:
        rr_quality = '✅ GOOD'
    
    # Confidence emoji
    confidence_emoji = '✅' if signal['confidence'] >= 0.7 else '🎯'
    
    # Smart formatting: Add more decimals if values look the same after rounding
    def smart_format_price(price, reference_prices=None):
        """Format price with enough decimals to show distinction"""
        # Start with 6 decimals
        for decimals in [6, 8, 10, 12]:
            formatted = f"{price:.{decimals}f}".rstrip('0').rstrip('.')
            
            # If we have reference prices, check if this formatted value is distinct
            if reference_prices:
                # Format reference prices with same decimals
                ref_formatted = [f"{ref:.{decimals}f}".rstrip('0').rstrip('.') for ref in reference_prices]
                # If current price is distinct from all references, we're good
                if formatted not in ref_formatted:
                    return formatted
            else:
                return formatted
        
        # Fallback: 12 decimals max
        return f"{price:.12f}".rstrip('0').rstrip('.')
    
    # Format with smart precision
    entry_price = signal['entry_price']
    stop_loss = signal['stop_loss']
    take_profit = signal['take_profit']
    
    # Format entry first
    entry = smart_format_price(entry_price)
    
    # Format SL ensuring it's different from entry
    stop_loss_str = smart_format_price(stop_loss, [entry_price])
    
    # Format TP ensuring it's different from both entry and SL
    take_profit_str = smart_format_price(take_profit, [entry_price, stop_loss])
    
    # Build message with signal number if provided
    signal_header = f"Signal #{signal_number}" if signal_number else "Signal"
    
    # Format for telegram with individual values copyable (without $ sign)
    msg = f"""{signal_header}
━━━━━━━━━━━━━━━━━━━━
{direction_emoji} {symbol} - {direction_text}
━━━━━━━━━━━━━━━━━━━━

Entry: `{entry}`
Stop Loss: `{stop_loss_str}` ({signal['stop_pct']*100:.2f}%)
Take Profit: `{take_profit_str}` ({signal['expected_profit_pct']*100:.2f}%)
Leverage: {signal['leverage']}x
R/R: 1:{signal['rr_ratio']:.1f} {rr_quality}

{confidence_emoji} Confidence: {signal['confidence']*100:.1f}%
📰 News: {signal['sentiment_score']:.2f}
📈 Technical: {signal['technical_score']:.2f}"""

    # Append ML probability or pending status
    try:
        if 'ml_probability' in signal and signal['ml_probability'] is not None:
            msg += f"\n🧪 ML Prob: {signal['ml_probability']*100:.1f}%"
        elif probability_predictor:
            pending_info = probability_predictor.get_pending_status()
            if pending_info:
                msg += f"\n🧪 ML/AI: {pending_info}"
    except Exception:
        pass
    
    return msg

# ==================== MAIN EXECUTION ====================

def display_learning_status():
    """Display comprehensive learning system status for cron visibility"""
    if not market_analyzer:
        return
    
    try:
        params = market_analyzer.get_adjusted_parameters()
        metrics = market_analyzer.precision_metrics
        
        print("\n" + "=" * 70)
        print("📚 LEARNING SYSTEM STATUS")
        print("=" * 70)
        
        # Trade counts
        total_trades = metrics.get('total_trades', 0)
        print(f"[TRADES] Total Verified: {total_trades}/20 (next optimization at 20)")
        
        # Check pending trades
        try:
            with open(TRADE_LOG_FILE, 'r') as f:
                logs = json.load(f)
            open_trades = len([t for t in logs if t.get('status') in ['open', 'queued']])
            completed_trades = len([t for t in logs if t.get('status') not in ['open', 'queued']])
            print(f"[TRADES] Pending: {open_trades} | Completed: {completed_trades}")
        except FileNotFoundError:
            # Expected if no trades logged yet
            pass
        except json.JSONDecodeError as e:
            # Trade log file is corrupted
            logger.warning(f"Trade log file corrupted, skipping pending trades display: {e}")
        except Exception as e:
            logger.debug(f"Could not read trade log: {e}")
        
        # Consecutive no-signals tracking
        no_signals_streak = metrics.get('consecutive_no_signals', 0)
        max_no_signals = metrics.get('max_consecutive_no_signals', 0)
        if no_signals_streak > 0:
            print(f"[ALERT] No-Signals Streak: {no_signals_streak} (triggers at 2, max was {max_no_signals})")
        else:
            print(f"[STATUS] No-Signals Streak: {no_signals_streak} (OK)")
        
        # Current adaptive parameters
        print(f"\n[ADAPTIVE] Current Parameters:")
        print(f"  • Confidence Threshold: {params.get('confidence_threshold', 0.3):.2f}")
        print(f"  • Entry Adjustment: {params.get('entry_adjustment_factor', 1.0):.2f}x")
        print(f"  • Stop Loss Adjustment: {params.get('sl_adjustment_factor', 1.0):.2f}x")
        print(f"  • Take Profit Adjustment: {params.get('tp_adjustment_factor', 1.0):.2f}x")
        
        # Win rate if available
        if total_trades >= 5 and hasattr(market_analyzer, 'performance_history'):
            recent = market_analyzer.performance_history[-20:]
            if recent:
                wins = sum(1 for t in recent if t['result'].get('profit', 0) > 0)
                win_rate = wins / len(recent)
                print(f"\n[PERFORMANCE] Recent Win Rate: {win_rate*100:.1f}%")
        
        print("=" * 70 + "\n")
    except Exception as e:
        logger.debug(f"Could not display learning status: {e}")

def main():
    """Main trading loop - NEWS-DRIVEN SHORT-TERM trading system (85-90% news/AI)"""
    print("\n[*] Starting Crypto Trading Signal Generator...")
    print("[NEWS] NEWS-DRIVEN TRADING SYSTEM (85-90% NEWS/AI)")
    print("=" * 70)
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"[MODE] Mode: {'Low Money' if LOW_MONEY_MODE else 'Standard'}")
    print(f"[DURATION] Trade Duration: 2 Hours (SHORT-TERM)")
    print(f"[TARGET] Strategy: News/AI Primary (85-90%) + Candlestick Analysis (10-15%)")
    print(f"[ANALYSIS] Candlestick Patterns: FREE (TA-Lib, no API calls)")
    try:
        dyn_lev = market_analyzer.get_adjusted_parameters().get('dynamic_max_leverage', MAX_LEVERAGE_CRYPTO) if market_analyzer else MAX_LEVERAGE_CRYPTO
    except Exception:
        dyn_lev = MAX_LEVERAGE_CRYPTO
    print(f"[LEVERAGE] Max Leverage: {dyn_lev}x (adaptive cap)")
    print(f"[RR] Min R/R: 1:{TARGET_RR_RATIO} (can be higher for strong signals)")
    print(f"[RISK] Stop Loss: {MIN_STOP_PCT*100:.1f}%-{MAX_STOP_PCT*100:.1f}%, Take Profit: up to {MAX_TP_PCT*100:.1f}%")
    
    # Show news cache stats
    news_cache = get_news_cache()
    cache_stats = news_cache.get_stats()
    print(f"[CACHE] News Cache: {cache_stats['total_cached']} analyzed, resets in {cache_stats['will_reset_in_hours']:.1f}h")
    print("=" * 70)
    print()
    
    # Display learning system status (NEW - for cron visibility)
    display_learning_status()
    
    # Check and verify outcomes of previous trades
    print("[CHECK] Checking previous trade outcomes...")
    check_trade_outcomes()
    
    # Check daily risk limit
    if check_daily_risk():
        msg = "[WARNING] Daily risk limit reached. No new trades today."
        print(msg)
        send_telegram_message(msg)
        return
    
    # Fetch news
    print("[NEWS] Fetching crypto news...")
    articles = get_crypto_news()

    if not articles:
        print("[WARNING] No news articles found")
        return

    print(f"[NEWS] Found {len(articles)} articles")

    # Extract symbols from news
    symbol_articles = {}
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        symbols = extract_crypto_symbols(text)

        for symbol in symbols:
            if symbol not in symbol_articles:
                symbol_articles[symbol] = []
            symbol_articles[symbol].append(article)

    print(f"[NEWS] Extracted symbols from news: {list(symbol_articles.keys())}")

    # Add default symbols
    for sym in DEFAULT_SYMBOLS:
        yf_symbol = CRYPTO_SYMBOL_MAP.get(sym, f"{sym}-USD")
        if yf_symbol not in symbol_articles:
            symbol_articles[yf_symbol] = articles[:5]  # Use general news

    print(f"[ANALYZE] Analyzing {len(symbol_articles)} cryptocurrencies: {list(symbol_articles.keys())}\n")
    
    # Analyze symbols in parallel for better performance
    signals = analyze_multiple_symbols_parallel(
        symbol_articles=symbol_articles,
        get_market_data_func=get_market_data,
        analyze_sentiment_func=analyze_sentiment_with_llm,
        calculate_signal_func=calculate_trade_signal,
        max_workers=8  # Use 8 parallel workers for optimal performance
    )

    print(f"\n[PARALLEL] Analysis complete. Found {len(signals)} signals.")

    # Debug: Show signal details
    if signals:
        print("[DEBUG] Signal details:")
        for i, item in enumerate(signals[:3]):  # Show first 3 signals
            signal = item['signal']
            print(f"  {i+1}. {item['symbol']}: confidence={signal.get('confidence', 0):.3f}, direction={signal.get('direction', 'N/A')}")
    else:
        print("[DEBUG] No signals generated. Checking why...")
        # Test one symbol manually
        test_symbol = list(symbol_articles.keys())[0] if symbol_articles else "BTC-USD"
        print(f"[DEBUG] Testing {test_symbol} manually...")

        try:
            market_data = get_market_data(test_symbol)
            if market_data:
                print(f"[DEBUG] Market data OK for {test_symbol}: ${market_data['price']:.2f}")
                articles_for_symbol = symbol_articles.get(test_symbol, [])
                if articles_for_symbol:
                    sentiment_result = analyze_sentiment_with_llm(articles_for_symbol)
                    if sentiment_result:
                        sentiment_score, sentiment_reason = sentiment_result
                        print(f"[DEBUG] Sentiment OK: {sentiment_score:.3f}")
                        test_signal = calculate_trade_signal(sentiment_score, len(articles_for_symbol), market_data, test_symbol)
                        if test_signal:
                            print(f"[DEBUG] Signal generated: {test_signal['direction']} with confidence {test_signal['confidence']:.3f}")
                        else:
                            print("[DEBUG] calculate_trade_signal returned None")
                    else:
                        print(f"[DEBUG] Sentiment analysis failed for {test_symbol}")
                else:
                    print(f"[DEBUG] No articles for {test_symbol}")
            else:
                print(f"[DEBUG] Market data fetch failed for {test_symbol}")
        except Exception as e:
            print(f"[DEBUG] Error testing {test_symbol}: {e}")

    # Sort signals by confidence
    signals.sort(key=lambda x: x['signal']['confidence'], reverse=True)
    
    # Sort signals by confidence
    signals.sort(key=lambda x: x['signal']['confidence'], reverse=True)
    
    # Output results
    if not signals:
        msg = "[INFO] No actionable trading signals found at this time."
        print(msg)
        
        # Track "no signals" event for consecutive loosening
        if market_analyzer:
            market_analyzer.track_no_signals_run()
            # Show updated parameters after tracking
            params = market_analyzer.get_adjusted_parameters()
            no_signals_count = market_analyzer.precision_metrics.get('consecutive_no_signals', 0)
            print(f"\n[LEARN] No-signals streak: {no_signals_count}")
            if no_signals_count >= 2:
                print(f"[LEARN] ⚠️  Parameters loosened automatically!")
                print(f"  • Confidence Threshold: {params.get('confidence_threshold', 0.3):.2f}")
                print(f"  • Entry Adjustment: {params.get('entry_adjustment_factor', 1.0):.2f}x")
                print(f"  • SL Adjustment: {params.get('sl_adjustment_factor', 1.0):.2f}x")
                print(f"  • TP Adjustment: {params.get('tp_adjustment_factor', 1.0):.2f}x")
            else:
                print(f"[LEARN] Will loosen after {2 - no_signals_count} more consecutive no-signal run(s)")
        
        send_telegram_message(msg)
        
        # Display final summary
        display_learning_status()
        
        return
    
    # Track that signals were generated (resets consecutive no-signals counter)
    if market_analyzer:
        market_analyzer.track_signals_generated()
        print("[LEARN] Signals generated - consecutive no-signals counter reset")
    
    print(f"\n{'='*60}")
    print(f"[TARGET] FOUND {len(signals)} TRADING SIGNALS")
    print(f"{'='*60}\n")
    
    # Create summary message for Telegram
    summary = f"""[AI] AI-DRIVEN TRADING SYSTEM (News: 24h | Trade: 2h)
[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | Duration: 2H
[TARGET] {len(signals)} Signals Found\n"""
    
    # Show top signals
    for idx, item in enumerate(signals[:5], start=1):  # Top 5 signals
        msg = format_trade_message(
            item['symbol'],
            item['signal'],
            item['sentiment_reason'],
            signal_number=idx
        )
        print(msg)
        print()

        # Add to summary
        summary += f"\n{msg}\n"

        # Log trade with indicators for learning
        print(f"[LOG] Logging trade for {item['symbol']}...")
        log_trade(item['symbol'], item['signal'], item['sentiment_reason'], item.get('indicators'))
        print(f"[LOG] Trade logged successfully for {item['symbol']}")
    
    # Send combined message to Telegram
    send_telegram_message(summary)
    
    print(f"\n[OK] Analysis complete. {len(signals)} signals generated.")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

    # Debug: Check if trades were logged
    try:
        with open(TRADE_LOG_FILE, 'r') as f:
            logged_trades = json.load(f)
        print(f"[DEBUG] Successfully logged {len(logged_trades)} total trades to {TRADE_LOG_FILE}")
        if logged_trades:
            latest_trade = logged_trades[-1]
            print(f"[DEBUG] Latest trade: {latest_trade['symbol']} {latest_trade['direction']} (status: {latest_trade['status']})")
    except FileNotFoundError:
        print(f"[DEBUG] No trades logged - {TRADE_LOG_FILE} not found")
    except Exception as e:
        print(f"[DEBUG] Error checking logged trades: {e}")
    
    # Display final learning status summary
    display_learning_status()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
