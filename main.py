import os
import time
import math
import re
import requests
import logging
import json
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from newsapi import NewsApiClient
import yfinance as yf
from textblob import TextBlob
# import snscrape.modules.twitter as sntwitter

# Silence yfinance verbosity
logging.getLogger("yfinance").setLevel(logging.ERROR)

# -------------------- Configuration ---------------- ----
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
if not NEWS_API_KEY:
    raise ValueError('Please set the NEWS_API_KEY environment variable')

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

def send_telegram_message(message):
    """Send a message via Telegram bot."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("Telegram credentials not set. Skipping Telegram send.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_market_session():
    """
    Detect the current market session based on UTC time and weekday.
    Returns a dict with session name, multiplier, and whether trading is allowed.
    """
    now_utc = datetime.now(timezone.utc)
    current_hour = now_utc.hour
    current_weekday = now_utc.weekday()  # 0=Monday, 6=Sunday
    
    # Check if it's weekend (Saturday=5, Sunday=6)
    if current_weekday >= 5:
        return {
            'session': 'Weekend',
            'multiplier': 0.0,
            'allow_trading': False,
            'reason': 'Weekend - Markets closed'
        }
    
    # Determine active session based on UTC hour
    # Priority reflects trading volume: New York > London > Tokyo > Sydney
    active_session = None
    
    if 13 <= current_hour < 22:  # New York (1PM-10PM UTC, 9 hours)
        active_session = 'New York'
    elif 8 <= current_hour < 13:  # London (8AM-1PM UTC, 5 hours)
        active_session = 'London'
    elif 0 <= current_hour < 8:  # Tokyo (12AM-8AM UTC, 8 hours)
        active_session = 'Tokyo'
    elif 22 <= current_hour < 24:  # Sydney (10PM-midnight UTC, 2 hours)
        active_session = 'Sydney'
    else:
        active_session = 'Off-Hours'
    
    session_config = MARKET_SESSIONS.get(active_session, MARKET_SESSIONS['Off-Hours'])
    
    # For crypto, allow trading in all sessions except weekends
    allow_trading = True
    
    return {
        'session': active_session,
        'multiplier': session_config['multiplier'],
        'allow_trading': allow_trading,
        'reason': f'{active_session} session active'
    }


CRYPTO_RSS_FEEDS = [
    ('CoinDesk', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
    ('Cointelegraph', 'https://cointelegraph.com/rss'),
    ('CoinMarketCap', 'https://coinmarketcap.com/headlines/news/'),
    ('CryptoSlate', 'https://cryptoslate.com/feed/'),
    ('Decrypt', 'https://decrypt.co/feed'),
    ('The Block', 'https://www.theblock.co/rss.xml'),
    ('Crypto News', 'https://cryptonews.com/news/rss/'),
    ('Bitcoin Magazine', 'https://bitcoinmagazine.com/feed'),
    ('Ethereum World News', 'https://ethereumworldnews.com/feed/'),
    ('CoinGecko', 'https://www.coingecko.com/en/news/rss'),
    ('Crypto Briefing', 'https://cryptobriefing.com/feed/'),
    ('AMB Crypto', 'https://ambcrypto.com/feed/'),
    ('NewsBTC', 'https://www.newsbtc.com/feed/'),
    ('BeInCrypto', 'https://beincrypto.com/feed/'),
    ('CryptoPotato', 'https://cryptopotato.com/feed/'),
]

# Map simple tickers/names to yfinance symbols for crypto (expanded list)
CRYPTO_SYMBOL_MAP = {
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD',
    'DOGE': 'DOGE-USD',
    'SHIB': 'SHIB-USD',
    'SOL': 'SOL-USD',
    'ADA': 'ADA-USD',
    'XRP': 'XRP-USD',
    'LTC': 'LTC-USD',
    'BNB': 'BNB-USD',
    'LINK': 'LINK-USD',
    'AVAX': 'AVAX-USD',
    'MATIC': 'MATIC-USD',
    'DOT': 'DOT-USD',
    'UNI': 'UNI-USD',
    'AAVE': 'AAVE-USD',
    'SUSHI': 'SUSHI-USD',
    'CAKE': 'CAKE-USD',
    'LUNA': 'LUNA-USD',
    'ATOM': 'ATOM-USD',
    'ALGO': 'ALGO-USD',
    'VET': 'VET-USD',
    'ICP': 'ICP-USD',
    'FIL': 'FIL-USD',
    'TRX': 'TRX-USD',
    'ETC': 'ETC-USD',
    'XLM': 'XLM-USD',
    'THETA': 'THETA-USD',
    'FTT': 'FTT-USD',
    'HBAR': 'HBAR-USD',
    'NEAR': 'NEAR-USD',
    'FLOW': 'FLOW-USD',
    'MANA': 'MANA-USD',
    'SAND': 'SAND-USD',
    'AXS': 'AXS-USD',
    'CHZ': 'CHZ-USD',
    'ENJ': 'ENJ-USD',
    'BAT': 'BAT-USD',
    'OMG': 'OMG-USD',
    'ZRX': 'ZRX-USD',
    'REP': 'REP-USD',
    'GNT': 'GNT-USD',
    'STORJ': 'STORJ-USD',
    'ANT': 'ANT-USD',
    'MKR': 'MKR-USD',
    'COMP': 'COMP-USD',
    'YFI': 'YFI-USD',
    'BAL': 'BAL-USD',
    'REN': 'REN-USD',
    'LRC': 'LRC-USD',
    'KNC': 'KNC-USD',
    'ZKS': 'ZKS-USD',
    'IMX': 'IMX-USD',
    'APE': 'APE-USD',
    'GMT': 'GMT-USD',
    'GAL': 'GAL-USD',
    'OP': 'OP-USD',
    'ARB': 'ARB11841-USD',
    'PEPE': 'PEPE-USD',
    'FLOKI': 'FLOKI-USD',
    'BONK': 'BONK-USD',
    'WIF': 'WIF-USD',
    'MEW': 'MEW-USD',
    'POPCAT': 'POPCAT-USD',
    'TURBO': 'TURBO-USD',
    'BRETT': 'BRETT-USD',
    'MOTHER': 'MOTHER-USD',
    'CUMMIES': 'CUMMIES-USD',
    'SLERF': 'SLERF-USD',
    'GOAT': 'GOAT-USD',
    'WEN': 'WEN-USD',
    'WIF': 'WIF-USD',
    'SMOG': 'SMOG-USD',
}

# Aliases for additional search terms
CRYPTO_ALIASES = {
    'BITCOIN': 'BTC',
    'ETHEREUM': 'ETH',
    'DOGECOIN': 'DOGE',
    'SHIBA': 'SHIB',
    'SHIBAINU': 'SHIB',
    'SOLANA': 'SOL',
    'CARDANO': 'ADA',
    'TRON': 'TRX',
    'POLYGON': 'MATIC',
    'POLKADOT': 'DOT',
    'UNISWAP': 'UNI',
    'PANCAKESWAP': 'CAKE',
    'TERRA': 'LUNA',
    'COSMOS': 'ATOM',
    'ALGORAND': 'ALGO',
    'VECHAIN': 'VET',
    'INTERNETCOMPUTER': 'ICP',
    'FILECOIN': 'FIL',
    'ETHEREUMCLASSIC': 'ETC',
    'STELLAR': 'XLM',
    'FTXTOKEN': 'FTT',
    'HEDERA': 'HBAR',
    'DECENTRALAND': 'MANA',
    'AXIEINFINITY': 'AXS',
    'CHILIZ': 'CHZ',
    'ENJIN': 'ENJ',
    'BASICATTENTIONTOKEN': 'BAT',
    'OMISEGO': 'OMG',
    '0X': 'ZRX',
    'AUGUR': 'REP',
    'GOLEM': 'GNT',
    'ARAGON': 'ANT',
    'MAKER': 'MKR',
    'COMPOUND': 'COMP',
    'YEARN': 'YFI',
    'BALANCER': 'BAL',
    'LOOPRING': 'LRC',
    'KYBER': 'KNC',
    'ZKSYNC': 'ZKS',
    'IMMUTABLEX': 'IMX',
    'APECOIN': 'APE',
    'STEPN': 'GMT',
    'GALAXY': 'GAL',
    'OPTIMISM': 'OP',
    'ARBITRUM': 'ARB',
    'DOGWIFHAT': 'WIF',
    'CATINME': 'MEW',
}

# Risk settings (optimized for 15m or 30m fast trading)
MIN_STOP_PCT = 0.001  # 0.1% minimal stop for 15m/30m
EXPECTED_RETURN_PER_SENTIMENT = 0.001  # 0.1% per full +1.0 sentiment for 15m/30m
NEWS_COUNT_BONUS = 0.0005  # 0.05% per article bonus
MAX_NEWS_BONUS = 0.002  # Max 0.2%

# Leverage caps - Updated to 100x for crypto
MAX_LEVERAGE_CRYPTO = 100
MAX_LEVERAGE_STOCK = 5

# Low money mode flag - Set to True for accounts with small capital (< $500 equivalent)
LOW_MONEY_MODE = False

if LOW_MONEY_MODE:
    EXPECTED_RETURN_PER_SENTIMENT = 0.002  # Higher ROI to offset fees
    NEWS_COUNT_BONUS = 0.001  # Increased bonus
    MAX_NEWS_BONUS = 0.004  # Higher max bonus
    MIN_STOP_PCT = 0.0005  # Tighter stops for better R/R

# Trade logging file
TRADE_LOG_FILE = 'trade_log.json'

# Indicator weights (adaptive learning)
ICHIMOKU_WEIGHT = 1.2
VOLUME_WEIGHT = 1.15
FVG_WEIGHT = 1.1
CANDLE_WEIGHT = 1.1
NEW_TECHNIQUE_ENABLED = False  # Placeholder for adding new techniques

# Market session configurations
# Note: All 24 hours covered by major sessions (crypto trades 24/7)
MARKET_SESSIONS = {
    'Sydney': {'multiplier': 0.95},     # 10PM-midnight UTC (2 hours)
    'Tokyo': {'multiplier': 1.0},       # 12AM-8AM UTC (8 hours)
    'London': {'multiplier': 1.15},     # 8AM-1PM UTC (5 hours, NY takes priority 1PM+)
    'New York': {'multiplier': 1.2},    # 1PM-10PM UTC (9 hours)
    'Off-Hours': {'multiplier': 0.85}   # Fallback (not used with current ranges)
}

def fetch_rss_items(url):
    '''Fetch RSS/Atom feed and return list of {'title','description'} items (best-effort).'''
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'news-trader/1.0'})
        text = resp.text
        items = []
        # crude parsing: find <item> blocks
        for block in re.findall(r'<item>(.*?)</item>', text, flags=re.S | re.I):
            title_m = re.search(r'<title>(.*?)</title>', block, flags=re.S | re.I)
            desc_m = re.search(r'<description>(.*?)</description>', block, flags=re.S | re.I)
            title = re.sub('<.*?>', '', title_m.group(1)).strip() if title_m else ''
            desc = re.sub('<.*?>', '', desc_m.group(1)).strip() if desc_m else ''
            if title or desc:
                items.append({'title': title, 'description': desc})
        return items
    except Exception as e:
        print(f'Failed to fetch RSS {url}: {e}')
        return []

# def fetch_tweets():
#     '''Fetch recent tweets from influential users.'''
#     users = ['elonmusk', 'realDonaldTrump', 'vitalikbuterin', 'cz_binance', 'brian_armstrong', 'saylor', 'michaeljburry', 'TimDraper', 'rogerkver', 'BarrySilbert', 'brian_armstrong', 'sandeepna[...]
#     tweets = []
#     cutoff = datetime.now() - timedelta(hours=24) # Last 24 hours for fast trading
#     for user in users:
#         try:
#             query = f'from:{user} since:{cutoff.date()}'
#             for tweet in sntwitter.TwitterSearchScraper(query).get_items():
#                 if tweet.date.replace(tzinfo=None) < cutoff:
#                 break
#                 tweets.append({'title': tweet.rawContent, 'description': '', 'source': f'Twitter-{user}'})
#         except Exception as e:
#             print(f'Failed to fetch tweets from {user}: {e}')
#     return tweets

def get_news():
    '''Fetch news from NewsAPI, RSS, and influential tweets.'''
    results = []
    cutoff = datetime.now() - timedelta(hours=48)  # Last 48 hours for more data
    try:
        # Fetch crypto/business related from NewsAPI (use q to bias crypto)
        resp_crypto = newsapi.get_everything(q='cryptocurrency OR crypto OR bitcoin OR ethereum OR blockchain OR nft OR defi OR solana OR dogecoin', language='en', sort_by='publishedAt', page_size=100)
        resp_general = newsapi.get_top_headlines(category='business', language='en', country='us', page_size=100)
        for a in resp_crypto.get('articles', []) + resp_general.get('articles', []):
            pub_date = a.get('publishedAt')
            if pub_date:
                try:
                    pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    if pub_dt < cutoff:
                        continue
                except:
                    pass  # Include if can't parse
            results.append({'title': a.get('title', ''), 'description': a.get('description', ''), 'source': a.get('source', {}).get('name')})
    except Exception as e:
        print(f'NewsAPI fetch error: {e}')

    # Fetch RSS-based crypto sources (assume recent)
    for name, url in CRYPTO_RSS_FEEDS:
        items = fetch_rss_items(url)
        for it in items:
            results.append({'title': it.get('title', ''), 'description': it.get('description', ''), 'source': name})

    # Fetch influential tweets (commented out due to snscrape issues in Python 3.12)
    # tweets = fetch_tweets()
    # results.extend(tweets)

    return results

def normalize_text(s: str) -> str:
    return (s or '').upper()

# --- REPLACE your extract_crypto_and_tickers() with this version ---
def extract_crypto_and_tickers(text: str):
    """
    Return list of dicts: {'symbol','yf','kind'} where kind in {'crypto','stock'}.
    Rules:
      - Accept $TICKER only if it’s a known crypto symbol or passes a quick market-data check.
      - Accept plain crypto names/symbols from CRYPTO_SYMBOL_MAP and CRYPTO_ALIASES.
      - Do NOT infer generic ALL-CAPS words as tickers.
    """
    text_u = normalize_text(text)
    found = {}
 
    # 1) $TICKER patterns (common in crypto/news posts)
    for m in re.findall(r'\$([A-Z]{2,6})\b', text_u):
        key = m.upper()
        if key in CRYPTO_SYMBOL_MAP:
            found[key] = (CRYPTO_SYMBOL_MAP[key], 'crypto')
        elif key in CRYPTO_ALIASES:
            canonical = CRYPTO_ALIASES[key]
            found[canonical] = (CRYPTO_SYMBOL_MAP[canonical], 'crypto')
        else:
            # tentatively a stock-like ticker; validate before keeping
            yf_sym = key
            if _symbol_has_prices(yf_sym):
                found[key] = (yf_sym, 'stock')

    # 2) Plain crypto tickers and names (BTC, ETH, BITCOIN, etc.)
    for name in CRYPTO_SYMBOL_MAP:
        if re.search(r'\b' + re.escape(name) + r'\b', text_u):
            found[name] = (CRYPTO_SYMBOL_MAP[name], 'crypto')
    for alias in CRYPTO_ALIASES:
        if re.search(r'\b' + re.escape(alias) + r'\b', text_u):
            canonical = CRYPTO_ALIASES[alias]
            found[canonical] = (CRYPTO_SYMBOL_MAP[canonical], 'crypto')

    return [{'symbol': k, 'yf': v[0], 'kind': v[1]} for k, v in found.items()]

def analyze_sentiment(texts):
    '''Aggregate sentiment over a list of texts using TextBlob. Boost influential sources.'''
    scores = []
    for t in texts:
        try:
            b = TextBlob(t)
            polarity = b.sentiment.polarity
            # Boost sentiment from influential tweets
            if 'Twitter-' in t.get('source', ''):
                polarity *= 2.0  # Double weight for Elon/Trump tweets
            scores.append(polarity)
        except Exception:
            continue
    if not scores:
        return 0.0
    # weighted by recency could be added; simple average for now
    return sum(scores) / len(scores)

@lru_cache(maxsize=100)
def get_market_data(yf_symbol, kind='stock'):
    """Get recent price, volatility/ATR, pivots, S/R, psych levels, candle patterns, smart money volume, ICT FVG."""
    try:
        ticker = yf.Ticker(yf_symbol)
        # Use 30m for low money mode (better ROI, fewer fees), else 15m
        interval = '30m' if LOW_MONEY_MODE else '15m'
        hist_hourly = ticker.history(period='3d', interval=interval)
        # Daily data for pivots
        hist_daily = ticker.history(period='30d', interval='1d')
        if hist_hourly.empty or len(hist_hourly) < 26 or hist_daily.empty or len(hist_daily) < 2:
            return None

        # Skip delisted or low-volume symbols
        if hist_hourly['Volume'].tail(10).mean() < 1000:  # Arbitrary low volume check
            return None

        close = hist_hourly['Close'].dropna()
        high = hist_hourly['High'].dropna()
        low = hist_hourly['Low'].dropna()
        volume = hist_hourly['Volume'].dropna()
        current_price = float(close.iloc[-1])

        # Volatility and ATR
        hourly_returns = close.pct_change().dropna()
        vol_hourly = hourly_returns.std()
        tr = []
        for i in range(1, len(high)):
            tr.append(max(high.iloc[i] - low.iloc[i], abs(high.iloc[i] - close.iloc[i-1]), abs(low.iloc[i] - close.iloc[i-1])))
        atr = sum(tr[-14:]) / min(14, len(tr)) if tr else 0
        atr_pct = atr / current_price

        # Pivots from previous day
        prev_day = hist_daily.iloc[-2]  # Yesterday
        pivot = (prev_day['High'] + prev_day['Low'] + prev_day['Close']) / 3
        r1 = 2 * pivot - prev_day['Low']
        s1 = 2 * pivot - prev_day['High']
        r2 = pivot + (prev_day['High'] - prev_day['Low'])
        s2 = pivot - (prev_day['High'] - prev_day['Low'])

        # Support/Resistance: recent swing highs/lows (simple: max/min of last 20 hours)
        recent_high = high.tail(20).max()
        recent_low = low.tail(20).min()

        # Psychological levels: round to nearest 100 for BTC, 10 for ETH, etc.
        if 'BTC' in yf_symbol.upper():
            psych_level = round(current_price / 100) * 100
        elif 'ETH' in yf_symbol.upper():
            psych_level = round(current_price / 10) * 10
        else:
            psych_level = round(current_price / 1) * 1  # For altcoins

        # Candle patterns: simple bullish/bearish signal from last 3 candles
        candle_signal = 0  # -1 bearish, 0 neutral, 1 bullish
        if len(close) >= 3:
            last3 = close.tail(3).values
            if last3[2] > last3[1] > last3[0]:  # Rising
                candle_signal = 1
            elif last3[2] < last3[1] < last3[0]:  # Falling
                candle_signal = -1

        # Ichimoku Cloud
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        chikou = close.shift(-26)
        ichimoku_signal = 0  # 1 bullish, -1 bearish
        if (current_price > senkou_a.iloc[-1] and current_price > senkou_b.iloc[-1] and 
            tenkan.iloc[-1] > kijun.iloc[-1] and senkou_a.iloc[-1] > senkou_b.iloc[-1]):
            ichimoku_signal = 1
        elif (current_price < senkou_a.iloc[-1] and current_price < senkou_b.iloc[-1] and 
              tenkan.iloc[-1] < kijun.iloc[-1] and senkou_a.iloc[-1] < senkou_b.iloc[-1]):
            ichimoku_signal = -1

        # Smart Money: Volume confirmation (institutional order flow)
        volume_avg = volume.tail(20).mean()
        recent_volume = volume.iloc[-1]
        volume_signal = 0  # 1 smart money buying, -1 smart money selling
        if recent_volume > volume_avg * 1.2:
            if close.iloc[-1] > close.iloc[-2]:
                volume_signal = 1
            elif close.iloc[-1] < close.iloc[-2]:
                volume_signal = -1

        # ICT: Fair Value Gap (FVG) detection - simple version
        fvg_signal = 0  # 1 bullish FVG, -1 bearish FVG
        if len(close) >= 4:
            # Bullish FVG: low of current > high of 2 candles ago
            if low.iloc[-1] > high.iloc[-3]:
                fvg_signal = 1
            # Bearish FVG: high of current < low of 2 candles ago
            elif high.iloc[-1] < low.iloc[-3]:
                fvg_signal = -1

        return {
            'price': current_price,
            'volatility_hourly': float(vol_hourly),
            'atr_pct': float(atr_pct),
            'pivot': float(pivot),
            'r1': float(r1), 'r2': float(r2),
            's1': float(s1), 's2': float(s2),
            'support': float(recent_low),
            'resistance': float(recent_high),
            'psych_level': float(psych_level),
            'candle_signal': candle_signal,
            'ichimoku_signal': ichimoku_signal,
            'volume_signal': volume_signal,
            'fvg_signal': fvg_signal
        }
    except Exception as e:
        # Suppress yfinance errors for cleaner output
        return None

def recommend_leverage(rr, volatility, kind='crypto'):
    '''Recommend leverage given RR and volatility. Returns integer leverage.'''
    # Base leverage from RR: more RR allows more leverage
    base = max(1, int(math.floor(rr * 10)))  # Increased multiplier for higher leverage in crypto
    # Cap by asset class
    max_lev = MAX_LEVERAGE_CRYPTO if kind == 'crypto' else MAX_LEVERAGE_STOCK
    # If volatility is very high, reduce recommended leverage
    if volatility is None:
        volatility = 1.0
    if volatility > 1.0:  # >100% annualized -> risky
        max_lev = min(max_lev, 50)  # Adjusted for higher cap
    if volatility > 2.0:
        max_lev = min(max_lev, 20)
    lev = min(base, max_lev)
    return max(1, lev)

def calculate_trade_plan(avg_sentiment, news_count, market_data, session_multiplier=1.0):
    '''Return dict with direction, expected_profit_pct, stop_pct, rr, recommended_leverage.'''
    global ICHIMOKU_WEIGHT, VOLUME_WEIGHT, FVG_WEIGHT, CANDLE_WEIGHT
    if not market_data:
        return None
    price = market_data['price']
    pivot = market_data['pivot']
    r1 = market_data['r1']
    r2 = market_data['r2']
    s1 = market_data['s1']
    s2 = market_data['s2']
    support = market_data['support']
    resistance = market_data['resistance']
    psych_level = market_data['psych_level']
    candle_signal = market_data['candle_signal']
    ichimoku_signal = market_data['ichimoku_signal']
    volume_signal = market_data['volume_signal']
    fvg_signal = market_data['fvg_signal']

    # sentiment-driven expected move
    news_bonus = min(MAX_NEWS_BONUS, NEWS_COUNT_BONUS * news_count)
    expected_return = avg_sentiment * EXPECTED_RETURN_PER_SENTIMENT + news_bonus * (1 if avg_sentiment >= 0 else -1)
    
    # Apply market session multiplier to expected return
    expected_return *= session_multiplier

    # Adjust for technical levels
    # Near resistance: reduce bullish
    if price > resistance * 0.98:
        expected_return *= 0.8
    # Near support: boost bullish
    if price < support * 1.02:
        expected_return *= 1.2
    # Near pivot: neutral
    # Psychological magnet: if close to psych level, slight boost
    if abs(price - psych_level) / price < 0.01:
        expected_return *= 1.1

    # Candle confirmation: boost if matches sentiment (using adaptive weight)
    if (avg_sentiment > 0 and candle_signal > 0) or (avg_sentiment < 0 and candle_signal < 0):
        expected_return *= CANDLE_WEIGHT
    elif (avg_sentiment > 0 and candle_signal < 0) or (avg_sentiment < 0 and candle_signal > 0):
        expected_return *= (2 - CANDLE_WEIGHT)  # Dampen inversely

    # Ichimoku confirmation: boost if matches sentiment
    if (avg_sentiment > 0 and ichimoku_signal > 0) or (avg_sentiment < 0 and ichimoku_signal < 0):
        expected_return *= ICHIMOKU_WEIGHT
    elif (avg_sentiment > 0 and ichimoku_signal < 0) or (avg_sentiment < 0 and ichimoku_signal > 0):
        expected_return *= (2 - ICHIMOKU_WEIGHT)
    elif ichimoku_signal == 0:
        expected_return *= 0.95  # slight dampen if Ichimoku neutral

    # Smart Money: Volume confirmation boost
    if (avg_sentiment > 0 and volume_signal > 0) or (avg_sentiment < 0 and volume_signal < 0):
        expected_return *= VOLUME_WEIGHT
    elif (avg_sentiment > 0 and volume_signal < 0) or (avg_sentiment < 0 and volume_signal > 0):
        expected_return *= (2 - VOLUME_WEIGHT)

    # ICT: FVG confirmation
    if (avg_sentiment > 0 and fvg_signal > 0) or (avg_sentiment < 0 and fvg_signal < 0):
        expected_return *= FVG_WEIGHT
    elif (avg_sentiment > 0 and fvg_signal < 0) or (avg_sentiment < 0 and fvg_signal > 0):
        expected_return *= (2 - FVG_WEIGHT)

    expected_profit_pct = abs(expected_return)

    vol = market_data.get('volatility_hourly', 0.0)
    atr_pct = market_data.get('atr_pct', 0.005)
    # Determine stop loss percent (use ATR for optimized 15m/30m stops)
    stop_pct = max(MIN_STOP_PCT, atr_pct * 1.0)  # 1.0x ATR for tighter stops on 15m/30m

    if stop_pct <= 0:
        return None

    rr = expected_profit_pct / stop_pct if stop_pct > 0 else 0.0

    # decide direction (adjusted thresholds for short trades)
    direction = 'flat'
    if expected_return > 0.0005:  # 0.05% for long
        direction = 'long'
    elif expected_return < -0.0002:  # Lower threshold for short to allow more shorts
        direction = 'short'

    # For bearish Ichimoku or candle, allow short even if sentiment neutral
    if direction == 'flat' and ichimoku_signal == -1:
        direction = 'short'
        expected_return = -0.001  # Set small negative
        expected_profit_pct = 0.001
    elif direction == 'flat' and candle_signal == -1 and avg_sentiment < 0.1:
        direction = 'short'
        expected_return = -0.001
        expected_profit_pct = 0.001

    lev = recommend_leverage(rr, vol, kind='crypto')

    return {
        'direction': direction,
        'expected_return_pct': expected_return,
        'expected_profit_pct': expected_profit_pct,
        'stop_pct': stop_pct,
        'rr': rr,
        'recommended_leverage': lev,
        'volatility_hourly': vol,
        'atr_pct': atr_pct,
        'pivot': pivot,
        'r1': r1, 'r2': r2,
        's1': s1, 's2': s2,
        'support': support,
        'resistance': resistance,
        'psych_level': psych_level,
        'candle_signal': candle_signal,
        'ichimoku_signal': ichimoku_signal,
        'volume_signal': volume_signal,
        'fvg_signal': fvg_signal,
    }

# --- ADD this helper anywhere above main() ---
@lru_cache(maxsize=2048)
def _symbol_has_prices(yf_symbol: str) -> bool:
    """Fast sanity check: does yfinance return any recent daily history?"""
    try:
        hist = yf.Ticker(yf_symbol).history(period='30d', interval='1d')
        return (not hist.empty) and (len(hist['Close'].dropna()) >= 5)
    except Exception:
        return False

def log_trades(results):
    """Log suggested trades to JSON file with indicator signals."""
    if not os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, 'w') as f:
            json.dump([], f)
    
    with open(TRADE_LOG_FILE, 'r') as f:
        logs = json.load(f)
    
    for r in results:
        price = r['price']
        direction = r['direction']
        stop_pct = r['stop_pct']
        exp_return_pct = r['expected_return_pct']
        if direction == 'long':
            stop_price = price * (1 - stop_pct)
            target_price = price * (1 + exp_return_pct)
        elif direction == 'short':
            stop_price = price * (1 + stop_pct)
            target_price = price * (1 - exp_return_pct)
        else:
            continue  # Skip flat
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': r['symbol'],
            'direction': direction,
            'entry_price': price,
            'stop_price': stop_price,
            'target_price': target_price,
            'leverage': r['recommended_leverage'],
            'status': 'open',
            'candle_signal': r['candle_signal'],
            'ichimoku_signal': r['ichimoku_signal'],
            'volume_signal': r['volume_signal'],
            'fvg_signal': r['fvg_signal']
        }
        logs.append(trade)
    
    with open(TRADE_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def evaluate_trades():
    """Evaluate past trades and adjust indicator weights based on performance."""
    global ICHIMOKU_WEIGHT, VOLUME_WEIGHT, FVG_WEIGHT, CANDLE_WEIGHT, NEW_TECHNIQUE_ENABLED
    if not os.path.exists(TRADE_LOG_FILE):
        return
    
    with open(TRADE_LOG_FILE, 'r') as f:
        logs = json.load(f)
    
    indicator_wins = {'candle': 0, 'ichimoku': 0, 'volume': 0, 'fvg': 0}
    indicator_losses = {'candle': 0, 'ichimoku': 0, 'volume': 0, 'fvg': 0}
    total_wins = 0
    total = 0
    
    for trade in logs:
        if trade['status'] != 'open':
            continue
        symbol = trade['symbol']
        yf_symbol = CRYPTO_SYMBOL_MAP.get(symbol, symbol + '-USD')
        try:
            ticker = yf.Ticker(yf_symbol)
            current_price = float(ticker.history(period='1d')['Close'].iloc[-1])
        except:
            continue
        direction = trade['direction']
        stop = trade['stop_price']
        target = trade['target_price']
        win = False
        if direction == 'long':
            if current_price >= target:
                trade['status'] = 'win'
                win = True
                total_wins += 1
            elif current_price <= stop:
                trade['status'] = 'loss'
        elif direction == 'short':
            if current_price <= target:
                trade['status'] = 'win'
                win = True
                total_wins += 1
            elif current_price >= stop:
                trade['status'] = 'loss'
        total += 1
        
        # Track indicator performance
        for ind in ['candle', 'ichimoku', 'volume', 'fvg']:
            signal = trade[f'{ind}_signal']
            if win:
                if (direction == 'long' and signal > 0) or (direction == 'short' and signal < 0):
                    indicator_wins[ind] += 1
            else:
                if (direction == 'long' and signal > 0) or (direction == 'short' and signal < 0):
                    indicator_losses[ind] += 1
    
    if total > 0:
        win_rate = total_wins / total
        print(f"Evaluated {total} trades, win rate: {win_rate:.2%}")
        
        # Adjust weights per indicator
        for ind in ['candle', 'ichimoku', 'volume', 'fvg']:
            wins = indicator_wins[ind]
            losses = indicator_losses[ind]
            if wins + losses > 0:
                ind_win_rate = wins / (wins + losses)
                if ind_win_rate > 0.6:
                    globals()[f'{ind.upper()}_WEIGHT'] *= 1.1  # Boost good performers
                elif ind_win_rate < 0.4:
                    globals()[f'{ind.upper()}_WEIGHT'] *= 0.9  # Reduce bad performers
                if globals()[f'{ind.upper()}_WEIGHT'] < 1.0:
                    globals()[f'{ind.upper()}_WEIGHT'] = 1.0  # Neutralize underperformers
                print(f"{ind.capitalize()} win rate: {ind_win_rate:.2%}, new weight: {globals()[f'{ind.upper()}_WEIGHT']:.2f}")
        
        # Adjust overall parameters if win rate < 30%
        if win_rate < 0.3:
            global EXPECTED_RETURN_PER_SENTIMENT, MIN_STOP_PCT
            MIN_STOP_PCT *= 0.9
            print("Adjusted: tighter stops due to low win rate (<30%).")
            # Enable new technique if overall poor
            NEW_TECHNIQUE_ENABLED = True
            print("Enabled new technique placeholder due to low performance.")
        
        # Save back
        with open(TRADE_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)

def main():
    print('Crypto News Trading Bot v2.0 - Fetching latest signals...')
    
    # Check market session
    session_info = get_market_session()
    print(f"Current Market Session: {session_info['session']} (Multiplier: {session_info['multiplier']:.2f})")
    print(f"Trading Status: {'Allowed' if session_info['allow_trading'] else 'Skipped'} - {session_info['reason']}")
    
    # Skip trading during weekends or when trading is not allowed
    if not session_info['allow_trading']:
        message = f"Trading skipped: {session_info['reason']}"
        print(message)
        send_telegram_message(message)
        return []
    
    articles = get_news()
    print(f'Retrieved {len(articles)} articles.')

    # Group articles mentioning each symbol

    # Group articles mentioning each symbol
    symbol_articles = {}
    for a in articles:
        title = a.get('title') or ''
        desc = a.get('description') or ''
        text = f'{title} {desc}'.strip()
        if not text:
            continue
        hits = extract_crypto_and_tickers(text)
        for h in hits:
            key = h['symbol']
            symbol_articles.setdefault(key, {'yf': h['yf'], 'kind': h['kind'], 'texts': [], 'count': 0})
            symbol_articles[key]['texts'].append(text)
            symbol_articles[key]['count'] += 1

    results = []
    print('Analyzing candidates...')
    for sym, info in symbol_articles.items():
        texts = info['texts']
        avg_sent = analyze_sentiment(texts)
        news_count = info['count']
        yf_symbol = info['yf']
        kind = info['kind']

        market = get_market_data(yf_symbol, kind=kind)
        if not market:
            continue

        plan = calculate_trade_plan(avg_sent, news_count, market, session_multiplier=session_info['multiplier'])
        if not plan:
            continue

        # Only keep actionable plans
        if plan['direction'] == 'flat' or plan['rr'] < 0.5:
            continue
# --- OPTIONAL safety in main() loop, just before get_market_data(...) ---
        # Skip unknown/price-less stock-like tickers defensively
        if kind == 'stock' and not _symbol_has_prices(yf_symbol):
            continue

        # Low money adjustments: if entry * leverage < $100, boost ROI and leverage for better R/R
        entry_cost = market['price'] * plan['recommended_leverage']
        if entry_cost < 100:
            plan['expected_return_pct'] *= 1.5  # Higher ROI
            plan['expected_profit_pct'] *= 1.5
            plan['recommended_leverage'] = min(plan['recommended_leverage'] * 2, MAX_LEVERAGE_CRYPTO)  # Higher leverage
            plan['stop_pct'] *= 0.7  # Tighter stops for better R/R
            plan['rr'] = plan['expected_profit_pct'] / plan['stop_pct'] if plan['stop_pct'] > 0 else 0

        results.append({
            'symbol': sym,
            'yf_symbol': yf_symbol,
            'kind': kind,
            'avg_sentiment': avg_sent,
            'news_count': news_count,
            'price': market['price'],
            'volatility_hourly': market['volatility_hourly'],
            'atr_pct': market['atr_pct'],
            'pivot': market['pivot'],
            'r1': market['r1'], 'r2': market['r2'],
            's1': market['s1'], 's2': market['s2'],
            'support': market['support'],
            'resistance': market['resistance'],
            'psych_level': market['psych_level'],
            'candle_signal': market['candle_signal'],
            'ichimoku_signal': market['ichimoku_signal'],
            'volume_signal': market['volume_signal'],
            'fvg_signal': market['fvg_signal'],
            **plan
        })

    # sort by quality: rr then news_count
    results.sort(key=lambda r: (r['rr'], r['news_count']), reverse=True)

    if not results:
        message = 'No actionable crypto trades found at this time.'
        print(message)
        send_telegram_message(message)
        return []

    message = f"Market Session: {session_info['session']} (Volatility Multiplier: {session_info['multiplier']:.2f})\n"
    message += f"Recommended trades:\nGenerated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | Total articles: {len(articles)} | Candidates analyzed: {len(symbol_articles)}\n"
    print('\nRecommended trades:')
    print(f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | Total articles: {len(articles)} | Candidates analyzed: {len(symbol_articles)}")
    for r in results:
        price = r['price']
        direction = r['direction']
        stop_pct = r['stop_pct']
        exp_return_pct = r['expected_return_pct']
        if direction == 'long':
            stop_price = price * (1 - stop_pct)
            target_price = price * (1 + exp_return_pct)
        elif direction == 'short':
            stop_price = price * (1 + stop_pct)
            target_price = price * (1 - exp_return_pct)
        else:
            stop_price = price
            target_price = price
        trade_line = f"Symbol: {r['symbol']} | Direction: {r['direction'].upper()} | Entry Price: {r['price']:.4f} | Stop Loss: {stop_price:.4f} | Take Profit: {target_price:.4f} | Leverage: {r['recommended_leverage']}"
        message += trade_line + "\n"
        print(trade_line)

    send_telegram_message(message)
    
    # Log trades
    log_trades(results)
    
    # Evaluate and learn every run
    evaluate_trades()
    
    return results


if __name__ == '__main__':
    main()
