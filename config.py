"""
Central Configuration for Crypto Trading System
All dynamic parameters and limits in one place
"""

import os

# ==================== FILE PATHS ====================
LLM_USAGE_FILE = 'llm_usage.json'

# ==================== TRADING PARAMETERS ====================

# Risk/Reward - CONSTANT (never goes below this)
TARGET_RR_RATIO = 3.0  # Minimum 1:3 risk/reward

# Stop Loss Boundaries (optimized for 2h trading window)
MIN_STOP_PCT = 0.008  # 0.8% minimum stop loss
MAX_STOP_PCT = 0.025  # 2.5% maximum stop loss

# Take Profit Boundaries (respecting R:R ratio)
MIN_TP_PCT = MIN_STOP_PCT * TARGET_RR_RATIO  # Minimum 2.4%
MAX_TP_PCT = 0.075  # 7.5% maximum for 2h trades

# Additional execution tuning constants (centralized from main.py)
ATR_STOP_MULTIPLIER = 1.2           # atr_stop = ATR * 1.2 (tighter for 2h trades)
REALISTIC_MOVEMENT_ATR_MULT = 2.5   # realistic movement = ATR * 2.5
TP_REALISTIC_CAP_MULT = 2.0         # cap expected profit at 2x realistic movement
BASE_TECH_RETURN_MULT = 0.5         # expected_return scaling by tech score
TP_CAP_BASE = 0.05                  # minimum TP cap before R:R override
ML_CONF_BLEND_HEURISTIC_WEIGHT = 0.6
ML_CONF_BLEND_MODEL_WEIGHT = 0.4
ML_LEVERAGE_LOW_PROB_FACTOR = 0.8   # reduce leverage when ml_prob < 0.5
ML_LEVERAGE_HIGH_PROB_INCREMENT = 1 # increment leverage when ml_prob > 0.7

# Trading Timeframe
TRADE_DURATION_HOURS = 2  # Short-term trading window

# Leverage
MIN_LEVERAGE = 2
MAX_LEVERAGE_CRYPTO = 20  # Maximum leverage for crypto

# News/Sentiment Parameters (for 2h SHORT-TERM trades)
EXPECTED_RETURN_PER_SENTIMENT = 0.04  # 4% base per sentiment point (realistic for 2h)
NEWS_IMPACT_MULTIPLIER = 0.015  # 1.5% per news article
MAX_NEWS_BONUS = 0.05  # 5% max bonus from news volume

# Low Money Mode Adjustments (for accounts < $500)
LOW_MONEY_MODE = True
if LOW_MONEY_MODE:
    EXPECTED_RETURN_PER_SENTIMENT = 0.05  # 5% for small accounts
    NEWS_IMPACT_MULTIPLIER = 0.018  # 1.8% per article
    MAX_NEWS_BONUS = 0.06  # 6% max bonus
    MIN_STOP_PCT = 0.008  # 0.8% - tight for short-term trades

# Risk Management
DAILY_RISK_LIMIT = 0.05  # 5% max daily loss
MAX_LEVERAGE_STOCK = 5  # 5x for stocks

# Indicator Weights (can be dynamically adjusted by learning system)
INDICATOR_WEIGHTS = {
    'candlestick': 3.0,  # Main analysis method using TA-Lib patterns
    'atr': 0.0,  # Used only for stop-loss calculation, not directional
}

# ==================== ML CONFIGURATION ====================
# Machine Learning is OPTIONAL - system works without it
ML_ENABLED = True  # Will be set to False if scikit-learn not available
ML_MODEL_FILE = 'crypto_ml_model.pkl'
ML_SCALER_FILE = 'crypto_ml_scaler.pkl'
ML_MIN_CONFIDENCE = 0.60
ML_RETRAIN_THRESHOLD = 20  # Retrain after 20 completed trades

# ==================== FILE PATHS ====================
TRADE_LOG_FILE = 'trade_log.json'
DAILY_RISK_FILE = 'daily_risk.json'

# ==================== LLM API LIMITS (FREE TIER) ====================

