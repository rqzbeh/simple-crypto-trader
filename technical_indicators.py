"""
Advanced Technical Indicators for Cryptocurrency Trading
Implements state-of-the-art indicators optimized for crypto markets
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_stoch_rsi(rsi: pd.Series, period: int = 14) -> tuple:
    """Calculate Stochastic RSI - more sensitive than regular RSI"""
    rsi_min = rsi.rolling(window=period).min()
    rsi_max = rsi.rolling(window=period).max()
    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min) * 100
    stoch_rsi_k = stoch_rsi.rolling(window=3).mean()  # %K
    stoch_rsi_d = stoch_rsi_k.rolling(window=3).mean()  # %D
    return stoch_rsi_k, stoch_rsi_d

def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Williams %R"""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
    return williams_r

def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """Calculate MACD"""
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def calculate_ema_trend(close: pd.Series) -> tuple:
    """Calculate EMA trend indicators"""
    ema9 = close.ewm(span=9).mean()
    ema21 = close.ewm(span=21).mean()
    ema50 = close.ewm(span=50).mean()
    ema200 = close.ewm(span=200).mean() if len(close) >= 200 else ema50
    return ema9, ema21, ema50, ema200

def calculate_supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0) -> tuple:
    """Calculate Supertrend indicator - excellent for crypto trend following"""
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

def calculate_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> tuple:
    """Calculate Bollinger Bands"""
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def calculate_keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20, atr_period: int = 10, multiplier: float = 2.0) -> tuple:
    """Calculate Keltner Channels - alternative to Bollinger Bands"""
    ema = close.ewm(span=period).mean()
    
    # Calculate ATR
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift()),
        'lc': abs(low - close.shift())
    }).max(axis=1)
    atr = tr.rolling(window=atr_period).mean()
    
    upper_channel = ema + (atr * multiplier)
    lower_channel = ema - (atr * multiplier)
    return upper_channel, ema, lower_channel

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift()),
        'lc': abs(low - close.shift())
    }).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume"""
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
    """Calculate Volume Weighted Average Price"""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap

def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Money Flow Index - RSI with volume"""
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    
    mfi_ratio = positive_flow / negative_flow
    mfi = 100 - (100 / (1 + mfi_ratio))
    return mfi

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> tuple:
    """Calculate Average Directional Index"""
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

