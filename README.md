# 🚀 Simple Crypto Trader

**📰 NEWS-DRIVEN Cryptocurrency Trading Signal Generator**

A sophisticated crypto trading bot that **trades primarily based on news, sentiment, and AI analysis**, with technical indicators serving as filters to validate setups. Built for 24/7 crypto markets with 3-hour timeframe optimization.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 Key Features

### 📰 NEWS-DRIVEN Trading Strategy
- **Primary Signals (70-80%)**: News sentiment + AI/LLM analysis
- **Technical Filters (20-30%)**: Validate and filter out bad setups
- **News Impact**: Up to 12% expected return based on news volume
- **Real-Time Analysis**: Multi-source news aggregation with AI reasoning

### ⚡ 3-Hour Timeframe Optimization
- **Perfect Balance**: Filters noise while keeping signals timely
- **News Validity**: 6-hour lookback (2x timeframe) for relevant context
- **Tighter Stops**: 1.2% minimum (vs 2% for 1h) - less noise allows precision
- **Better R/R**: Consistent 1:3 minimum risk/reward ratios

### 🎯 Aggressive But Smart
- **10x Max Leverage**: 3h timeframes justify higher leverage
- **2x Minimum Leverage**: Take advantage of clear trends
- **Dynamic Sizing**: Leverage = floor(R/R + confidence×5)
- **Risk Management**: 5% daily loss limit, ATR-based stops

### 🤖 Hybrid Intelligence
- **10 Optimized Indicators**: No conflicts, serve as filters only
- **AI Reasoning**: Groq LLM analyzes market like a human trader
- **Adaptive Learning**: Self-adjusts based on performance
- **70/30 Balance**: 70% news/AI, 30% technical filter

### 📊 Technical Excellence
- **Conflict-Free**: Removed 7 redundant indicators
- **Proven Methods**: Stoch RSI, EMA, MACD, Bollinger Bands, VWAP
- **Filter Purpose**: Technicals validate news signals, don't generate them
- **Real-Time Data**: yfinance integration for live prices

---

## 📰 News Trading Philosophy

### Primary Signal Sources (70-80%)
1. **News Sentiment Analysis**
   - Multi-source aggregation (CoinDesk, Cointelegraph, etc.)
   - 6-hour validity window for relevance
   - Weighted by article count and quality

2. **AI/LLM Analysis** 
   - Groq's Llama 3.1 for market context
   - Risk assessment and reasoning
   - Detects market psychology and sentiment

### Technical Filters (20-30%)
- **Not signal generators** - only validate/filter
- Strong technical contradiction → Signal filtered out
- Weak technical support → Confidence reduced
- Strong technical agreement → Confidence boost

---

## 📈 Performance Strategy

### Why News-Driven Approach?

| Factor | Technical-Only | **News-Driven** | Advantage |
|--------|---------------|-----------------|-----------|
| Signal Source | Lagging | ✅ Leading | Earlier entries |
| Market Events | Misses | ✅ Captures | Better timing |
| Volatility | Reacts after | ✅ Anticipates | Higher R/R |
| Psychology | Ignores | ✅ Analyzes | Edge |

### Why 3-Hour Timeframe?

| Aspect | 1-Hour | **3-Hour** | Daily |
|--------|--------|------------|-------|
| Noise Level | High | ✅ Low | Very Low |
| Signal Quality | Medium | ✅ High | High |
| Opportunities | Many | ✅ Optimal | Few |
| News Relevance | 24h (stale) | ✅ 6h (fresh) | Days (old) |
| Stop Loss | 2% | ✅ 1.2% | 5% |
| Typical Move | 1-2% | ✅ 3-5% | 10-15% |

### Risk/Reward Targets

**Minimum 1:3 R/R Enforced:**
```
Risk: 1.2% stop loss
Reward: 3.6% take profit (minimum)
Win Rate Needed: 25% to break even
Target Win Rate: 40-50%
```

**Example with Leverage:**
```
BTC Entry: $50,000
Stop Loss: $49,400 (1.2% = $600 risk)
Take Profit: $51,800 (3.6% = $1,800 gain)
Leverage: 7x
Confidence: 82%

Win: $1,800 × 7 = $12,600 profit
Loss: $600 × 7 = $4,200 loss
```

---

## 🎮 Quick Start

### Prerequisites
- Python 3.8+
- API keys (NewsAPI, Groq)

### Installation