# Groq API Limits (https://console.groq.com/docs/rate-limits)
# Free tier as of 2025:
GROQ_LIMITS = {
    'llama-3.3-70b-versatile': {
        'requests_per_minute': 30,
        'requests_per_day': 14400,  # Confirmed free tier limit
        'tokens_per_minute': 6000,
        'context_window': 128000
    },
    'llama-3.1-70b-versatile': {
        'requests_per_minute': 30,
        'requests_per_day': 14400,
        'tokens_per_minute': 6000,
        'context_window': 128000
    },
    'llama-3.1-8b-instant': {
        'requests_per_minute': 30,
        'requests_per_day': 14400,
        'tokens_per_minute': 6000,
        'context_window': 128000
    },
    'mixtral-8x7b-32768': {
        'requests_per_minute': 30,
        'requests_per_day': 14400,
        'tokens_per_minute': 5000,
        'context_window': 32768
    },
    'gemma2-9b-it': {
        'requests_per_minute': 30,
        'requests_per_day': 14400,
        'tokens_per_minute': 15000,
        'context_window': 8192
    }
}

# OllamaFreeAPI Limits (community service, estimated)
# Based on typical free API patterns
OLLAMA_FREE_LIMITS = {
    'llama3.1:8b': {
        'requests_per_minute': 20,
        'requests_per_hour': 1000,
        'requests_per_day': 10000,  # Estimated safe limit
        'tokens_per_minute': 4000
    },
    'llama3.3:70b': {
        'requests_per_minute': 10,
        'requests_per_hour': 500,
        'requests_per_day': 5000,
        'tokens_per_minute': 3000
    }
}

# Default safe daily budget if model not found (conservative)
DEFAULT_DAILY_BUDGET = 1000
DEFAULT_HOURLY_BUDGET = 100
DEFAULT_MINUTE_BUDGET = 10

# Buffer percentage (use only this % of limit to be safe)
RATE_LIMIT_BUFFER = 0.85  # Use only 85% of stated limits

# ==================== LEARNING SYSTEM PARAMETERS ====================

# Optimization intervals
OPTIMIZATION_INTERVAL_TRADES = 20  # Optimize after every 20 trades
MIN_TRADES_FOR_ADJUSTMENT = 10  # Minimum trades before adjusting strategy

# Adjustment bounds (safety limits for dynamic optimization)
ADJUSTMENT_BOUNDS = {
    'tp_adjustment_factor': (0.5, 2.0),  # TP can be 50%-200% of calculated
    'sl_adjustment_factor': (0.7, 1.6),  # SL can be 70%-160% of calculated
    'entry_adjustment_factor': (0.7, 1.2),  # Entry can move 70%-120%
    'risk_multiplier': (0.5, 1.5),  # Risk can be 50%-150%
    'confidence_threshold': (0.2, 0.7)  # Confidence threshold 20%-70%
}

# Dynamic bounds for adaptive parameter tuning (used in analyzer)
ADAPTIVE_LIMITS = {
    'expected_return_per_sentiment': (0.015, 0.08),
    'news_impact_multiplier': (0.005, 0.03),
    'max_news_bonus': (0.02, 0.10),
    'dynamic_max_leverage': (3, 25),
    'daily_risk_limit': (0.03, 0.07),
    'sl_adjustment_factor': (0.7, 1.4),
    'tp_adjustment_factor': (0.7, 1.3)
}

# Performance thresholds
GOOD_WIN_RATE = 0.55  # 55%+ is good
EXCELLENT_WIN_RATE = 0.65  # 65%+ is excellent
POOR_WIN_RATE = 0.40  # Below 40% triggers aggressive adjustment

# ==================== CACHE & STORAGE ====================

LEARNING_STATE_FILE = 'learning_state.json'
TRADE_LOG_FILE = 'trade_log.json'
NEWS_CACHE_FILE = 'news_cache.json'
LLM_USAGE_FILE = 'llm_usage.json'

NEWS_CACHE_MAX_AGE_HOURS = 12  # Cache news analysis for 12 hours
NEWS_CACHE_RESET_HOURS = 24  # Full cache reset every 24 hours

# ==================== HELPER FUNCTIONS ====================

