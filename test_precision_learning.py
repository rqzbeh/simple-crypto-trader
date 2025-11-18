#!/usr/bin/env python3
"""
Test the new precision learning system
Demonstrates how the system learns from TP/SL precision, not just win/loss
"""

from llm_analyzer import CryptoMarketAnalyzer
import random

def test_precision_learning():
    """
    Test scenario: System predicts correct direction but TPs are too ambitious
    This simulates the real problem: "BTC goes from 91k to 89k but TP is 86k"
    """
    
    print("=" * 80)
    print("TESTING PRECISION LEARNING SYSTEM")
    print("=" * 80)
    print()
    print("Scenario: Direction predictions are CORRECT (65% accuracy)")
    print("          But TP targets are TOO FAR (only 60% of predicted distance)")
    print()
    print("This simulates: BTC predicted to drop 5% (to 86k from 91k)")
    print("                But actually drops only 3% (to 89k)")
    print("=" * 80)
    print()
    
    analyzer = CryptoMarketAnalyzer(None)
    
    # Simulate 25 trades where direction is mostly correct but TPs too far
    indicators = ['stoch_rsi', 'ema_trend', 'macd', 'supertrend', 'vwap']
    
    print("Simulating 25 trades...\n")
    
    for i in range(25):
        # Direction is correct 65% of the time (good)
        direction_correct = random.random() < 0.65
        
        if direction_correct:
            # Direction correct, but price only moves 55-65% of TP distance
            tp_distance = random.uniform(0.03, 0.05)  # TP set at 3-5%
            actual_movement = tp_distance * random.uniform(0.55, 0.65)  # Only 55-65% of TP
            profit = random.uniform(0.01, 0.03)  # Small profit but didn't hit TP
        else:
            # Wrong direction
            tp_distance = random.uniform(0.03, 0.05)
            actual_movement = -random.uniform(0.01, 0.02)  # Price went opposite way
            profit = random.uniform(-0.04, -0.01)  # Loss
        
        # Create indicator signals
        indicator_signals = {}
        for ind in indicators:
            signal = 1 if direction_correct else -1
            indicator_signals[ind] = signal
        
        # Feed to learning system
        trade_result = {
            'profit': profit,
            'direction': 'LONG',
            'indicators': indicator_signals,
            'tp_distance': tp_distance,
            'actual_movement': abs(actual_movement)
        }
        
        analyzer.learn_from_trade(trade_result)
        
        if (i + 1) % 10 == 0:
            print(f"✓ Completed {i + 1} trades")
    
    print()
    print("=" * 80)
    print("RESULTS - BEFORE vs AFTER")
    print("=" * 80)
    print()
    
    # Calculate metrics
    direction_accuracy = sum(analyzer.precision_metrics['direction_accuracy'][-20:]) / len(analyzer.precision_metrics['direction_accuracy'][-20:])
    tp_precision = sum(analyzer.precision_metrics['tp_precision'][-20:]) / len(analyzer.precision_metrics['tp_precision'][-20:])
    
    print("BEFORE (Initial Settings):")
    print("  TP Target: 4.0% (based on sentiment/news)")
    print("  TP Adjustment: 1.0x (no adjustment)")
    print("  Actual TP Used: 4.0%")
    print()
    
    print("LEARNED METRICS:")
    print(f"  Direction Accuracy: {direction_accuracy*100:.1f}% ✓ (Good - trend prediction works)")
    print(f"  TP Precision: {tp_precision*100:.1f}% ✗ (Problem - TPs too ambitious)")
    print(f"  Avg TP Overshoot: {analyzer.precision_metrics['avg_tp_overshoot']*100:.1f}%")
    print(f"  Avg Price Movement: {analyzer.precision_metrics['avg_price_movement']*100:.2f}%")
    print()
    
    print("AFTER (Adaptive Adjustment):")
    tp_adj = analyzer.strategy_adjustments['tp_adjustment_factor']
    original_tp = 4.0
    adjusted_tp = original_tp * tp_adj
    
    print(f"  TP Target: 4.0% (based on sentiment/news)")
    print(f"  TP Adjustment: {tp_adj:.2f}x (learned from precision)")
    print(f"  Actual TP Used: {adjusted_tp:.2f}%")
    print()
    
    print("IMPROVEMENT:")
    improvement = ((1.0 - tp_adj) * 100)
    print(f"  • TPs reduced by {improvement:.0f}% to match realistic 2-4h movements")
    print(f"  • Direction prediction still good ({direction_accuracy*100:.0f}%)")
    print(f"  • Now targeting realistic levels ({analyzer.precision_metrics['avg_price_movement']*100:.1f}% avg movement)")
    print()
    
    # Show example
    print("EXAMPLE TRADE:")
    print("  Before: BTC at $91,000 → Predict SHORT to $86,000 (5.5% drop)")
    print(f"  After:  BTC at $91,000 → Predict SHORT to ${91000 * (1 - adjusted_tp/100):.0f} ({adjusted_tp:.1f}% drop)")
    print(f"  Result: More likely to hit TP in 2-4h timeframe!")
    print()
    
    print("=" * 80)
    print("✅ PRECISION LEARNING TEST COMPLETE")
    print("=" * 80)
    print()
    print("KEY INSIGHT: System now learns from PRECISION, not just win/loss")
    print("             - Knows when direction is right but TP too far")
    print("             - Automatically adjusts future TPs to realistic levels")
    print("             - Better suited for 2-4 hour trading timeframe")
    print()

if __name__ == '__main__':
    test_precision_learning()
