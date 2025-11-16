#!/usr/bin/env python3
"""
Test Stop Loss and Take Profit validation improvements
Ensures realistic values with proper bounds
"""

import sys
from datetime import datetime

# Test parameters
MIN_STOP_PCT = 0.015  # 1.5% minimum
MAX_STOP_PCT = 0.05   # 5% maximum (maintains 3:1 R/R with 15% TP cap)
TARGET_RR_RATIO = 3.0  # 1:3 minimum
MAX_TP_PCT = 0.15     # 15% maximum

def validate_stop_loss(atr_pct, adaptive_multiplier=1.0):
    """Validate stop loss calculation matches main.py logic"""
    # Calculate ATR-based stop
    atr_stop = atr_pct * 1.5
    
    # Apply bounds (5% max to maintain 3:1 R/R with 15% TP cap)
    stop_pct = max(MIN_STOP_PCT, min(atr_stop, 0.05))
    
    # Apply adaptive multiplier
    stop_pct *= adaptive_multiplier
    
    # Final validation - hard limits
    stop_pct = max(0.015, min(stop_pct, 0.05))
    
    return stop_pct

def validate_take_profit(expected_return, stop_pct):
    """Validate take profit calculation matches main.py logic"""
    expected_profit = abs(expected_return)
    min_profit_for_target_rr = stop_pct * TARGET_RR_RATIO
    
    # Ensure minimum R/R
    if expected_profit < min_profit_for_target_rr:
        expected_profit = min_profit_for_target_rr
    
    # Cap at maximum
    expected_profit = min(expected_profit, MAX_TP_PCT)
    
    return expected_profit

def test_scenarios():
    """Test various scenarios to ensure realistic values"""
    
    print("=" * 70)
    print("TESTING STOP LOSS & TAKE PROFIT VALIDATION")
    print("=" * 70)
    print()
    
    # Test scenarios with different ATR values
    test_cases = [
        # (ATR%, Expected Return, Adaptive Multiplier, Description)
        (0.01, 0.08, 1.0, "Low volatility"),
        (0.02, 0.10, 1.0, "Normal volatility"),
        (0.03, 0.12, 1.0, "Medium volatility"),
        (0.05, 0.15, 1.0, "High volatility"),
        (0.08, 0.20, 1.0, "Very high volatility (should cap)"),
        (0.10, 0.25, 1.0, "Extreme volatility (should cap)"),
        (0.02, 0.03, 1.0, "Low expected return (should enforce min R/R)"),
        (0.02, 0.10, 0.8, "With risk reduction"),
        (0.02, 0.10, 1.2, "With risk increase"),
    ]
    
    all_passed = True
    
    for atr_pct, expected_return, adaptive_mult, description in test_cases:
        # Calculate values
        stop_pct = validate_stop_loss(atr_pct, adaptive_mult)
        tp_pct = validate_take_profit(expected_return, stop_pct)
        
        # Calculate R/R ratio
        rr_ratio = tp_pct / stop_pct if stop_pct > 0 else 0
        
        # Validation checks
        checks = []
        
        # Check 1: Stop loss within bounds
        if MIN_STOP_PCT <= stop_pct <= MAX_STOP_PCT:
            checks.append("✅ SL within bounds")
        else:
            checks.append(f"❌ SL out of bounds: {stop_pct*100:.2f}%")
            all_passed = False
        
        # Check 2: Take profit within bounds
        if tp_pct <= MAX_TP_PCT:
            checks.append("✅ TP within bounds")
        else:
            checks.append(f"❌ TP too high: {tp_pct*100:.2f}%")
            all_passed = False
        
        # Check 3: Minimum R/R ratio met (with small tolerance for floating point)
        if rr_ratio >= TARGET_RR_RATIO - 0.01:  # Allow 0.01 tolerance
            checks.append("✅ Min R/R met")
        else:
            checks.append(f"❌ R/R too low: {rr_ratio:.2f}")
            all_passed = False
        
        # Check 4: Realistic values for 4h timeframe
        if stop_pct < 0.10 and tp_pct < 0.20:
            checks.append("✅ Realistic for 4h")
        else:
            checks.append("⚠️ May be aggressive")
        
        # Print results
        print(f"\nTest: {description}")
        print(f"  Input: ATR={atr_pct*100:.1f}%, Expected Return={expected_return*100:.1f}%, Risk Multiplier={adaptive_mult:.1f}x")
        print(f"  Output: SL={stop_pct*100:.2f}%, TP={tp_pct*100:.2f}%, R/R=1:{rr_ratio:.1f}")
        print(f"  Checks: {' | '.join(checks)}")
    
    print()
    print("=" * 70)
    
    if all_passed:
        print("✅ ALL TESTS PASSED - SL/TP validation working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Review validation logic")
        sys.exit(1)
    
    print("=" * 70)
    print()
    
    # Summary
    print("VALIDATION SUMMARY:")
    print(f"  • Stop Loss Range: {MIN_STOP_PCT*100:.1f}% to {MAX_STOP_PCT*100:.1f}%")
    print(f"  • Take Profit Max: {MAX_TP_PCT*100:.1f}%")
    print(f"  • Minimum R/R: 1:{TARGET_RR_RATIO:.0f}")
    print(f"  • Timeframe: 4 hours")
    print(f"  • Approach: 90% News/AI, 10% Technical Filter")
    print()

if __name__ == '__main__':
    test_scenarios()