def get_llm_limits(provider: str, model: str) -> dict:
    """
    Get rate limits for specific provider and model
    Returns dict with requests_per_minute, requests_per_day, etc.
    """
    if provider.lower() == 'groq':
        limits = GROQ_LIMITS.get(model, None)
        if limits:
            # Apply safety buffer
            return {
                'requests_per_minute': int(limits['requests_per_minute'] * RATE_LIMIT_BUFFER),
                'requests_per_day': int(limits['requests_per_day'] * RATE_LIMIT_BUFFER),
                'tokens_per_minute': int(limits['tokens_per_minute'] * RATE_LIMIT_BUFFER)
            }
    elif provider.lower() in ['ollamafreeapi', 'ollama']:
        limits = OLLAMA_FREE_LIMITS.get(model, None)
        if limits:
            return {
                'requests_per_minute': int(limits['requests_per_minute'] * RATE_LIMIT_BUFFER),
                'requests_per_hour': int(limits['requests_per_hour'] * RATE_LIMIT_BUFFER),
                'requests_per_day': int(limits['requests_per_day'] * RATE_LIMIT_BUFFER)
            }
    
    # Default conservative limits if model not found
    return {
        'requests_per_minute': DEFAULT_MINUTE_BUDGET,
        'requests_per_hour': DEFAULT_HOURLY_BUDGET,
        'requests_per_day': DEFAULT_DAILY_BUDGET
    }

def clamp_value(value: float, bounds: tuple) -> float:
    """Clamp value within bounds (min, max)"""
    return max(bounds[0], min(value, bounds[1]))

def enforce_min_rr(stop_pct: float, tp_pct: float) -> tuple:
    """
    Ensure stop loss and take profit maintain minimum R:R ratio
    Returns (adjusted_stop_pct, adjusted_tp_pct)
    """
    current_rr = tp_pct / stop_pct if stop_pct > 0 else 0
    
    if current_rr < TARGET_RR_RATIO:
        # Adjust TP to meet minimum R:R
        tp_pct = stop_pct * TARGET_RR_RATIO
    
    # Ensure within bounds
    stop_pct = max(MIN_STOP_PCT, min(stop_pct, MAX_STOP_PCT))
    tp_pct = max(MIN_TP_PCT, min(tp_pct, MAX_TP_PCT))
    
    # Final R:R check
    final_rr = tp_pct / stop_pct if stop_pct > 0 else 0
    if final_rr < TARGET_RR_RATIO:
        # If still below, increase TP even if it exceeds MAX_TP_PCT
        # This ensures we NEVER trade with R:R < 1:3
        tp_pct = stop_pct * TARGET_RR_RATIO
    
    return stop_pct, tp_pct

def apply_trade_bounds(stop_pct: float, tp_pct: float) -> tuple:
    """Unified enforcement of trade bounds and minimum R:R.
    Applies clamping to stop and take profit percentages, then ensures
    the R:R ratio is at least TARGET_RR_RATIO by adjusting tp_pct upward if needed.
    Returns (adjusted_stop_pct, adjusted_tp_pct, rr_ratio).
    """
    # Clamp stop within allowed range
    stop_pct = max(MIN_STOP_PCT, min(stop_pct, MAX_STOP_PCT))
    # Clamp TP first to ensure realism, but we'll still enforce R:R afterwards
    tp_pct = max(MIN_TP_PCT, min(tp_pct, MAX_TP_PCT))
    # Enforce minimum R:R (1:TARGET_RR_RATIO)
    if stop_pct > 0:
        min_tp = stop_pct * TARGET_RR_RATIO
        if tp_pct < min_tp:
            tp_pct = min_tp  # may exceed MAX_TP_PCT intentionally to respect mandatory R:R
    rr_ratio = tp_pct / stop_pct if stop_pct > 0 else 0
    return stop_pct, tp_pct, rr_ratio

# ==================== ENVIRONMENT OVERRIDES ====================

# Allow environment variables to override defaults
TARGET_RR_RATIO = float(os.getenv('TARGET_RR_RATIO', TARGET_RR_RATIO))
MAX_LEVERAGE_CRYPTO = int(os.getenv('MAX_LEVERAGE', MAX_LEVERAGE_CRYPTO))
TRADE_DURATION_HOURS = float(os.getenv('TRADE_DURATION_HOURS', TRADE_DURATION_HOURS))

# Custom daily budget override (if user wants to be more/less conservative)
CUSTOM_DAILY_BUDGET = os.getenv('LLM_DAILY_BUDGET')
if CUSTOM_DAILY_BUDGET:
    DEFAULT_DAILY_BUDGET = int(CUSTOM_DAILY_BUDGET)
