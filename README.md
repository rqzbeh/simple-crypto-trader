# 🚀 Simple Crypto Trader

**News-Driven Cryptocurrency Trading Signal Generator**

An intelligent cryptocurrency trading signal generator that combines news sentiment analysis, AI-powered market reasoning, and technical indicators to identify high-probability trading opportunities. Built for 24/7 crypto markets with short-term trades (2-4 hours maximum duration).

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 Key Features

### 📰 News-Driven Trading Strategy
- **Primary Signals**: News sentiment analysis combined with AI/LLM market reasoning
- **Technical Validation**: Technical indicators filter and validate trading setups
- **Multi-Source Data**: Aggregates news from NewsAPI and RSS feeds (CoinDesk, Cointelegraph, etc.)
- **Real-Time Analysis**: 6-8 hour news lookback window for fresh, relevant market context
- **Smart Execution**: Technical indicators calculate precise entry, stop loss, and take profit levels

### ⚡ Short-Term Trading Optimization
- **Trade Duration**: 2-4 hours maximum for quick entries and exits
- **Tight Risk Management**: 0.8%-2.5% stop loss range
- **Achievable Targets**: Maximum 7.5% take profit (realistic for 2-4h timeframe)
- **Minimum 1:3 Risk/Reward**: Enforced minimum ratio, can be higher for strong signals
- **Fresh News Context**: 6-8 hour lookback ensures news relevance

### 🎯 Dynamic Position Sizing
- **Leverage Range**: 2x minimum, 10x maximum
- **Dynamic Calculation**: Leverage = floor(R/R + confidence×5)
- **Tight Stops**: 0.8%-2.5% stop loss enables higher leverage safely
- **ATR-Based Stops**: Volatility-adjusted risk management

### 🤖 Hybrid Intelligence System
- **10 Optimized Indicators**: Conflict-free technical analysis
- **AI Market Analysis**: Groq LLM (Llama 3.3) interprets market context and psychology
- **Adaptive Learning**: Self-adjusts parameters based on historical performance
- **Precision Tracking**: Monitors entry timing, stop loss, and take profit accuracy
- **Performance-Based**: Automatically adjusts strategy based on trade outcomes

### 📊 Technical Excellence
- **Proven Indicators**: Stochastic RSI, EMA, MACD, Bollinger Bands, VWAP, Supertrend, ADX
- **No Redundancy**: Each indicator serves a unique purpose
- **No Conflicts**: All indicators are independent and complementary
- **Real-Time Data**: yfinance integration for live price feeds

---

## 📈 Trading Philosophy

### Signal Generation Approach

**Primary Sources (85-90%):**
- News sentiment analysis from multiple sources
- AI/LLM market context interpretation
- Market psychology and sentiment detection
- Risk assessment and opportunity identification

**Technical Validation (10-15%):**
- Filters out contradictory setups
- Calculates precise entry, stop loss, and take profit levels
- Validates trend strength and momentum
- Adjusts confidence based on technical alignment

### Risk/Reward Framework

**Minimum 1:3 R/R Enforced:**
```
Risk: 0.8-2.5% stop loss
Reward: 2.4-7.5% take profit
MINIMUM R/R: 1:3 (strictly enforced)
ACTUAL R/R: Often 4:1, 5:1, or 6:1+ for strong signals
Break-even Win Rate: 25% (at 3:1 R/R)
Target Win Rate: 40-50%
Trade Duration: 2-4 hours maximum
```

**Example Trade (3:1 R/R):**
```
BTC Entry: $50,000
Stop Loss: $49,500 (1.0% = $500 risk)
Take Profit: $51,500 (3.0% = $1,500 gain)
R/R Ratio: 1:3.0
Leverage: 7x
Confidence: 82%
Duration: 2-4 hours

Potential Win: $1,500 × 7 = $10,500 profit
Potential Loss: $500 × 7 = $3,500 loss
```

**Example Strong Signal (6:1 R/R):**
```
ETH Entry: $3,000
Stop Loss: $2,988 (0.8% = $24 risk)
Take Profit: $3,144 (4.8% = $144 gain)
R/R Ratio: 1:6.0
Leverage: 8x
Confidence: 91%
Duration: 2-4 hours

Potential Win: $144 × 8 = $1,152 profit
Potential Loss: $24 × 8 = $192 loss
```

---

## 🎮 Quick Start

### Prerequisites
- Python 3.8 or higher
- API keys for NewsAPI and Groq

### Installation

```bash
# Clone the repository
git clone https://github.com/rqzbeh/simple-crypto-trader.git
cd simple-crypto-trader

# Install required dependencies
pip install -r requirements.txt
```

### Configuration

Set up your API keys as environment variables:

```bash
# Required API Keys
export NEWS_API_KEY='your_newsapi_key'      # Get from https://newsapi.org
export GROQ_API_KEY='your_groq_api_key'     # Get from https://console.groq.com

# Optional: Telegram Notifications
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

### Running the Bot

**Single Run:**
```bash
python main.py
```

**Scheduled Execution (Recommended):**

The bot works perfectly with crontab for automated trading. It tracks trades across multiple runs and only trains on completed trades.

```bash
# Edit crontab
crontab -e

# Add this line to run every 2 hours (recommended)
0 */2 * * * cd /path/to/simple-crypto-trader && /usr/bin/python3 main.py >> logs/trader.log 2>&1
```

**Why 2-hour intervals?**
- Allows trades to develop naturally
- Checks progress mid-window
- Respects 2-4 hour trade duration
- Efficient balance between responsiveness and API usage

---

## 🔧 Technical Indicators

The system uses 10 optimized, conflict-free technical indicators:

### Core Indicators

1. **Stochastic RSI** (Weight: 2.5)
   - Primary momentum indicator
   - Most sensitive for crypto volatility
   - Signal: <20 oversold, >80 overbought

2. **EMA Trend** (Weight: 2.3)
   - Multi-timeframe trend direction (9, 21, 50, 200 EMAs)
   - Signal: All EMAs aligned = strong trend

3. **MACD** (Weight: 2.0)
   - Convergence/divergence momentum
   - Signal: Histogram crossing zero

4. **Supertrend** (Weight: 1.9)
   - Volatility-adjusted trend following
   - Uses ATR for dynamic adjustments
   - Signal: Price above/below band

5. **ADX** (Weight: 1.8)
   - Trend strength measurement
   - Signal: >25 = tradeable trend strength

6. **Bollinger Bands** (Weight: 2.0)
   - Volatility and price range measurement
   - Signal: Position in bands (<10% or >90%)

7. **ATR** (No directional weight)
   - Used for stop-loss calculation
   - 1.5× ATR for stop distance

8. **OBV** (Weight: 1.7)
   - Volume-based accumulation/distribution
   - Signal: Above/below 20-period average

9. **VWAP** (Weight: 2.1)
   - Institutional price levels
   - Critical for crypto markets
   - Signal: Price above/below VWAP

10. **Pivot Points** (Weight: 1.5)
    - Classical support/resistance levels
    - Signal: Price near key levels

---

## 🤖 AI Integration

### LLM-Powered Market Analysis

The system leverages Groq's Llama 3.3 for advanced market interpretation:
- Market context and psychology analysis
- Risk assessment (LOW/MEDIUM/HIGH)
- Timeframe recommendations
- Trading rationale generation

### Hybrid Decision Making

```
Signal Generation = News Sentiment + AI Analysis + Technical Validation

Primary Layer: News Sentiment (40%) + LLM Reasoning (50%)
Validation Layer: Technical Indicators (10% - filters contradictions)

Agreement Boost: +5% confidence when all methods align
```

### Adaptive Learning System

The bot continuously learns from its trading history:

**Performance Tracking:**
- Monitors win rate from last 20 trades
- Tracks take profit precision separately from direction accuracy
- Learns actual price movements within 2-4 hour timeframe

**Auto-Adjustment:**
- **Entry Timing**: Adjusts entry calculation based on how often entry prices are reached
- **Stop Loss**: Widens or tightens stops based on premature stop-out frequency
- **Take Profit**: Scales targets based on historical achievement rate (0.6x-1.2x multiplier)
- **Confidence Thresholds**: Dynamically adjusted based on overall performance
- **Indicator Weights**: Optimizes weights based on historical accuracy

**Precision Learning:**
The system distinguishes between different failure types:
- Wrong direction → Adjusts signal generation confidence
- Correct direction but TP too far → Reduces TP targets
- TP too conservative → Gradually increases targets
- SL hit too early → Widens stop loss range

Example: If BTC consistently moves 2% but predictions are 3%, future targets adjust to 2.1%.

---

## 💰 Risk Management

### Stop Loss Strategy
```python
Base Stop = 0.8% minimum (suitable for short-term trades)
ATR Stop = 1.2× ATR percentage (volatility-adjusted)
Final Stop = max(Base, min(ATR, 2.5%))  # Capped at 2.5% maximum
Range = 0.8% to 2.5% (maintains minimum 1:3 R/R)
```

### Leverage Calculation
```python
R/R = Take Profit % / Stop Loss %
Confidence = 0 to 1 (signal strength)
Leverage = floor(R/R + Confidence × 5)
Maximum = 10x
Minimum = 2x
```

### Take Profit Strategy
```python
Expected Return = Sentiment Score × 4-5% (realistic for 2-4h)
News Bonus = News Count × 1.5-1.8% (max 5-6%)
Minimum TP = Stop Loss × 3 (enforces 1:3 minimum R/R)
Maximum TP = 7.5% (realistic cap for 2-4h trades)

Strong signals achieve higher R/R naturally:
- Weak signal: 3:1 R/R (minimum enforced)
- Good signal: 4:1 to 5:1 R/R
- Excellent signal: 6:1+ R/R
```

### Position Sizing
- Daily risk limit: 5% of capital
- Per-trade risk: Adjusted by signal confidence
- Minimum R/R: 1:3 (strictly enforced)

---

## 📊 Supported Cryptocurrencies

### Default Analysis (8 cryptocurrencies)
BTC, ETH, BNB, ADA, SOL, DOGE, XRP, MATIC

### Full Support (50+ cryptocurrencies)
Bitcoin, Ethereum, Binance Coin, Cardano, Solana, Dogecoin, XRP, Polkadot, Litecoin, Avalanche, Chainlink, Uniswap, Cosmos, Stellar, Algorand, VeChain, Filecoin, Tron, Ethereum Classic, AAVE, Maker, Compound, Sushi, YFI, Synthetix, Shiba Inu, NEAR, Flow, Decentraland, Sandbox, Axie Infinity, Chiliz, Enjin, BAT, 0x, Loopring, ImmutableX, ApeCoin, Optimism, Arbitrum, PEPE, Floki, and more...

---

## 📁 Project Structure

```
simple-crypto-trader/
├── main.py                    # Core trading bot engine
├── technical_indicators.py    # Technical analysis module
├── llm_analyzer.py           # AI reasoning and market analysis
├── requirements.txt          # Python dependencies
├── trade_log.json           # Trade history (auto-created)
├── learning_state.json      # Adaptive learning data (auto-created)
├── daily_risk.json          # Daily risk tracking (auto-created)
└── README.md                # Documentation
```

---

## 🎯 Configuration Options

### Main Configuration (in `main.py`)

```python
# Data Collection
interval = '1h'               # 1-hour candles for analysis
period = '7d'                 # 7 days of historical data
NEWS_LOOKBACK = 6             # Hours of news to analyze (fresh context)

# Risk Parameters (Short-term 2-4h trades)
MIN_STOP_PCT = 0.008          # 0.8% minimum stop loss
MAX_STOP_PCT = 0.025          # 2.5% maximum stop loss
TARGET_RR_RATIO = 3.0         # 1:3 minimum R/R (can be higher)
MAX_LEVERAGE_CRYPTO = 10      # 10x maximum leverage
MIN_LEVERAGE_CRYPTO = 2       # 2x minimum leverage

