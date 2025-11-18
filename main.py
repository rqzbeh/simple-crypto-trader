#!/usr/bin/env python3
"""
Simple Crypto Trader - NEWS-DRIVEN Cryptocurrency Trading Signal Generator

[TARGET] PRIMARY APPROACH: NEWS TRADING (85-100%)
- News sentiment and AI analysis are the MAIN signal sources (85-90%)
- Technical indicators serve as FILTERS ONLY (10-15%)
- Technicals used for: entry price, stop loss, take profit, leverage calculation
- Trade based on market psychology, news events, and AI reasoning
- Technicals validate/filter out bad setups, not generate signals

Built for 24/7 crypto markets with SHORT-TERM trades (2-4 hours max duration)
"""

import os
import re
import json
import math
import time
import logging
import requests
from datetime import datetime, timedelta
from functools import lru_cache
from newsapi import NewsApiClient
import yfinance as yf
import pandas as pd
import numpy as np

# Import advanced technical indicators and LLM analyzer
from technical_indicators import get_all_indicators
from llm_analyzer import CryptoMarketAnalyzer

# Try to import optional components
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: Groq not available. Install with: pip install groq")

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
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not NEWS_API_KEY:
    raise ValueError('NEWS_API_KEY environment variable is required')

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Initialize Groq if available
if GROQ_AVAILABLE and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    market_analyzer = CryptoMarketAnalyzer(groq_client)
else:
    groq_client = None
    market_analyzer = CryptoMarketAnalyzer(None)

print("=" * 70)
print("SIMPLE CRYPTO TRADER - AI-Powered Signal Generator")
print("=" * 70)
print(f"NEWS_API: {'OK' if NEWS_API_KEY else 'MISSING'}")
print(f"GROQ_API: {'OK' if GROQ_API_KEY and GROQ_AVAILABLE else 'MISSING'}")
print(f"TELEGRAM: {'OK' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'MISSING'}")
print(f"ML Support: {'OK' if ML_AVAILABLE else 'MISSING'}")
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

# Default symbols to always analyze
DEFAULT_SYMBOLS = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOGE', 'XRP', 'MATIC']

