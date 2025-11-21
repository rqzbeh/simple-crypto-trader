"""
Candlestick Pattern Analyzer - FREE candlestick pattern recognition
Uses TA-Lib for pattern detection (no additional API calls needed)
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, List, Tuple


def calculate_atr_for_stops(df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
    """
    Calculate ATR for stop-loss purposes only (not for signals)
    """
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    
    atr = talib.ATR(high, low, close, timeperiod=period)
    current_price = float(close[-1])
    atr_value = float(atr[-1])  # Fixed: talib returns numpy array
    atr_pct = atr_value / current_price if current_price > 0 else 0.02
    
    return {
        'value': atr_value,
        'percent': atr_pct,
        'signal': 0  # ATR is not directional
    }


def detect_candlestick_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect candlestick patterns using TA-Lib (100% free, no API calls)
    Returns comprehensive pattern analysis with signals
    
    Args:
        df: DataFrame with OHLC data (Open, High, Low, Close)
    
    Returns:
        Dictionary with pattern detections and trading signals
    """
    if df.empty or len(df) < 10:
        return {'patterns': {}, 'signal': 0, 'confidence': 0}
    
    open_prices = df['Open'].values
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    
    patterns = {}
    bullish_patterns = []
    bearish_patterns = []
    
    # === BULLISH PATTERNS ===
    
    # Hammer (bullish reversal)
    hammer = talib.CDLHAMMER(open_prices, high, low, close)
    if hammer[-1] > 0:
        patterns['hammer'] = {'detected': True, 'type': 'bullish', 'strength': hammer[-1]}
        bullish_patterns.append(('hammer', 1.0))
    
    # Inverted Hammer (bullish reversal)
    inv_hammer = talib.CDLINVERTEDHAMMER(open_prices, high, low, close)
    if inv_hammer[-1] > 0:
        patterns['inverted_hammer'] = {'detected': True, 'type': 'bullish', 'strength': inv_hammer[-1]}
        bullish_patterns.append(('inverted_hammer', 0.9))
    
    # Bullish Engulfing (strong bullish)
    engulfing = talib.CDLENGULFING(open_prices, high, low, close)
    if engulfing[-1] > 0:
        patterns['bullish_engulfing'] = {'detected': True, 'type': 'bullish', 'strength': engulfing[-1]}
        bullish_patterns.append(('bullish_engulfing', 1.2))
    
    # Morning Star (strong bullish reversal)
    morning_star = talib.CDLMORNINGSTAR(open_prices, high, low, close)
    if morning_star[-1] > 0:
        patterns['morning_star'] = {'detected': True, 'type': 'bullish', 'strength': morning_star[-1]}
        bullish_patterns.append(('morning_star', 1.5))
    
    # Three White Soldiers (very strong bullish)
    three_white = talib.CDL3WHITESOLDIERS(open_prices, high, low, close)
    if three_white[-1] > 0:
        patterns['three_white_soldiers'] = {'detected': True, 'type': 'bullish', 'strength': three_white[-1]}
        bullish_patterns.append(('three_white_soldiers', 1.8))
    
    # Piercing Line (bullish reversal)
    piercing = talib.CDLPIERCING(open_prices, high, low, close)
    if piercing[-1] > 0:
        patterns['piercing_line'] = {'detected': True, 'type': 'bullish', 'strength': piercing[-1]}
        bullish_patterns.append(('piercing_line', 1.0))
    
    # Bullish Harami (moderate bullish)
    harami = talib.CDLHARAMI(open_prices, high, low, close)
    if harami[-1] > 0:
        patterns['bullish_harami'] = {'detected': True, 'type': 'bullish', 'strength': harami[-1]}
        bullish_patterns.append(('bullish_harami', 0.8))
    
    # Three Inside Up (bullish continuation)
    three_inside = talib.CDL3INSIDE(open_prices, high, low, close)
    if three_inside[-1] > 0:
        patterns['three_inside_up'] = {'detected': True, 'type': 'bullish', 'strength': three_inside[-1]}
        bullish_patterns.append(('three_inside_up', 1.1))
    
    # === BEARISH PATTERNS ===
    
    # Shooting Star (bearish reversal)
    shooting_star = talib.CDLSHOOTINGSTAR(open_prices, high, low, close)
    if shooting_star[-1] < 0:
        patterns['shooting_star'] = {'detected': True, 'type': 'bearish', 'strength': shooting_star[-1]}
        bearish_patterns.append(('shooting_star', -1.0))
    
    # Hanging Man (bearish reversal)
    hanging_man = talib.CDLHANGINGMAN(open_prices, high, low, close)
    if hanging_man[-1] < 0:
        patterns['hanging_man'] = {'detected': True, 'type': 'bearish', 'strength': hanging_man[-1]}
        bearish_patterns.append(('hanging_man', -0.9))
    
    # Bearish Engulfing (strong bearish)
    if engulfing[-1] < 0:
        patterns['bearish_engulfing'] = {'detected': True, 'type': 'bearish', 'strength': engulfing[-1]}
        bearish_patterns.append(('bearish_engulfing', -1.2))
    
    # Evening Star (strong bearish reversal)
    evening_star = talib.CDLEVENINGSTAR(open_prices, high, low, close)
    if evening_star[-1] < 0:
        patterns['evening_star'] = {'detected': True, 'type': 'bearish', 'strength': evening_star[-1]}
        bearish_patterns.append(('evening_star', -1.5))
    
    # Three Black Crows (very strong bearish)
    three_black = talib.CDL3BLACKCROWS(open_prices, high, low, close)
    if three_black[-1] < 0:
        patterns['three_black_crows'] = {'detected': True, 'type': 'bearish', 'strength': three_black[-1]}
        bearish_patterns.append(('three_black_crows', -1.8))
    
    # Dark Cloud Cover (bearish reversal)
    dark_cloud = talib.CDLDARKCLOUDCOVER(open_prices, high, low, close)
    if dark_cloud[-1] < 0:
        patterns['dark_cloud_cover'] = {'detected': True, 'type': 'bearish', 'strength': dark_cloud[-1]}
        bearish_patterns.append(('dark_cloud_cover', -1.0))
    
    # Bearish Harami (moderate bearish)
    if harami[-1] < 0:
        patterns['bearish_harami'] = {'detected': True, 'type': 'bearish', 'strength': harami[-1]}
        bearish_patterns.append(('bearish_harami', -0.8))
    
    # Three Inside Down (bearish continuation)
    if three_inside[-1] < 0:
        patterns['three_inside_down'] = {'detected': True, 'type': 'bearish', 'strength': three_inside[-1]}
        bearish_patterns.append(('three_inside_down', -1.1))
    
    # === NEUTRAL/CONTINUATION PATTERNS ===
    
    # Doji (indecision)
    doji = talib.CDLDOJI(open_prices, high, low, close)
    if doji[-1] != 0:
        patterns['doji'] = {'detected': True, 'type': 'neutral', 'strength': 0}
    
    # Spinning Top (indecision)
    spinning_top = talib.CDLSPINNINGTOP(open_prices, high, low, close)
    if spinning_top[-1] != 0:
        patterns['spinning_top'] = {'detected': True, 'type': 'neutral', 'strength': 0}
    
    # Calculate overall signal (-1 to +1)
    bullish_score = sum(strength for _, strength in bullish_patterns)
    bearish_score = sum(abs(strength) for _, strength in bearish_patterns)
    
    total_score = bullish_score - bearish_score
    
    # Normalize to -1 to +1 range
    max_possible_score = 5.0  # Reasonable max for multiple patterns
    signal = max(-1.0, min(1.0, total_score / max_possible_score))
    
    # Calculate confidence based on number and strength of patterns
    num_patterns = len(bullish_patterns) + len(bearish_patterns)
    confidence = min(1.0, num_patterns * 0.15 + abs(signal) * 0.3)
    
    return {
        'patterns': patterns,
        'signal': signal,
        'confidence': confidence,
        'bullish_patterns': [name for name, _ in bullish_patterns],
        'bearish_patterns': [name for name, _ in bearish_patterns],
        'bullish_score': bullish_score,
        'bearish_score': bearish_score,
        'pattern_count': num_patterns
    }


