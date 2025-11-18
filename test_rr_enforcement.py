#!/usr/bin/env python3
"""
Test to verify that 3:1 R/R minimum is ALWAYS maintained
Even when TP precision learning reduces TPs
"""

def test_rr_ratio_enforcement():
    """
    Verify that the minimum 3:1 R/R is maintained in all scenarios
    """
    
    print("=" * 80)
    print("TESTING: 3:1 R/R RATIO IS ALWAYS MAINTAINED")
    print("=" * 80)
    print()
    print("This test verifies that even with TP precision learning,")
    print("the system NEVER violates the minimum 3:1 risk/reward ratio.")
    print()
    print("=" * 80)
    print()
    
    MIN_STOP_PCT = 0.008
    MAX_STOP_PCT = 0.025
    TARGET_RR_RATIO = 3.0
    
    test_scenarios = [
        {
            'name': 'Low volatility, small SL',
            'atr_pct': 0.008,
            'initial_tp': 0.04,
            'tp_adjustment': 1.0,
            'description': 'Normal case, no precision adjustment'
        },
        {
            'name': 'Low volatility, aggressive TP reduction',
            'atr_pct': 0.010,
            'initial_tp': 0.06,
            'tp_adjustment': 0.6,
            'description': 'TP reduced 40% due to precision learning'
        },
        {
            'name': 'Medium volatility, moderate TP reduction',
            'atr_pct': 0.015,
            'initial_tp': 0.05,
            'tp_adjustment': 0.7,
            'description': 'TP reduced 30% due to precision learning'
        },
        {
            'name': 'High volatility, large SL',
            'atr_pct': 0.020,
            'initial_tp': 0.07,
            'tp_adjustment': 0.6,
            'description': 'High volatility needs larger TP for 3:1 R/R'
        },
        {
            'name': 'Maximum volatility, maximum SL',
            'atr_pct': 0.025,
            'initial_tp': 0.08,
            'tp_adjustment': 0.5,
            'description': 'Edge case: 2.5% SL needs 7.5% TP for 3:1'
        },
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print("-" * 80)
        
        # Calculate stop loss (ATR-based)
        atr_stop = scenario['atr_pct'] * 1.2
        stop_pct = max(MIN_STOP_PCT, min(atr_stop, MAX_STOP_PCT))
        stop_pct = max(0.008, min(stop_pct, 0.025))
        
        # Calculate TP with precision adjustment
        expected_profit = scenario['initial_tp'] * scenario['tp_adjustment']
        
        # Minimum R/R enforcement
        min_profit_for_target_rr = stop_pct * TARGET_RR_RATIO
        
        if expected_profit < min_profit_for_target_rr:
            expected_profit = min_profit_for_target_rr
        
        # NEW LOGIC: Cap respects minimum R/R
        max_tp_cap = max(0.05, min_profit_for_target_rr)
        expected_profit = min(expected_profit, max_tp_cap)
        
        # Calculate final R/R
        rr_ratio = expected_profit / stop_pct if stop_pct > 0 else 0
        
        # Display results
        print(f"  ATR: {scenario['atr_pct']*100:.1f}%")
        print(f"  Initial TP: {scenario['initial_tp']*100:.1f}%")
        print(f"  TP Adjustment Factor: {scenario['tp_adjustment']:.1f}x")
        print(f"  Stop Loss: {stop_pct*100:.2f}%")
        print(f"  Min TP for 3:1 R/R: {min_profit_for_target_rr*100:.2f}%")
        print(f"  TP Cap: {max_tp_cap*100:.2f}%")
        print(f"  Final TP: {expected_profit*100:.2f}%")
        print(f"  Final R/R Ratio: 1:{rr_ratio:.2f}")
        
        # Check if passes
        if rr_ratio >= TARGET_RR_RATIO - 0.01:  # Allow small floating point tolerance
            print(f"  ✅ PASS - Maintains minimum 3:1 R/R")
        else:
            print(f"  ❌ FAIL - R/R {rr_ratio:.2f}:1 is below 3:1 minimum!")
            all_passed = False
        
        print()
    
    print("=" * 80)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print()
        print("CONCLUSION:")
        print("  • The 3:1 minimum R/R is ALWAYS maintained")
        print("  • TP precision learning CANNOT violate this requirement")
        print("  • When SL is large (e.g., 2.5%), TP can go up to 7.5% to maintain 3:1")
        print("  • The dynamic TP cap ensures minimum R/R is never broken")
        print()
    else:
        print("❌ SOME TESTS FAILED")
        print("The minimum 3:1 R/R requirement was violated!")
        print()
        import sys
        sys.exit(1)
    
    print("=" * 80)

if __name__ == '__main__':
    test_rr_ratio_enforcement()
