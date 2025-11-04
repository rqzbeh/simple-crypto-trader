# Simple Python Trader

A Python script that analyzes cryptocurrency news from various sources, performs sentiment analysis, and suggests trading opportunities based on technical indicators, smart money concepts, and ICT methodology.

## Description

This tool fetches recent news articles related to cryptocurrencies from NewsAPI and multiple RSS feeds (e.g., CoinDesk, Cointelegraph, The Block, etc.). It identifies mentioned cryptocurrencies, analyzes sentiment, and integrates market data including technical indicators, smart money volume analysis, and ICT elements like Fair Value Gaps.

It calculates trade plans with expected returns, stop losses, risk-reward ratios, and leverage recommendations. Suggestions include both long and short positions based on sentiment and technical confirmations. For low-capital traders, it adjusts parameters for higher ROI and better R/R, including a longer timeframe to reduce fees.

The bot includes a learning mechanism: it logs all suggestions, evaluates their real-world performance (win/loss rates), and self-adjusts indicator weights and parameters to optimize over time. It also considers current market sessions to adjust trading behavior, boosting activity during peak hours and reducing during off-hours or weekends.

Recommendations are printed to the console and optionally sent via Telegram bot.

## Features

- **News Aggregation**: Collects articles from NewsAPI and RSS feeds from prominent crypto news sources.
- **Cryptocurrency Detection**: Automatically identifies cryptocurrencies mentioned in news (supports BTC, ETH, DOGE, SHIB, SOL, ADA, XRP, LTC, BNB, LINK, AVAX, MATIC, DOT, UNI, AAVE, SUSHI, CAKE, LUNA, ATOM, ALGO, VET, ICP, FIL, TRX, ETC, XLM, THETA, FTT, HBAR, NEAR, FLOW, MANA, SAND, AXS, CHZ, ENJ, BAT, OMG, ZRX, REP, GNT, STORJ, ANT, MKR, COMP, YFI, BAL, REN, LRC, KNC, ZKS, IMX, APE, GMT, GAL, OP, ARB, PEPE, FLOKI, BONK, WIF, MEW, POPCAT, TURBO, BRETT, MOTHER, CUMMIES, SLERF, GOAT, WEN, PUMP, SMOG).
- **Sentiment Analysis**: Uses TextBlob for polarity scoring of news sentiment, boosted for influential sources.
- **Market Data Integration**: Fetches 15-minute or 30-minute interval data from yfinance (30m for low-money mode), including price, volatility, ATR, pivot points, support/resistance levels, psychological levels, candle patterns, Ichimoku Cloud, smart money volume signals, and ICT Fair Value Gaps.
- **Smart Money Concepts**: Analyzes volume to detect institutional order flow, boosting signals aligned with smart money moves.
- **ICT Methodology**: Incorporates Fair Value Gap detection for liquidity imbalances, enhancing trade confirmations.
- **Trade Calculation**: Generates trade plans with expected returns, stop losses, risk-reward ratios, and leverage recommendations (up to 100x for crypto). Supports both long and short directions.
- **Low Money Trading**: Automatically adjusts for small accounts (entry cost < $100) with higher ROI, increased leverage, tighter stops for better R/R, and 30m timeframe to minimize fees.
- **Learning Mechanism**: Logs all suggested trades to a JSON file, evaluates performance (win/loss rates), and self-adjusts indicator weights (e.g., boosting Ichimoku if it wins >60%) and parameters (e.g., tighter stops if win rate <30%) to optimize over time. Can neutralize underperforming indicators.
- **Market Session Awareness**: Detects current global market sessions (Sydney, Tokyo, London, New York) based on UTC time and adjusts expected returns (boosting 20% during active sessions like London/New York, reducing 10% during off-hours), skips trades entirely on weekends for low liquidity.
- **Telegram Notifications**: Sends trade suggestions via Telegram if configured.
- **Filtering and Safety**: Filters out low-volume or delisted assets, and only suggests trades with reasonable risk-reward ratios.

## Installation

1. Clone the repository:
