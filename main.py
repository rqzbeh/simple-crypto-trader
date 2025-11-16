#!/usr/bin/env python3
"""
Simple Crypto Trader - AI-Powered Cryptocurrency Trading Signal Generator
Built from scratch for 24/7 crypto markets with optimized indicators and risk management
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
print(f"NEWS_API: {'✓' if NEWS_API_KEY else '✗'}")
print(f"GROQ_API: {'✓' if GROQ_API_KEY and GROQ_AVAILABLE else '✗'}")
print(f"TELEGRAM: {'✓' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else '✗'}")
print(f"ML Support: {'✓' if ML_AVAILABLE else '✗'}")
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

# Risk Management Settings (Optimized for 3-hour timeframe)
# 3h candles = less noise = can use tighter stops and higher leverage
MIN_STOP_PCT = 0.012  # 1.2% minimum stop (tighter for 3h vs 2% for 1h)
MAX_STOP_PCT = 0.05   # 5% maximum stop
TARGET_RR_RATIO = 3.0  # Target 1:3 risk/reward minimum
EXPECTED_RETURN_PER_SENTIMENT = 0.04  # 4% base per sentiment point (3h moves)
NEWS_IMPACT_MULTIPLIER = 0.012  # 1.2% per news article
MAX_NEWS_BONUS = 0.06  # 6% max bonus from news

# Leverage caps - Higher for 3h timeframe (clearer trends)
MAX_LEVERAGE_CRYPTO = 10  # 10x max (vs 5x for 1h) - 3h trends more reliable
MAX_LEVERAGE_STOCK = 5    # 5x for stocks

DAILY_RISK_LIMIT = 0.05  # 5% max daily loss (can take more risk with better R/R)

# Trading Parameters (3-hour timeframe optimized)
LOW_MONEY_MODE = True  # Optimized for accounts < $500
if LOW_MONEY_MODE:
    EXPECTED_RETURN_PER_SENTIMENT = 0.05  # 5% for small accounts (3h moves are bigger)
    NEWS_IMPACT_MULTIPLIER = 0.015  # 1.5%
    MAX_NEWS_BONUS = 0.07  # 7%
    MIN_STOP_PCT = 0.010  # 1.0% - aggressive but 3h timeframe allows it

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
    """Fetch cryptocurrency news from multiple sources (optimized for 3-hour timeframe)"""
    articles = []
    cutoff = datetime.now() - timedelta(hours=6)  # Last 6 hours (2x our trading timeframe)
    
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
    
    print(f"Fetched {len(articles)} news articles (last 6 hours)")
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
        
        # Parse response
        score_match = re.search(r'SCORE:\s*([-+]?[0-9]*\.?[0-9]+)', result)
        reason_match = re.search(r'REASON:\s*(.+)', result, re.S)
        
        score = float(score_match.group(1)) if score_match else 0.0
        reason = reason_match.group(1).strip() if reason_match else result
        
        # Clamp score
        score = max(-1.0, min(1.0, score))
        
        return score, reason[:200]
    
    except Exception as e:
        print(f"LLM sentiment error: {e}")
        return 0.0, f"Error: {str(e)[:100]}"

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
def get_market_data(symbol, period='10d', interval='3h'):
    """
    Fetch market data and calculate advanced technical indicators
    Optimized for 3-hour trading timeframe:
    - 3h candles: balance between noise and signal
    - 10 days history: ~80 candles for reliable indicators
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty or len(df) < 80:  # Need ~80 candles for 200 EMA
            return None
        
        close = df['Close']
        current_price = float(close.iloc[-1])
        
        # Calculate volatility (annualized for 3h candles)
        returns = close.pct_change()
        # 3h candles = 8 periods per day, 365 days
        volatility = float(returns.std() * np.sqrt(8 * 365))
        
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
    
    except Exception as e:
        print(f"Market data error for {symbol}: {e}")
        return None