# Signal Generation
NEWS_AI_WEIGHT = 0.90         # 90% news/AI driven signals
TECHNICAL_WEIGHT = 0.10       # 10% technical validation
```

### Customization Examples

**More Aggressive:**
```python
MIN_STOP_PCT = 0.010          # 1.0% stops
MAX_LEVERAGE_CRYPTO = 15      # 15x max leverage
TARGET_RR_RATIO = 4.0         # 1:4 minimum target
```

**More Conservative:**
```python
MIN_STOP_PCT = 0.015          # 1.5% stops
MAX_LEVERAGE_CRYPTO = 5       # 5x max leverage
TARGET_RR_RATIO = 2.0         # 1:2 minimum target
```

---

## 📝 Example Output

```
============================================================
🚨 CRYPTO TRADE SIGNAL (SHORT-TERM 2-4H - NEWS DRIVEN)
============================================================
Symbol: BTC
Direction: LONG 🟢
Entry: $67,234.50
Stop Loss: $66,560.97 (1.00%)
Take Profit: $69,247.97 (3.00%)
Leverage: 7x 💪
Risk/Reward: 1:3.0 🎯
Confidence: 82.5%
Duration: 2-4 hours

📊 Analysis:
News Sentiment: 0.68 (PRIMARY)
Technical Validation: PASSED
Strong bullish news momentum with multiple positive articles.
LLM confirms bullish outlook based on market psychology.
Technical indicators support trend (no major contradiction).
Stop loss at 1.0% (ATR-based, tight for 2-4h duration).
Take profit at 3.0% (news-driven, achievable in 2-4h).

⏰ 2025-11-16 17:09:00 UTC | Duration: 2-4H | NEWS-DRIVEN
============================================================
```

---

## 📚 API Setup Guide

### NewsAPI (Required)
1. Visit https://newsapi.org/register
2. Free tier: 100 requests/day
3. Create account and get API key
4. Set environment variable: `export NEWS_API_KEY='your_key'`

### Groq AI (Required)
1. Visit https://console.groq.com/
2. Free tier: 1000 requests/day  
3. Create account and generate API key
4. Set environment variable: `export GROQ_API_KEY='your_key'`

### Telegram Notifications (Optional)
1. Create bot via https://t.me/BotFather
2. Get your chat ID from https://t.me/userinfobot
3. Set environment variables:
   - `export TELEGRAM_BOT_TOKEN='your_bot_token'`
   - `export TELEGRAM_CHAT_ID='your_chat_id'`

---

## 📊 Expected Performance

### Performance Metrics
- **Target Win Rate**: 40-50%
- **Average R/R**: 1:3 to 1:5
- **Signals Per Day**: 2-5 high-quality setups
- **Max Drawdown**: 10-20% with proper position sizing

### Best Practices
1. **Start Small**: Test with minimum capital first
2. **Paper Trade**: Verify strategies work in your environment
3. **Monitor Performance**: Track win rate and adjust parameters
4. **Risk Management**: Never risk more than 5% daily
5. **Diversify**: Don't trade only one cryptocurrency
6. **Be Patient**: Wait for quality 1:3+ setups

---

## ⚠️ Risk Disclaimer

**CRITICAL WARNING:**

❌ This is NOT financial advice
❌ NO guarantee of profits
❌ High risk of loss possible
❌ Can lose entire investment

✅ Educational and research tool only
✅ Test with small amounts first
✅ Never risk more than you can afford to lose
✅ Consult a licensed financial advisor before trading

**Cryptocurrency trading is extremely risky. Past performance does not guarantee future results. The authors are NOT responsible for any financial losses.**

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional non-conflicting indicators
- Enhanced LLM prompts and reasoning
- Backtesting framework
- Paper trading mode
- Web dashboard interface
- Mobile notifications
- Multi-exchange integration

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **yfinance**: Market data provider
- **Groq**: Fast LLM inference platform
- **NewsAPI**: News aggregation service
- Cryptocurrency trading community

---

<div align="center">

**Built for Cryptocurrency Traders** 🚀

[⭐ Star](https://github.com/rqzbeh/simple-crypto-trader) • [🐛 Issues](https://github.com/rqzbeh/simple-crypto-trader/issues) • [💡 Discussions](https://github.com/rqzbeh/simple-crypto-trader/discussions)

</div>