# Crypto News Sources
CRYPTO_NEWS_SOURCES = [
    ('CoinDesk', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
    ('Cointelegraph', 'https://cointelegraph.com/rss'),
    ('CryptoSlate', 'https://cryptoslate.com/feed/'),
    ('Decrypt', 'https://decrypt.co/feed'),
    ('The Block', 'https://www.theblock.co/rss.xml'),
    ('Bitcoin Magazine', 'https://bitcoinmagazine.com/feed'),
    ('NewsBTC', 'https://www.newsbtc.com/feed/'),
    ('BeInCrypto', 'https://beincrypto.com/feed/'),
    ('CryptoPotato', 'https://cryptopotato.com/feed/'),
    ('U.Today', 'https://u.today/rss'),
]

# Risk Management Settings (Optimized for 2-4 hour SHORT-TERM trades)
# NEWS-DRIVEN TRADING: News and AI are primary signals (85-90%), technicals filter only (10-15%)
# Technicals provide: entry price, stop loss, take profit, leverage calculation
# 2-4h trade duration = need tighter stops and realistic targets
MIN_STOP_PCT = 0.008  # 0.8% minimum stop (tight for 2-4h trades)
MAX_STOP_PCT = 0.025  # 2.5% maximum stop (realistic for short-term trades)
TARGET_RR_RATIO = 3.0  # MINIMUM 1:3 risk/reward (can be higher for strong signals)

# NEWS IMPACT PARAMETERS (Primary Signal Source - 85-90%)
# Reduced for 2-4h SHORT-TERM trades
EXPECTED_RETURN_PER_SENTIMENT = 0.04  # 4% base per sentiment point (realistic for 2-4h)
NEWS_IMPACT_MULTIPLIER = 0.015  # 1.5% per news article
MAX_NEWS_BONUS = 0.05  # 5% max bonus from news volume

# Leverage caps - Higher for 4h timeframe (clearer trends)
MAX_LEVERAGE_CRYPTO = 10  # 10x max - 4h trends more reliable
MAX_LEVERAGE_STOCK = 5    # 5x for stocks

DAILY_RISK_LIMIT = 0.05  # 5% max daily loss (can take more risk with better R/R)

# Trading Parameters (2-4 hour SHORT-TERM trades)
# NEWS TRADING FOCUS: 85-90% emphasis on news/sentiment, 10-15% technical filter
LOW_MONEY_MODE = True  # Optimized for accounts < $500
if LOW_MONEY_MODE:
    EXPECTED_RETURN_PER_SENTIMENT = 0.05  # 5% for small accounts (realistic for 2-4h)
    NEWS_IMPACT_MULTIPLIER = 0.018  # 1.8% per article
    MAX_NEWS_BONUS = 0.06  # 6% max bonus
    MIN_STOP_PCT = 0.008  # 0.8% - tight for short-term trades

# Technical Indicator Weights (OPTIMIZED - No Conflicts/Redundancies)
# Reduced from 17 to 10 indicators by removing overlapping ones
INDICATOR_WEIGHTS = {
    # Momentum (Only the best one)
    'stoch_rsi': 2.5,     # Most sensitive momentum indicator for crypto
    
    # Trend Indicators (Each serves unique purpose)
    'ema_trend': 2.3,     # Multi-timeframe trend direction
    'macd': 2.0,          # Convergence/divergence (different from EMA)
    'supertrend': 1.9,    # Volatility-adjusted trend following
    'adx': 1.8,           # Trend STRENGTH filter (not direction)
    
    # Volatility (Best one + ATR for stops)
    'bb': 2.0,            # Bollinger Bands (industry standard)
    'atr': 0.0,           # Not directional - used only for stop-loss calculation
    
    # Volume (Unique purposes)
    'obv': 1.7,           # Accumulation/distribution
    'vwap': 2.1,          # Institutional price levels
    
    # Support/Resistance
    'pivot_points': 1.5,  # Classical S/R levels
}

# ML Configuration
ML_ENABLED = ML_AVAILABLE
ML_MODEL_FILE = 'crypto_ml_model.pkl'
ML_SCALER_FILE = 'crypto_ml_scaler.pkl'
ML_MIN_CONFIDENCE = 0.60
ML_RETRAIN_THRESHOLD = 20  # Retrain after 20 completed trades

# Files
TRADE_LOG_FILE = 'trade_log.json'
DAILY_RISK_FILE = 'daily_risk.json'

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
        print(f"Telegram error: {e}")

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
    """Fetch cryptocurrency news from multiple sources (optimized for 4-hour timeframe)"""
    articles = []
    cutoff = datetime.now() - timedelta(hours=8)  # Last 8 hours (2x our trading timeframe)
    
    # NewsAPI
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
                'source': article.get('source', {}).get('name', 'Unknown')
            })
    except Exception as e:
        print(f"NewsAPI error: {e}")
    
    # RSS Feeds (recent only)
    for name, url in CRYPTO_NEWS_SOURCES:
        items = fetch_rss_feed(url)
        for item in items[:10]:  # Limit to 10 most recent per source
            articles.append({
                'title': item['title'],
                'description': item['description'],
                'source': name
            })
    
    print(f"Fetched {len(articles)} news articles (last 8 hours)")
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
    """Analyze sentiment using Groq LLM"""
    if not groq_client or not articles:
        return 0.0, "No analysis available"
    
    # Prepare article summaries
    article_texts = []
    for i, article in enumerate(articles[:10], 1):  # Limit to 10 articles
        title = article.get('title', '')
        desc = article.get('description', '')
        article_texts.append(f"{i}. {title}\n   {desc[:200]}")
    
    combined_text = "\n".join(article_texts)
    
    prompt = f"""Analyze the sentiment of these cryptocurrency news articles about {symbol if symbol else 'the crypto market'}:

{combined_text}

Provide:
1. Overall sentiment score from -1.0 (very bearish) to +1.0 (very bullish)
2. Brief reasoning (2-3 sentences)

Format: SCORE: [number] | REASON: [text]"""
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        result = response.choices[0].message.content
        
        # Check if result is None
        if result is None:
            return 0.0, "No response from LLM"
        
        # Parse response
        score_match = re.search(r'SCORE:\s*([-+]?[0-9]*\.?[0-9]+)', result)
        reason_match = re.search(r'REASON:\s*(.+)', result, re.S)
        
        score = float(score_match.group(1)) if score_match else 0.0
        reason = reason_match.group(1).strip() if reason_match else result
        
        # Clamp score
        score = max(-1.0, min(1.0, score))
        
        return score, reason[:200]
    
    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            print(f"[WARNING] Groq API access denied - check API key or rate limits")
        else:
            print(f"LLM sentiment error: {e}")
        return 0.0, "LLM unavailable, using fallback sentiment"