```bash
# Clone repository
git clone https://github.com/rqzbeh/simple-crypto-trader.git
cd simple-crypto-trader

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Required
export NEWS_API_KEY='your_newsapi_key'
export GROQ_API_KEY='your_groq_key'

# Optional (Telegram notifications)
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

### Run

```bash
python main.py
```

---

## 🔧 Technical Indicators

### The 10 Optimized Indicators (No Conflicts)

#### 1. **Stochastic RSI** (Weight: 2.5)
- **Purpose**: Primary momentum indicator
- **Why**: Most sensitive for crypto's volatility
- **Signal**: <20 oversold, >80 overbought

#### 2. **EMA Trend** (Weight: 2.3)
- **Purpose**: Multi-timeframe trend direction
- **EMAs**: 9, 21, 50, 200
- **Signal**: All aligned = strong trend

#### 3. **MACD** (Weight: 2.0)
- **Purpose**: Convergence/divergence
- **Why**: Different from EMA (measures momentum shift)
- **Signal**: Histogram crossing zero

#### 4. **Supertrend** (Weight: 1.9)
- **Purpose**: Volatility-adjusted trend
- **Why**: Uses ATR, complements EMA
- **Signal**: Price above/below band

#### 5. **ADX** (Weight: 1.8)
- **Purpose**: Trend STRENGTH filter
- **Why**: Tells if trend is strong enough to trade
- **Signal**: >25 = tradeable trend

#### 6. **Bollinger Bands** (Weight: 2.0)
- **Purpose**: Volatility measurement
- **Why**: Industry standard
- **Signal**: Position in bands (<10% or >90%)

#### 7. **ATR** (Weight: N/A)
- **Purpose**: Stop-loss calculation
- **Why**: Not directional, used for risk
- **Usage**: 1.5× ATR for stop distance

#### 8. **OBV** (Weight: 1.7)
- **Purpose**: Accumulation/distribution
- **Why**: Unique volume-based signal
- **Signal**: Above/below 20-period average

#### 9. **VWAP** (Weight: 2.1)
- **Purpose**: Institutional price levels
- **Why**: Critical for crypto markets
- **Signal**: Price above/below VWAP

#### 10. **Pivot Points** (Weight: 1.5)
- **Purpose**: Support/resistance levels
- **Why**: Classical technical analysis
- **Signal**: Price near key levels

---

## 🤖 AI Integration

### LLM-Powered Analysis
The system uses Groq's Llama 3.1 for:
- Market context interpretation
- Risk assessment (LOW/MEDIUM/HIGH)
- Timeframe recommendations
- Trading reasoning

### Hybrid Decision Making
```
Final Score = (60% × Technical Score) + (40% × LLM Score)

Agreement Boost: +30% confidence when all methods align
```

### Adaptive Learning
- Monitors win rate from past 20 trades
- Adjusts confidence thresholds dynamically
- Modifies risk multipliers based on volatility
- Self-optimizes without manual intervention

---

## 💰 Risk Management

### Stop Loss Strategy
```python
Base Stop = 1.2% minimum
ATR Stop = 1.5× ATR percentage
Final Stop = max(Base, min(ATR, 5%))
```

### Leverage Calculation
```python
R/R = Take Profit % / Stop Loss %
Confidence = 0 to 1
Leverage = floor(R/R + Confidence×5)
Max = 10x, Min = 2x
```

### Position Sizing
- Daily risk limit: 5%
- Per-trade risk: Adjusted by confidence
- Minimum R/R: 1:3 (enforced)

---

## 📊 Supported Cryptocurrencies

### Always Analyzed (Default 8)
BTC, ETH, BNB, ADA, SOL, DOGE, XRP, MATIC

### Full Support (50+)
Bitcoin, Ethereum, Binance Coin, Cardano, Solana, Dogecoin, XRP, Polkadot, Litecoin, Avalanche, Chainlink, Uniswap, Cosmos, Stellar, Algorand, VeChain, Filecoin, Tron, Ethereum Classic, AAVE, Maker, Compound, Sushi, YFI, Synthetix, Shiba Inu, NEAR, Flow, Decentraland, Sandbox, Axie Infinity, Chiliz, Enjin, BAT, 0x, Loopring, ImmutableX, ApeCoin, Optimism, Arbitrum, PEPE, Floki, and more...

---

## 📁 Project Structure

```
simple-crypto-trader/
├── main.py                    # Core trading bot (600+ lines)
├── technical_indicators.py    # Optimized indicators (280 lines)
├── llm_analyzer.py           # AI reasoning layer (250 lines)
├── requirements.txt          # Dependencies
├── trade_log.json           # Trade history (auto-created)
├── daily_risk.json          # Risk tracking (auto-created)
└── README.md                # This file
```

---

## 🎯 Configuration Options

### In `main.py`:

```python
# Timeframe
interval = '3h'  # 3-hour candles
period = '10d'   # 10 days history

# Risk
MIN_STOP_PCT = 0.012      # 1.2% minimum stop
TARGET_RR_RATIO = 3.0     # 1:3 minimum R/R
MAX_LEVERAGE_CRYPTO = 10  # 10x maximum

# News
NEWS_LOOKBACK = 6  # Hours

