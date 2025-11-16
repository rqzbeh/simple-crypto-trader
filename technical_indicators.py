"""
Optimized Technical Indicators for Cryptocurrency Trading
CONFLICT-FREE: Each indicator serves a unique, non-overlapping purpose
Reduced from 17 to 10 indicators by removing redundancies
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_stoch_rsi(close: pd.Series, rsi_period: int = 14, stoch_period: int = 14) -> tuple:
    """
    Calculate Stochastic RSI - Most sensitive momentum indicator
    Better than regular RSI for crypto's high volatility
    """
    # First calculate RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Then calculate Stochastic of RSI
    rsi_min = rsi.rolling(window=stoch_period).min()
    rsi_max = rsi.rolling(window=stoch_period).max()
    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min) * 100
    stoch_rsi_k = stoch_rsi.rolling(window=3).mean()  # %K
    stoch_rsi_d = stoch_rsi_k.rolling(window=3).mean()  # %D
    return stoch_rsi_k, stoch_rsi_d

def calculate_ema_trend(close: pd.Series) -> tuple:
    """Multi-timeframe EMA trend - Primary trend indicator"""
    ema9 = close.ewm(span=9).mean()
    ema21 = close.ewm(span=21).mean()
    ema50 = close.ewm(span=50).mean()
    ema200 = close.ewm(span=200).mean() if len(close) >= 200 else ema50
    return ema9, ema21, ema50, ema200

def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """MACD - Measures convergence/divergence (different from EMA trend)"""
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def calculate_supertrend(high: pd.Series, low: pd.Series, close: pd.Series, 
                        period: int = 10, multiplier: float = 3.0) -> tuple:
    """Supertrend - Volatility-adjusted trend (uses ATR, complements EMA)"""
    # Calculate ATR
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift()),
        'lc': abs(low - close.shift())
    }).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Calculate basic bands
    hl_avg = (high + low) / 2
    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)
    
    # Calculate Supertrend
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    
    for i in range(period, len(close)):
        if i == period:
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        else:
            if close.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
                direction.iloc[i] = 1
            else:
                supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
                direction.iloc[i] = -1
    
    return supertrend, direction

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> tuple:
    """ADX - Measures trend STRENGTH, not direction (unique purpose)"""
    # Calculate True Range
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift()),
        'lc': abs(low - close.shift())
    }).max(axis=1)
    
    # Calculate Directional Movement
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    # Smooth the values
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    
    # Calculate ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    
    return adx, plus_di, minus_di

def calculate_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> tuple:
    """Bollinger Bands - Industry standard volatility indicator"""
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """ATR - For stop-loss calculation only (not directional)"""
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift()),
        'lc': abs(low - close.shift())
    }).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """OBV - Unique accumulation/distribution indicator"""
    obv = pd.Series(index=close.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]
    
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv

def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """VWAP - Institutional price levels"""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap

def calculate_pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, float]:
    """Pivot Points - Classical support/resistance levels"""
    pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
    r1 = 2 * pivot - low.iloc[-2]
    s1 = 2 * pivot - high.iloc[-2]
    r2 = pivot + (high.iloc[-2] - low.iloc[-2])
    s2 = pivot - (high.iloc[-2] - low.iloc[-2])
    r3 = high.iloc[-2] + 2 * (pivot - low.iloc[-2])
    s3 = low.iloc[-2] - 2 * (high.iloc[-2] - pivot)
    
    return {
        'pivot': pivot,
        'r1': r1, 'r2': r2, 'r3': r3,
        's1': s1, 's2': s2, 's3': s3
    }

def get_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate all OPTIMIZED technical indicators
    NO CONFLICTS - Each indicator serves unique purpose
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    volume = df['Volume']
    current_price = float(close.iloc[-1])
    
    indicators = {}
    
    # 1. Stochastic RSI - PRIMARY momentum indicator
    stoch_rsi_k, stoch_rsi_d = calculate_stoch_rsi(close)
    stoch_rsi_value = float(stoch_rsi_k.iloc[-1]) if not stoch_rsi_k.empty else 50
    indicators['stoch_rsi'] = {
        'value': stoch_rsi_value,
        'signal': 1 if stoch_rsi_value < 20 else (-1 if stoch_rsi_value > 80 else 0)
    }
    
    # 2. EMA Trend - PRIMARY trend indicator
    ema9, ema21, ema50, ema200 = calculate_ema_trend(close)
    ema_trend_signal = 0
    if ema9.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1] and current_price > ema9.iloc[-1]:
        ema_trend_signal = 1  # Strong uptrend
    elif ema9.iloc[-1] < ema21.iloc[-1] < ema50.iloc[-1] and current_price < ema9.iloc[-1]:
        ema_trend_signal = -1  # Strong downtrend
    
    indicators['ema_trend'] = {
        'ema9': float(ema9.iloc[-1]),
        'ema21': float(ema21.iloc[-1]),
        'ema50': float(ema50.iloc[-1]),
        'signal': ema_trend_signal
    }
    
    # 3. MACD - Convergence/divergence indicator
    macd, macd_signal_line, macd_hist = calculate_macd(close)
    indicators['macd'] = {
        'value': float(macd_hist.iloc[-1]),
        'signal': 1 if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-1] > macd_hist.iloc[-2] else -1
    }
    
    # 4. Supertrend - Volatility-adjusted trend
    supertrend, st_direction = calculate_supertrend(high, low, close)
    indicators['supertrend'] = {
        'value': float(supertrend.iloc[-1]),
        'signal': int(st_direction.iloc[-1])
    }
    
    # 5. ADX - Trend STRENGTH filter
    adx, plus_di, minus_di = calculate_adx(high, low, close)
    adx_value = float(adx.iloc[-1])
    # Signal: 1 if strong trend + bullish, -1 if strong trend + bearish, 0 if weak trend
    if adx_value > 25:
        if plus_di.iloc[-1] > minus_di.iloc[-1]:
            adx_signal = 1
        else:
            adx_signal = -1
    else:
        adx_signal = 0  # Trend too weak to trade
    
    indicators['adx'] = {
        'value': adx_value,
        'plus_di': float(plus_di.iloc[-1]),
        'minus_di': float(minus_di.iloc[-1]),
        'signal': adx_signal
    }
    
    # 6. Bollinger Bands - Volatility indicator
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
    bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
    indicators['bb'] = {
        'upper': float(bb_upper.iloc[-1]),
        'middle': float(bb_middle.iloc[-1]),
        'lower': float(bb_lower.iloc[-1]),
        'position': bb_position,
        # Signal: Mean reversion logic
        'signal': 1 if bb_position < 0.1 else (-1 if bb_position > 0.9 else 0)
    }
    
    # 7. ATR - For stop-loss only (not directional)
    atr = calculate_atr(high, low, close)
    atr_pct = float(atr.iloc[-1] / current_price)
    indicators['atr'] = {
        'value': float(atr.iloc[-1]),
        'percent': atr_pct,
        'signal': 0  # ATR is not directional
    }
    
    # 8. OBV - Accumulation/distribution
    obv = calculate_obv(close, volume)
    obv_sma = obv.rolling(window=20).mean()
    indicators['obv'] = {
        'value': float(obv.iloc[-1]),
        'signal': 1 if obv.iloc[-1] > obv_sma.iloc[-1] else -1
    }
    
    # 9. VWAP - Institutional levels
    vwap = calculate_vwap(high, low, close, volume)
    indicators['vwap'] = {
        'value': float(vwap.iloc[-1]),
        'signal': 1 if current_price > vwap.iloc[-1] else -1
    }
    
    # 10. Pivot Points - Support/Resistance
    pivots = calculate_pivot_points(high, low, close)
    pivot_signal = 0
    if current_price < pivots['s1']:
        pivot_signal = 1  # Below support, potential bounce
    elif current_price > pivots['r1']:
        pivot_signal = -1  # Above resistance, potential pullback
    
    indicators['pivot_points'] = {
        **pivots,
        'signal': pivot_signal
    }
    
    return indicators
