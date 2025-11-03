# Simple Python Trader

A Python script that analyzes cryptocurrency news from various sources, performs sentiment analysis, and suggests trading opportunities based on technical indicators and market data.

## Description

This tool fetches recent news articles related to cryptocurrencies from NewsAPI and multiple RSS feeds (e.g., CoinDesk, Cointelegraph, The Block, etc.). It identifies mentioned cryptocurrencies, analyzes the sentiment of the articles using TextBlob, retrieves real-time market data via yfinance, and calculates potential trade plans including direction (long/short), stop loss, take profit, and recommended leverage.

Recommendations are printed to the console and optionally sent via Telegram bot.

## Features

- **News Aggregation**: Collects articles from NewsAPI and RSS feeds from prominent crypto news sources.
- **Cryptocurrency Detection**: Automatically identifies cryptocurrencies mentioned in news (supports BTC, ETH, DOGE, SHIB, SOL, ADA, XRP, LTC, BNB, LINK, AVAX, MATIC, DOT, UNI, AAVE, SUSHI, CAKE, LUNA, ATOM, ALGO, VET, ICP, FIL, TRX, ETC, XLM, THETA, FTT, HBAR, NEAR, FLOW, MANA, SAND, AXS, CHZ, ENJ, BAT, OMG, ZRX, REP, GNT, STORJ, ANT, MKR, COMP, YFI, BAL, REN, LRC, KNC, ZKS, IMX, APE, GMT, GAL, OP, ARB, PEPE, FLOKI, BONK, WIF, MEW, POPCAT, TURBO, BRETT, MOTHER, CUMMIES, SLERF, GOAT, WEN, PUMP, SMOG).
- **Sentiment Analysis**: Uses TextBlob for polarity scoring of news sentiment.
- **Market Data Integration**: Fetches 15-minute interval data from yfinance, including price, volatility, ATR, pivot points, support/resistance levels, psychological levels, candle patterns, and Ichimoku Cloud signals.
- **Trade Calculation**: Generates trade plans with expected returns, stop losses, risk-reward ratios, and leverage recommendations (up to 20x for crypto).
- **Telegram Notifications**: Sends trade suggestions via Telegram if configured.
- **Filtering and Safety**: Filters out low-volume or delisted assets, and only suggests trades with reasonable risk-reward ratios.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/rqzbeh/simple-python-trader.git
   cd simple-python-trader
   ```

2. Install the required Python packages:
   ```
   pip install requests newsapi-python yfinance textblob
   ```

3. Set up environment variables:
   - `NEWS_API_KEY`: Obtain a free API key from [NewsAPI](https://newsapi.org/).
   - (Optional) `TELEGRAM_BOT_TOKEN`: Create a Telegram bot via [BotFather](https://t.me/botfather) and get the token.
   - (Optional) `TELEGRAM_CHAT_ID`: Find your chat ID by messaging the bot and checking updates.

   Example:
   ```
   export NEWS_API_KEY='your_news_api_key_here'
   export TELEGRAM_BOT_TOKEN='your_bot_token_here'
   export TELEGRAM_CHAT_ID='your_chat_id_here'
   ```

## Usage

Run the script:
```
python main.py
```

The script will:
- Fetch recent news (last 48 hours).
- Analyze cryptocurrencies mentioned.
- Compute trade suggestions.
- Print recommendations to the console.
- Send a summary via Telegram if configured.

Example output:
```
Recommended trades:
Generated at 2025-11-03 21:27:15 | Total articles: 150 | Candidates analyzed: 25
Symbol: BTC | Direction: LONG | Entry Price: 95000.0000 | Stop Loss: 94500.0000 | Take Profit: 95250.0000 | Leverage: 5
...
```

## Configuration

- **Risk Settings**: Adjust parameters like `MIN_STOP_PCT`, `EXPECTED_RETURN_PER_SENTIMENT`, `MAX_LEVERAGE_CRYPTO` in the script for customization.
- **News Sources**: Modify `CRYPTO_RSS_FEEDS` to add or remove RSS sources.
- **Cryptocurrency Map**: Extend `CRYPTO_SYMBOL_MAP` and `CRYPTO_ALIASES` for more assets.

## Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Cryptocurrency trading involves significant risk of loss. Always do your own research and consider consulting a financial advisor. The developers are not responsible for any trading losses incurred.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.