def simple_sentiment(text):
    """Simple rule-based sentiment analysis as fallback"""
    text_lower = text.lower()
    
    positive = ['bullish', 'surge', 'rally', 'gain', 'rise', 'up', 'high', 'pump',
                'adoption', 'breakthrough', 'partnership', 'launch', 'success']
    negative = ['bearish', 'crash', 'drop', 'fall', 'down', 'low', 'dump', 'hack',
                'scam', 'ban', 'regulation', 'sell', 'loss', 'decline']
    
    pos_count = sum(1 for word in positive if word in text_lower)
    neg_count = sum(1 for word in negative if word in text_lower)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    return (pos_count - neg_count) / total

@lru_cache(maxsize=200)
def get_market_data(symbol, period='30d', interval='4h'):
    """
    Fetch market data and calculate advanced technical indicators
    Optimized for 4-hour trading timeframe:
    - 4h candles: excellent balance between noise and signal
    - 30 days history: ~180 candles for reliable indicators
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty or len(df) < 80:  # Need ~80 candles for 200 EMA
            return None
        
        close = df['Close']
        current_price = float(close.iloc[-1])
        
        # Calculate volatility (annualized for 4h candles)
        returns = close.pct_change()
        # 4h candles = 6 periods per day, 365 days
        volatility = float(returns.std() * np.sqrt(6 * 365))
        
        # Get all advanced technical indicators
        indicators = get_all_indicators(df)
        
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
    3. Technical indicators (FILTER ONLY - 10-15% + execution levels)
    
    Technicals are used to:
    - Filter out bad setups (contradiction check)
    - Calculate entry price, stop loss, take profit
    - Determine optimal leverage
    """
    if not market_data:
        return None
    
    price = market_data['price']
    indicators = market_data['indicators']
    
    # Base expected return from sentiment
    expected_return = sentiment_score * EXPECTED_RETURN_PER_SENTIMENT
    
    # News volume bonus
    news_bonus = min(news_count * NEWS_IMPACT_MULTIPLIER, MAX_NEWS_BONUS)
    expected_return += news_bonus if sentiment_score > 0 else -news_bonus
    
    # Technical indicator score (weighted combination with dynamic optimization)
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
    
    # Get adaptive parameters
    adaptive_params = market_analyzer.get_adjusted_parameters() if market_analyzer else {
        'confidence_threshold': 0.3,
        'risk_multiplier': 1.0
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
        expected_return *= (1 + abs(tech_score_normalized) * 0.5)
        if combined.get('agreement_boost'):
            expected_return *= 1.2  # Boost when all methods agree
    else:
        expected_return *= (1 + abs(tech_score_normalized) * 0.5)
    
    # Calculate stop loss with adaptive risk (optimized for 2-4h SHORT-TERM trades)
    # Use ATR as primary method with reasonable bounds for short-term trading
    atr_stop = market_data['atr_pct'] * 1.2  # 1.2x ATR - tighter for 2-4h trades
    
    # Ensure stop loss is tight for short-term trades
    # For 2-4h crypto trades: 0.8% min, 2.5% max
    stop_pct = max(MIN_STOP_PCT, min(atr_stop, MAX_STOP_PCT))
    
    # Apply adaptive risk adjustment from learning system
    stop_pct *= adaptive_params['risk_multiplier']
    
    # Final validation: ensure stop is within acceptable range for SHORT-TERM trades
    stop_pct = max(0.008, min(stop_pct, 0.025))  # Hard limits: 0.8% to 2.5% for 2-4h
    
    # Calculate take profit - TARGET 1:3 MINIMUM R/R (can be higher for strong signals)
    # Expected profit is driven by news/sentiment (PRIMARY signal source)
    expected_profit = abs(expected_return)
    
    # NEW: Apply TP adjustment factor from learning system
    # If system learned that TPs are too far, reduce them
    tp_adjustment = adaptive_params.get('tp_adjustment_factor', 1.0)
    expected_profit *= tp_adjustment
    
    # Consider recent actual price movements (use ATR as proxy for realistic movement)
    # For 2-4h timeframe, typical movements are 1-3x ATR
    realistic_movement = market_data['atr_pct'] * 2.5  # 2.5x ATR is realistic for 2-4h
    if expected_profit > realistic_movement * 2:
        # Cap overly ambitious TPs to 2x realistic movement
        expected_profit = realistic_movement * 2
    
    min_profit_for_target_rr = stop_pct * TARGET_RR_RATIO  # 1:3 minimum
    
    # Ensure we meet MINIMUM R/R ratio (but allow higher if signal is strong)
    if expected_profit < min_profit_for_target_rr:
        expected_profit = min_profit_for_target_rr  # Enforce 1:3 minimum only if below
    
    # Cap maximum take profit to be realistic for 2-4h SHORT-TERM trades
    # Max 5% BUT must respect minimum R/R ratio
    # If stop loss is high (e.g., 2.5%), we need higher TP to maintain 3:1 R/R (7.5%)
    # Strong signals can aim for higher R/R (4:1, 5:1, even 6:1)
    max_tp_cap = max(0.05, min_profit_for_target_rr)  # At least 5% or what's needed for 3:1 R/R
    expected_profit = min(expected_profit, max_tp_cap)
    
    # Risk/Reward ratio (will be >= 3:1, can be much higher)
    rr_ratio = expected_profit / stop_pct if stop_pct > 0 else 0
    
    # Skip trades that don't meet minimum R/R even after adjustment
    if rr_ratio < TARGET_RR_RATIO:
        return None  # Not worth the risk
    
    # Leverage recommendation - More aggressive for 4h timeframe
    # Formula: Use R/R ratio + confidence to determine leverage
    confidence_factor = combined['confidence']  # 0 to 1
    
    # Base leverage from R/R: Higher R/R = can use more leverage
    base_leverage = min(
        math.floor(rr_ratio + (confidence_factor * 5)),  # Add up to 5x based on confidence
        MAX_LEVERAGE_CRYPTO
    )
    
    # Reduce if LLM flags high risk
    if llm_analysis and llm_analysis.get('risk') == 'HIGH':
        base_leverage = max(2, base_leverage // 2)  # Halve but minimum 2x
    
    leverage = max(2, base_leverage)  # Minimum 2x leverage (4h timeframe justifies it)
    
    # Calculate prices
    if direction == 'LONG':
        stop_loss = price * (1 - stop_pct)
        take_profit = price * (1 + expected_profit)
    else:
        stop_loss = price * (1 + stop_pct)
        take_profit = price * (1 - expected_profit)
    
    return {
        'direction': direction,
        'entry_price': price,
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
        'timestamp': datetime.now().isoformat(),
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
        'check_time': (datetime.now() + timedelta(hours=4)).isoformat(),
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
                return risk_data.get('loss_pct', 0) >= DAILY_RISK_LIMIT
    except:
        pass
    return False

def check_trade_outcomes():
    """
    Check open trades and verify if predictions were correct
    Updates learning system with actual outcomes
    """
    try:
        with open(TRADE_LOG_FILE, 'r') as f:
            logs = json.load(f)
    except:
        return
    
    now = datetime.now()
    updated = False
    verified_count = 0
    
    for trade in logs:
        if trade.get('status') != 'open':
            continue
        
        # Check if 4 hours have passed (skip if no check_time)
        if 'check_time' not in trade:
            continue
        
        check_time = datetime.fromisoformat(trade['check_time'])
        if now < check_time:
            continue
        
        # Fetch current price to verify outcome
        symbol = trade['symbol']
        yf_symbol = CRYPTO_SYMBOL_MAP.get(symbol, f"{symbol}-USD")
        
        try:
            ticker = yf.Ticker(yf_symbol)
            current_data = ticker.history(period='1d', interval='1h')
            
            if current_data.empty:
                continue
            
            current_price = float(current_data['Close'].iloc[-1])
            entry_price = trade['entry_price']
            direction = trade['direction']
            
            # Calculate actual profit/loss
            if direction == 'LONG':
                price_change = (current_price - entry_price) / entry_price
            else:  # SHORT
                price_change = (entry_price - current_price) / entry_price
            
            actual_profit = price_change * trade.get('leverage', 1)
            
            # Check if hit stop loss or take profit
            if direction == 'LONG':
                hit_sl = current_price <= trade['stop_loss']
                hit_tp = current_price >= trade['take_profit']
            else:
                hit_sl = current_price >= trade['stop_loss']
                hit_tp = current_price <= trade['take_profit']
            
            if hit_sl:
                actual_profit = -(trade['stop_loss'] - entry_price) / entry_price * trade.get('leverage', 1)
                if direction == 'SHORT':
                    actual_profit = -actual_profit
                trade['status'] = 'stopped'
                trade['exit_price'] = trade['stop_loss']
            elif hit_tp:
                actual_profit = (trade['take_profit'] - entry_price) / entry_price * trade.get('leverage', 1)
                if direction == 'SHORT':
                    actual_profit = -actual_profit
                trade['status'] = 'completed'
                trade['exit_price'] = trade['take_profit']
            else:
                trade['status'] = 'checked'
                trade['exit_price'] = current_price
            
            trade['actual_profit'] = actual_profit
            trade['verified_at'] = now.isoformat()
            
            # Calculate precision metrics for learning
            # NEW: Track TP distance vs actual movement
            tp_price = trade['take_profit']
            if direction == 'LONG':
                tp_distance = (tp_price - entry_price) / entry_price
                actual_movement = (current_price - entry_price) / entry_price
            else:  # SHORT
                tp_distance = (entry_price - tp_price) / entry_price
                actual_movement = (entry_price - current_price) / entry_price
            
            # Feed to learning system with precision data
            if market_analyzer and trade.get('indicators'):
                trade_result = {
                    'profit': actual_profit,
                    'indicators': trade['indicators'],
                    'symbol': symbol,
                    'direction': direction,
                    'confidence': trade.get('confidence', 0),
                    'entry_price': entry_price,
                    'exit_price': trade['exit_price'],
                    # NEW: Precision tracking
                    'tp_distance': tp_distance,  # How far TP was set
                    'actual_movement': actual_movement,  # How far price actually moved
                    'hit_tp': hit_tp,  # Did it reach TP?
                    'hit_sl': hit_sl   # Did it hit SL?
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
            print(f"\n[OK] Verified {verified_count} trade outcomes and updated learning system\n")

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
    
    # Format numbers more compactly (without $ for easy copying)
    entry = f"{signal['entry_price']:.6f}".rstrip('0').rstrip('.')
    stop_loss = f"{signal['stop_loss']:.6f}".rstrip('0').rstrip('.')
    take_profit = f"{signal['take_profit']:.6f}".rstrip('0').rstrip('.')
    
    # Build message with signal number if provided
    signal_header = f"Signal #{signal_number}" if signal_number else "Signal"
    
    msg = f"""{signal_header}
━━━━━━━━━━━━━━━━━━━━
{direction_emoji} {symbol} - {direction_text}
━━━━━━━━━━━━━━━━━━━━

💵 Entry: $`{entry}`
🛑 Stop Loss: $`{stop_loss}` ({signal['stop_pct']*100:.2f}%)
🎯 Take Profit: $`{take_profit}` ({signal['expected_profit_pct']*100:.2f}%)

⚡️ Leverage: {signal['leverage']}x
📊 R/R: 1:{signal['rr_ratio']:.1f} {rr_quality}

{confidence_emoji} Confidence: {signal['confidence']*100:.1f}%
📰 News: {signal['sentiment_score']:.2f}
📈 Technical: {signal['technical_score']:.2f}"""
    
    return msg

# ==================== MAIN EXECUTION ====================

def main():
    """Main trading loop - NEWS-DRIVEN SHORT-TERM trading system (85-90% news/AI)"""
    print("\n[*] Starting Crypto Trading Signal Generator...")
    print("[NEWS] NEWS-DRIVEN TRADING SYSTEM (85-90% NEWS/AI)")
    print("=" * 70)
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"[MODE] Mode: {'Low Money' if LOW_MONEY_MODE else 'Standard'}")
    print(f"[DURATION] Trade Duration: 2-4 Hours (SHORT-TERM)")
    print(f"[TARGET] Strategy: News/AI Primary (85-90%) + Technical Filter (10-15%)")
    print(f"[TECH] Technicals: Entry Price, Stop Loss, Take Profit, Leverage")
    print(f"[LEVERAGE] Max Leverage: {MAX_LEVERAGE_CRYPTO}x")
    print(f"[RR] Min R/R: 1:{TARGET_RR_RATIO} (can be higher for strong signals)")
    print(f"[RISK] Stop Loss: {MIN_STOP_PCT*100:.1f}%-{MAX_STOP_PCT*100:.1f}%, Take Profit: up to {0.075*100:.1f}%")
    print("=" * 70)
    print()
    
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
    
    # Extract symbols from news
    symbol_articles = {}
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        symbols = extract_crypto_symbols(text)
        
        for symbol in symbols:
            if symbol not in symbol_articles:
                symbol_articles[symbol] = []
            symbol_articles[symbol].append(article)
    
    # Add default symbols
    for sym in DEFAULT_SYMBOLS:
        yf_symbol = CRYPTO_SYMBOL_MAP.get(sym, f"{sym}-USD")
        if yf_symbol not in symbol_articles:
            symbol_articles[yf_symbol] = articles[:5]  # Use general news
    
    print(f"[ANALYZE] Analyzing {len(symbol_articles)} cryptocurrencies...\n")
    
    # Analyze each symbol
    signals = []
    
    for yf_symbol, symbol_articles_list in symbol_articles.items():
        # Get clean symbol name
        symbol_name = yf_symbol.replace('-USD', '')
        
        print(f"Analyzing {symbol_name}...")
        
        # Analyze sentiment
        if groq_client:
            sentiment_score, sentiment_reason = analyze_sentiment_with_llm(
                symbol_articles_list, symbol_name
            )
        else:
            # Fallback to simple sentiment
            sentiment_texts = [f"{a.get('title', '')} {a.get('description', '')}" 
                             for a in symbol_articles_list]
            sentiment_score = sum(simple_sentiment(t) for t in sentiment_texts) / len(sentiment_texts) if sentiment_texts else 0
            sentiment_reason = f"Simple sentiment analysis (no LLM)"
        
        news_count = len(symbol_articles_list)
        
        # Get market data
        market_data = get_market_data(yf_symbol)
        if not market_data:
            print(f"  [WARNING] No market data available\n")
            continue
        
        # Calculate signal with LLM enhancement
        signal = calculate_trade_signal(sentiment_score, news_count, market_data, 
                                       symbol_name, symbol_articles_list)
        
        if signal and signal['confidence'] > 0.3:  # Minimum confidence threshold
            # Extract indicator signals for learning
            indicators_signals = {}
            for ind_name, ind_data in market_data['indicators'].items():
                if isinstance(ind_data, dict) and 'signal' in ind_data:
                    indicators_signals[ind_name] = ind_data['signal']
            
            signals.append({
                'symbol': symbol_name,
                'yf_symbol': yf_symbol,
                'signal': signal,
                'sentiment_reason': sentiment_reason,
                'news_count': news_count,
                'indicators': indicators_signals
            })
            print(f"  [OK] Signal: {signal['direction']} | Confidence: {signal['confidence']*100:.1f}%\n")
        else:
            print(f"  [INFO] No strong signal\n")
    
    # Sort signals by confidence
    signals.sort(key=lambda x: x['signal']['confidence'], reverse=True)
    
    # Output results
    if not signals:
        msg = "[INFO] No actionable trading signals found at this time."
        print(msg)
        send_telegram_message(msg)
        return
    
    print(f"\n{'='*60}")
    print(f"[TARGET] FOUND {len(signals)} TRADING SIGNALS")
    print(f"{'='*60}\n")
    
    # Create summary message for Telegram
    summary = f"""[NEWS] NEWS-DRIVEN TRADING SYSTEM (85-90% NEWS/AI)
[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | Duration: 2-4H
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
        log_trade(item['symbol'], item['signal'], item['sentiment_reason'], item.get('indicators'))
    
    # Send combined message to Telegram
    send_telegram_message(summary)
    
    print(f"\n[OK] Analysis complete. {len(signals)} signals generated.")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