def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Commodity Channel Index"""
    typical_price = (high + low + close) / 3
    sma = typical_price.rolling(window=period).mean()
    mad = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    cci = (typical_price - sma) / (0.015 * mad)
    return cci

def calculate_pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, float]:
    """Calculate pivot points for support/resistance"""
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

def calculate_fibonacci_levels(high: pd.Series, low: pd.Series, lookback: int = 50) -> Dict[str, float]:
    """Calculate Fibonacci retracement levels"""
    recent_high = high.tail(lookback).max()
    recent_low = low.tail(lookback).min()
    diff = recent_high - recent_low
    
    return {
        'level_0': recent_high,
        'level_236': recent_high - 0.236 * diff,
        'level_382': recent_high - 0.382 * diff,
        'level_500': recent_high - 0.500 * diff,
        'level_618': recent_high - 0.618 * diff,
        'level_786': recent_high - 0.786 * diff,
        'level_100': recent_low
    }

def get_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate all technical indicators and return signals"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    volume = df['Volume']
    current_price = float(close.iloc[-1])
    
    indicators = {}
    
    # RSI
    rsi = calculate_rsi(close)
    rsi_value = float(rsi.iloc[-1])
    indicators['rsi'] = {
        'value': rsi_value,
        'signal': 1 if rsi_value < 30 else (-1 if rsi_value > 70 else 0)
    }
    
    # Stochastic RSI
    stoch_rsi_k, stoch_rsi_d = calculate_stoch_rsi(rsi)
    stoch_rsi_value = float(stoch_rsi_k.iloc[-1]) if not stoch_rsi_k.empty else 50
    indicators['stoch_rsi'] = {
        'value': stoch_rsi_value,
        'signal': 1 if stoch_rsi_value < 20 else (-1 if stoch_rsi_value > 80 else 0)
    }
    
    # Williams %R
    williams_r = calculate_williams_r(high, low, close)
    williams_value = float(williams_r.iloc[-1])
    indicators['williams_r'] = {
        'value': williams_value,
        'signal': 1 if williams_value < -80 else (-1 if williams_value > -20 else 0)
    }
    
    # MACD
    macd, macd_signal_line, macd_hist = calculate_macd(close)
    indicators['macd'] = {
        'value': float(macd_hist.iloc[-1]),
        'signal': 1 if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-1] > macd_hist.iloc[-2] else -1
    }
    
    # EMA Trend
    ema9, ema21, ema50, ema200 = calculate_ema_trend(close)
    ema_trend_signal = 0
    if ema9.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1] and current_price > ema9.iloc[-1]:
        ema_trend_signal = 1
    elif ema9.iloc[-1] < ema21.iloc[-1] < ema50.iloc[-1] and current_price < ema9.iloc[-1]:
        ema_trend_signal = -1
    
    indicators['ema_trend'] = {
        'ema9': float(ema9.iloc[-1]),
        'ema21': float(ema21.iloc[-1]),
        'ema50': float(ema50.iloc[-1]),
        'signal': ema_trend_signal
    }
    
    # Supertrend
    supertrend, st_direction = calculate_supertrend(high, low, close)
    indicators['supertrend'] = {
        'value': float(supertrend.iloc[-1]),
        'signal': int(st_direction.iloc[-1])
    }
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
    bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
    indicators['bb'] = {
        'upper': float(bb_upper.iloc[-1]),
        'middle': float(bb_middle.iloc[-1]),
        'lower': float(bb_lower.iloc[-1]),
        'position': bb_position,
        'signal': 1 if bb_position < 0.1 else (-1 if bb_position > 0.9 else 0)
    }
    
    # Keltner Channels
    kc_upper, kc_middle, kc_lower = calculate_keltner_channels(high, low, close)
    indicators['keltner'] = {
        'upper': float(kc_upper.iloc[-1]),
        'middle': float(kc_middle.iloc[-1]),
        'lower': float(kc_lower.iloc[-1]),
        'signal': 1 if current_price < kc_lower.iloc[-1] else (-1 if current_price > kc_upper.iloc[-1] else 0)
    }
    
    # ATR
    atr = calculate_atr(high, low, close)
    atr_pct = float(atr.iloc[-1] / current_price)
    indicators['atr'] = {
        'value': float(atr.iloc[-1]),
        'percent': atr_pct,
        'signal': 0  # ATR is for volatility measurement, not directional
    }
    
    # OBV
    obv = calculate_obv(close, volume)
    obv_sma = obv.rolling(window=20).mean()
    indicators['obv'] = {
        'value': float(obv.iloc[-1]),
        'signal': 1 if obv.iloc[-1] > obv_sma.iloc[-1] else -1
    }
    
    # VWAP
    vwap = calculate_vwap(high, low, close, volume)
    indicators['vwap'] = {
        'value': float(vwap.iloc[-1]),
        'signal': 1 if current_price > vwap.iloc[-1] else -1
    }
    
    # Volume Profile (simplified)
    avg_volume = volume.rolling(window=20).mean()
    indicators['volume_profile'] = {
        'current': float(volume.iloc[-1]),
        'average': float(avg_volume.iloc[-1]),
        'signal': 1 if volume.iloc[-1] > avg_volume.iloc[-1] * 1.5 else 0
    }
    
    # MFI
    mfi = calculate_mfi(high, low, close, volume)
    mfi_value = float(mfi.iloc[-1])
    indicators['mfi'] = {
        'value': mfi_value,
        'signal': 1 if mfi_value < 20 else (-1 if mfi_value > 80 else 0)
    }
    
    # ADX
    adx, plus_di, minus_di = calculate_adx(high, low, close)
    adx_value = float(adx.iloc[-1])
    indicators['adx'] = {
        'value': adx_value,
        'plus_di': float(plus_di.iloc[-1]),
        'minus_di': float(minus_di.iloc[-1]),
        'signal': 1 if adx_value > 25 and plus_di.iloc[-1] > minus_di.iloc[-1] else (-1 if adx_value > 25 else 0)
    }
    
    # CCI
    cci = calculate_cci(high, low, close)
    cci_value = float(cci.iloc[-1])
    indicators['cci'] = {
        'value': cci_value,
        'signal': 1 if cci_value < -100 else (-1 if cci_value > 100 else 0)
    }
    
    # Pivot Points
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
    
    # Fibonacci Levels
    fib_levels = calculate_fibonacci_levels(high, low)
    fib_signal = 0
    # Check if price is near key Fibonacci levels
    for level_name, level_value in fib_levels.items():
        if abs(current_price - level_value) / current_price < 0.01:  # Within 1%
            if '618' in level_name or '382' in level_name:
                fib_signal = 1 if current_price < level_value else -1
    
    indicators['fibonacci'] = {
        **fib_levels,
        'signal': fib_signal
    }
    
    return indicators