def calculate_trade_signal(sentiment_score, news_count, market_data, symbol='', news_articles=None):
    """
    Enhanced trading signal calculation using:
    1. Technical indicators (quantitative, proven)
    2. Sentiment analysis (market psychology)
    3. LLM reasoning (adaptive, qualitative) - inspired by AI-Trader
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
    
    # Technical indicator score (weighted combination)
    tech_score = 0
    total_weight = 0
    
    for indicator, weight in INDICATOR_WEIGHTS.items():
        if indicator in indicators and 'signal' in indicators[indicator]:
            tech_score += indicators[indicator]['signal'] * weight
            total_weight += weight
    
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
    
    # Calculate stop loss with adaptive risk (tighter for 3h timeframe)
    atr_stop = market_data['atr_pct'] * 1.5  # 1.5x ATR (vs 2x for 1h) - 3h has less noise
    stop_pct = max(MIN_STOP_PCT, min(atr_stop, MAX_STOP_PCT))
    stop_pct *= adaptive_params['risk_multiplier']  # Adaptive risk adjustment
    
    # Calculate take profit - TARGET 1:3 minimum R/R
    expected_profit = abs(expected_return)
    min_profit_for_target_rr = stop_pct * TARGET_RR_RATIO  # 1:3 minimum
    
    if expected_profit < min_profit_for_target_rr:
        expected_profit = min_profit_for_target_rr  # Force 1:3 minimum
    
    # Risk/Reward ratio
    rr_ratio = expected_profit / stop_pct if stop_pct > 0 else 0
    
    # Skip trades that don't meet minimum R/R even after adjustment
    if rr_ratio < TARGET_RR_RATIO:
        return None  # Not worth the risk
    
    # Leverage recommendation - More aggressive for 3h timeframe
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
    
    leverage = max(2, base_leverage)  # Minimum 2x leverage (3h timeframe justifies it)
    
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
        'adaptive_threshold': adaptive_params['confidence_threshold']
    }

def log_trade(symbol, signal, sentiment_reason=''):
    """Log trade to file"""
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
        'status': 'open'
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

def format_trade_message(symbol, signal, sentiment_reason=''):
    """Format trade signal for output"""
    msg = f"""
{'='*60}
🚨 CRYPTO TRADE SIGNAL (3H TIMEFRAME)
{'='*60}
Symbol: {symbol}
Direction: {signal['direction']} {'🟢' if signal['direction'] == 'LONG' else '🔴'}
Entry: ${signal['entry_price']:.6f}
Stop Loss: ${signal['stop_loss']:.6f} ({signal['stop_pct']*100:.2f}%)
Take Profit: ${signal['take_profit']:.6f} ({signal['expected_profit_pct']*100:.2f}%)
Leverage: {signal['leverage']}x 💪
Risk/Reward: 1:{signal['rr_ratio']:.1f} {'🎯' if signal['rr_ratio'] >= 3 else '⚡'}
Confidence: {signal['confidence']*100:.1f}%

📊 Analysis:
Sentiment: {signal['sentiment_score']:.2f} | Technical: {signal['technical_score']:.2f}
{sentiment_reason[:200]}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | Timeframe: 3H
{'='*60}
"""
    return msg

# ==================== MAIN EXECUTION ====================

def main():
    """Main trading loop - 3-hour timeframe optimized"""
    print("\n🚀 Starting Crypto Trading Signal Generator...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"💰 Mode: {'Low Money' if LOW_MONEY_MODE else 'Standard'}")
    print(f"⏱️  Timeframe: 3 Hours (optimal balance)")
    print(f"🎯 Max Leverage: {MAX_LEVERAGE_CRYPTO}x")
    print(f"🎲 Target R/R: 1:{TARGET_RR_RATIO} minimum")
    print(f"🛡️ Daily Risk Limit: {DAILY_RISK_LIMIT*100}%\n")
    
    # Check daily risk limit
    if check_daily_risk():
        msg = "⚠️ Daily risk limit reached. No new trades today."
        print(msg)
        send_telegram_message(msg)
        return
    
    # Fetch news
    print("📰 Fetching crypto news...")
    articles = get_crypto_news()
    
    if not articles:
        print("⚠️ No news articles found")
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
    
    print(f"📈 Analyzing {len(symbol_articles)} cryptocurrencies...\n")
    
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
            print(f"  ⚠️ No market data available\n")
            continue
        
        # Calculate signal with LLM enhancement
        signal = calculate_trade_signal(sentiment_score, news_count, market_data, 
                                       symbol_name, symbol_articles_list)
        
        if signal and signal['confidence'] > 0.3:  # Minimum confidence threshold
            signals.append({
                'symbol': symbol_name,
                'yf_symbol': yf_symbol,
                'signal': signal,
                'sentiment_reason': sentiment_reason,
                'news_count': news_count
            })
            print(f"  ✅ Signal: {signal['direction']} | Confidence: {signal['confidence']*100:.1f}%\n")
        else:
            print(f"  ℹ️ No strong signal\n")
    
    # Sort signals by confidence
    signals.sort(key=lambda x: x['signal']['confidence'], reverse=True)
    
    # Output results
    if not signals:
        msg = "ℹ️ No actionable trading signals found at this time."
        print(msg)
        send_telegram_message(msg)
        return
    
    print(f"\n{'='*60}")
    print(f"🎯 FOUND {len(signals)} TRADING SIGNALS")
    print(f"{'='*60}\n")
    
    # Show top signals
    for item in signals[:5]:  # Top 5 signals
        msg = format_trade_message(
            item['symbol'],
            item['signal'],
            item['sentiment_reason']
        )
        print(msg)
        
        # Log trade
        log_trade(item['symbol'], item['signal'], item['sentiment_reason'])
        
        # Send to Telegram
        send_telegram_message(msg)
        
        time.sleep(1)  # Rate limiting
    
    print(f"\n✅ Analysis complete. {len(signals)} signals generated.")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
