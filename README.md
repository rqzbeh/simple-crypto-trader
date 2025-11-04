# Simple Python Trader

A Python script that analyzes cryptocurrency news from various sources, performs sentiment analysis, and suggests trading opportunities based on technical indicators, smart money concepts, and ICT methodology.

## Description

This tool fetches recent news articles related to cryptocurrencies from NewsAPI and multiple RSS feeds (e.g., CoinDesk, Cointelegraph, The Block, etc.). It identifies mentioned cryptocurrencies, analyzes sentiment, and integrates market data including technical indicators, smart money volume analysis, and ICT elements like Fair Value Gaps.

It calculates trade plans with expected returns, stop losses, risk-reward ratios, and leverage recommendations. Suggestions include both long and short positions based on sentiment and technical confirmations. For low-capital traders, it adjusts parameters for higher ROI and better R/R, including a longer timeframe to reduce fees.

The bot includes a learning mechanism: it logs all suggestions, evaluates their real-world performance (win/loss rates), and self-adjusts indicator weights and parameters to optimize over time.

Recommendations are printed to the console and optionally sent via Telegram bot.

## Features

- **News Aggregation**: Collects articles from NewsAPI and RSS feeds from prominent crypto news sources.
- **Cryptocurrency Detection**: Automatically identifies cryptocurrencies mentioned in news (supports BTC, ETH, DOGE, SHIB, SOL, ADA, XRP, LTC, BNB, LINK, AVAX, MATIC, DOT, UNI, AAVE, SUSHI, CAKE, LUNA, ATOM, ALGO, VET, ICP, FIL, TRX, ETC, XLM, THETA, FTT, HBAR, NEAR, FLOW, MANA, SAND, AXS, CHZ, ENJ, BAT, OMG, ZRX, REP, GNT, STORJ, ANT, MKR, COMP, YFI, BAL, REN, LRC, KNC, ZKS, IMX, APE, GMT, GAL, OP, ARB, PEPE, FLOKI, BONK, WIF, MEW, POPCAT, TURBO, BRETT, MOTHER, CUMMIES, SLERF, GOAT, WEN, PUMP, SMOG).
- **Sentiment Analysis**: Uses TextBlob for polarity scoring of news sentiment, boosted for influential sources.
- **Market Session Awareness**: Detects current market session (Sydney, Tokyo, London, New York) based on UTC time and adjusts expected returns accordingly:
  - **New York Session** (1PM-10PM UTC): +20% expected return boost for higher volatility and trading volume
  - **London Session** (8AM-4PM UTC): +15% expected return boost for active trading
  - **Tokyo Session** (12AM-9AM UTC): Neutral (no adjustment)
  - **Sydney Session** (10PM-7AM UTC): -5% expected return reduction for lower volume
  - **Off-Hours**: -15% expected return reduction for minimal activity
  - **Weekend Trading**: Completely skipped (Saturday-Sunday)
- **Market Data Integration**: Fetches 15-minute or 30-minute interval data from yfinance (30m for low-money mode), including price, volatility, ATR, pivot points, support/resistance levels, psychological levels, candle patterns, Ichimoku Cloud, smart money volume signals, and ICT Fair Value Gaps.
- **Smart Money Concepts**: Analyzes volume to detect institutional order flow, boosting signals aligned with smart money moves.
- **ICT Methodology**: Incorporates Fair Value Gap detection for liquidity imbalances, enhancing trade confirmations.
- **Trade Calculation**: Generates trade plans with expected returns, stop losses, risk-reward ratios, and leverage recommendations (up to 100x for crypto). Supports both long and short directions.
- **Low Money Trading**: Automatically adjusts for small accounts (entry cost < $100) with higher ROI, increased leverage, tighter stops for better R/R, and 30m timeframe to minimize fees. Works seamlessly with market session awareness.
- **Learning Mechanism**: Logs all suggested trades to a JSON file, evaluates performance (win/loss rates), and self-adjusts indicator weights (e.g., boosting Ichimoku if it wins >60%) and parameters (e.g., tighter stops if win rate <30%) to optimize over time. Can neutralize underperforming indicators.
- **Telegram Notifications**: Sends trade suggestions via Telegram if configured, including current market session information.
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
- Detect the current market session and check if trading is allowed.
- Skip trading entirely on weekends or during configured off-hours.
- Fetch recent news (last 48 hours).
- Analyze cryptocurrencies mentioned.
- Compute trade suggestions (long/short) with session-adjusted expected returns.
- Log suggestions and evaluate past performance for learning.
- Print recommendations to the console with session information.
- Send a summary via Telegram if configured.

Example output:
```
Crypto News Trading Bot v2.0 - Fetching latest signals...
Current Market Session: New York (Multiplier: 1.20)
Trading Status: Allowed - New York session active
Retrieved 150 articles.
Analyzing candidates...

Recommended trades:
Market Session: New York (Volatility Multiplier: 1.20)
Generated at 2025-11-04 17:27:15 UTC | Total articles: 150 | Candidates analyzed: 25
Symbol: BTC | Direction: LONG | Entry Price: 95000.0000 | Stop Loss: 94500.0000 | Take Profit: 95250.0000 | Leverage: 5
Symbol: ETH | Direction: SHORT | Entry Price: 3200.0000 | Stop Loss: 3232.0000 | Take Profit: 3168.0000 | Leverage: 3
...
Evaluated 20 trades, win rate: 65.0%
Ichimoku win rate: 70.0%, new weight: 1.32
```

Example weekend output:
```
Crypto News Trading Bot v2.0 - Fetching latest signals...
Current Market Session: Weekend (Multiplier: 0.00)
Trading Status: Skipped - Weekend - Markets closed
Trading skipped: Weekend - Markets closed
```

## Configuration

- **Risk Settings**: Adjust parameters like `MIN_STOP_PCT`, `EXPECTED_RETURN_PER_SENTIMENT`, `MAX_LEVERAGE_CRYPTO` in the script for customization.
- **Low Money Mode**: Set `LOW_MONEY_MODE = True` at the top of main.py to enable adjustments for low-capital trading and 30m timeframe.
- **Learning Logs**: Check `trade_log.json` for logged trades and their statuses. The bot evaluates and adjusts after each run.
- **News Sources**: Modify `CRYPTO_RSS_FEEDS` to add or remove RSS sources.
- **Cryptocurrency Map**: Extend `CRYPTO_SYMBOL_MAP` and `CRYPTO_ALIASES` for more assets.

## Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Cryptocurrency trading involves significant risk of loss. Always do your own research and consider consulting a financial advisor.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