def get_candlestick_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get comprehensive candlestick analysis with trading signals
    This is the main function to use - returns everything needed
    
    Returns:
        Dictionary with:
        - signal: -1 to +1 (bearish to bullish)
        - confidence: 0 to 1
        - patterns: detected patterns
        - description: human-readable summary
    """
    analysis = detect_candlestick_patterns(df)
    
    # Generate description
    if analysis['signal'] > 0.5:
        strength = "Very Strong"
    elif analysis['signal'] > 0.2:
        strength = "Strong"
    elif analysis['signal'] > 0:
        strength = "Moderate"
    elif analysis['signal'] > -0.2:
        strength = "Weak Bearish"
    elif analysis['signal'] > -0.5:
        strength = "Strong Bearish"
    else:
        strength = "Very Strong Bearish"
    
    description = f"{strength} signal from {analysis['pattern_count']} candlestick patterns"
    if analysis['bullish_patterns']:
        description += f". Bullish: {', '.join(analysis['bullish_patterns'][:3])}"
    if analysis['bearish_patterns']:
        description += f". Bearish: {', '.join(analysis['bearish_patterns'][:3])}"
    
    return {
        'signal': analysis['signal'],
        'confidence': analysis['confidence'],
        'patterns': analysis['patterns'],
        'pattern_names': {
            'bullish': analysis['bullish_patterns'],
            'bearish': analysis['bearish_patterns']
        },
        'description': description,
        'raw_analysis': analysis
    }


def get_all_candlestick_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Wrapper to match the interface expected by main.py
    Returns candlestick analysis in the same format as technical_indicators
    Multi-timeframe analysis: 1h (short-term), 4h (medium-term), Daily (long-term)
    Optimized for 2-hour trading timeframe
    """
    # Get analysis on multiple timeframes
    analysis_1h = get_candlestick_analysis(df)
    
    signals = []
    weights = []
    timeframes = []
    
    # 1-hour analysis (50% weight) - for timing and short-term patterns
    signals.append(analysis_1h['signal'])
    weights.append(0.5)
    timeframes.append('1h')
    
    # Create 4h timeframe by resampling (if we have enough data)
    if len(df) >= 8:  # Need at least 8 hours for 4h resampling
        df_4h = df.resample('4H').agg({
            'Open': 'first',
            'High': 'max', 
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        if len(df_4h) >= 5:  # Need at least 5 candles for meaningful analysis
            analysis_4h = get_candlestick_analysis(df_4h)
            # 4-hour analysis (35% weight) - for medium-term trend confirmation
            signals.append(analysis_4h['signal'])
            weights.append(0.35)
            timeframes.append('4h')
    
    # Create daily timeframe (if we have enough data)
    if len(df) >= 48:  # Need at least 2 days for daily resampling
        df_daily = df.resample('D').agg({
            'Open': 'first',
            'High': 'max', 
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        if len(df_daily) >= 7:  # Need at least 1 week for meaningful daily analysis
            analysis_daily = get_candlestick_analysis(df_daily)
            # Daily analysis (15% weight) - for long-term trend context
            signals.append(analysis_daily['signal'])
            weights.append(0.15)
            timeframes.append('daily')
    
    # Combine signals using weighted average
    if len(signals) > 1:
        combined_signal = sum(s * w for s, w in zip(signals, weights))
        # Use the highest confidence from any timeframe
        confidences = [analysis_1h['confidence']]
        if 'analysis_4h' in locals():
            confidences.append(analysis_4h['confidence'])
        if 'analysis_daily' in locals():
            confidences.append(analysis_daily['confidence'])
        combined_confidence = max(confidences)
        
        # Determine primary timeframe (the one with strongest signal)
        max_signal_idx = signals.index(max(signals, key=abs))
        primary_timeframe = timeframes[max_signal_idx]
        
        final_analysis = {
            'signal': combined_signal,
            'confidence': combined_confidence,
            'timeframe': f'{primary_timeframe}_primary',
            'description': f'Multi-timeframe analysis ({", ".join(timeframes)})',
            'pattern_names': analysis_1h['pattern_names']  # Use 1h patterns for display
        }
    else:
        # Fallback to 1h only
        final_analysis = analysis_1h
        final_analysis['timeframe'] = '1h_only'
    
    # Pure candlestick analysis only - no additional indicators
    combined_signal = final_analysis['signal']
    
    # Return in format compatible with existing code
    return {
        'candlestick': {
            'signal': combined_signal,
            'confidence': final_analysis['confidence'],
            'description': final_analysis['description'],
            'patterns': final_analysis['pattern_names'],
            'value': combined_signal,  # For compatibility
            'timeframe': final_analysis.get('timeframe', 'unknown')
        },
        # Include minimal ATR for stop-loss calculation (still needed)
        'atr': {
            'value': float(talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)[-1]),
            'percent': float(talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)[-1]) / float(df['Close'].iloc[-1]),
            'signal': 0
        }
    }