# Leverage
LOW_MONEY_MODE = True  # Optimized for <$500 accounts
```

---

## 📝 Example Output

```
============================================================
🚨 CRYPTO TRADE SIGNAL (3H TIMEFRAME)
============================================================
Symbol: BTC
Direction: LONG 🟢
Entry: $67234.50
Stop Loss: $66427.85 (1.20%)
Take Profit: $69654.20 (3.60%)
Leverage: 7x 💪
Risk/Reward: 1:3.0 🎯
Confidence: 82.5%

📊 Analysis:
Sentiment: 0.68 | Technical: 0.76
Strong bullish momentum with Stochastic RSI oversold. 
EMA trend aligned upward. MACD histogram positive and increasing.
OBV showing accumulation. Price above VWAP.

⏰ 2025-11-16 13:30:00 UTC | Timeframe: 3H
============================================================
```

---

## ⚙️ Advanced Customization

### Adjust Indicator Weights

```python
INDICATOR_WEIGHTS = {
    'stoch_rsi': 2.5,     # Increase for more momentum focus
    'ema_trend': 2.3,     # Increase for more trend focus
    'bb': 2.0,            # Volatility weight
    # ... customize as needed
}
```

### Modify Risk Parameters

```python
# More aggressive
MIN_STOP_PCT = 0.010      # 1.0% stops
MAX_LEVERAGE_CRYPTO = 15  # 15x max
TARGET_RR_RATIO = 4.0     # 1:4 target

# More conservative
MIN_STOP_PCT = 0.015      # 1.5% stops
MAX_LEVERAGE_CRYPTO = 5   # 5x max
TARGET_RR_RATIO = 2.0     # 1:2 target
```

---

## 🔬 System Architecture

### Design Principles
1. **No Redundancies**: Each indicator unique
2. **No Conflicts**: Indicators don't contradict
3. **Modular**: Easy to extend and maintain
4. **Adaptive**: Learns from performance
5. **Transparent**: Clear reasoning for every trade

### Data Flow
```
News → Sentiment Analysis → LLM Enhancement
  ↓
Market Data → Technical Indicators → Signals
  ↓
Combined Analysis → Risk Calculation → Trade Signal
  ↓
Logging → Adaptive Learning → Parameter Adjustment
```

---

## ⚠️ Risk Disclaimer

**CRITICAL WARNING:**

- ❌ NOT financial advice
- ❌ NOT guaranteed profits
- ❌ High risk of loss
- ✅ Educational/research tool only
- ✅ Test with small amounts first
- ✅ Never risk more than you can lose
- ✅ Consult licensed financial advisor

**Cryptocurrency trading is extremely risky. You can lose your entire investment. The authors are NOT responsible for any losses.**

---

## 📚 API Keys Setup

### NewsAPI (Required)
1. Visit: https://newsapi.org/register
2. Free tier: 100 requests/day
3. Get API key
4. `export NEWS_API_KEY='your_key'`

### Groq (Recommended)
1. Visit: https://console.groq.com/
2. Free tier: 1000 requests/day
3. Create API key
4. `export GROQ_API_KEY='your_key'`

### Telegram (Optional)
1. Create bot: https://t.me/BotFather
2. Get chat ID: https://t.me/userinfobot
3. Set environment variables

---

## 🤝 Contributing

Contributions welcome! Areas to improve:
- Additional indicators (must be non-conflicting)
- Better LLM prompts
- Backtesting framework
- Paper trading mode
- Web interface
- Mobile notifications

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- **AI-Trader (HKUDS)**: Inspiration for LLM-based trading
- **yfinance**: Market data provider
- **Groq**: Fast LLM inference
- **NewsAPI**: News aggregation
- Crypto trading community

---

## 📊 Performance Notes

### What to Expect
- **Win Rate**: Target 40-50%
- **Average R/R**: 1:3 to 1:5
- **Signals Per Day**: 2-5 high-quality setups
- **Drawdown**: Expect 10-20% max with proper sizing

### Best Practices
1. **Start Small**: Test with minimum capital
2. **Paper Trade First**: Verify strategies work
3. **Monitor Performance**: Track win rate
4. **Adjust Parameters**: Based on your risk tolerance
5. **Diversify**: Don't trade one coin only
6. **Be Patient**: Wait for 1:3+ setups

---

## 🔄 Updates & Roadmap

### v2.0 (Current)
- ✅ 3-hour timeframe optimization
- ✅ 1:3 minimum R/R enforcement
- ✅ 10x leverage capability
- ✅ LLM integration
- ✅ Adaptive learning
- ✅ Conflict-free indicators

### Future Plans
- [ ] Backtesting engine
- [ ] Paper trading mode
- [ ] Web dashboard
- [ ] Mobile app
- [ ] Multi-exchange support
- [ ] Advanced ML models

---

<div align="center">

**Built for Serious Crypto Traders** 🚀

[⭐ Star](https://github.com/rqzbeh/simple-crypto-trader) • [🐛 Issues](https://github.com/rqzbeh/simple-crypto-trader/issues) • [💡 Discussions](https://github.com/rqzbeh/simple-crypto-trader/discussions)

</div>
