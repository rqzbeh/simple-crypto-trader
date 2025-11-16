#!/usr/bin/env python3
"""
Test the adaptive learning system with simulated trades
"""

from llm_analyzer import CryptoMarketAnalyzer
import random

def simulate_trade_outcomes():
    """Simulate trades to test the learning system"""
    
    print("=" * 70)
    print("TESTING ADAPTIVE LEARNING SYSTEM")
    print("=" * 70)
    print()
    
    analyzer = CryptoMarketAnalyzer(None)
    
    # Simulate 30 trades with various outcomes
    indicators = ['stoch_rsi', 'ema_trend', 'macd', 'supertrend', 'adx', 
                  'bb', 'obv', 'vwap', 'pivot_points']
    
    print("Simulating 30 trades...\n")
    
    for i in range(30):
        # Create realistic indicator signals
        indicator_signals = {}
        for ind in indicators:
            # Some indicators are more accurate than others in simulation
            if ind in ['ema_trend', 'supertrend', 'vwap']:
                # These are "good" indicators in our simulation (70% accuracy)
                signal = 1 if random.random() > 0.3 else -1
            elif ind in ['stoch_rsi', 'macd']:
                # Medium indicators (55% accuracy)
                signal = 1 if random.random() > 0.45 else -1
            else:
                # Weaker indicators (40% accuracy)
                signal = 1 if random.random() > 0.6 else -1
            
            indicator_signals[ind] = signal
        
        # Simulate profit based on indicator agreement
        # If more indicators agree, higher chance of profit
        positive_signals = sum(1 for s in indicator_signals.values() if s > 0)
        agreement = positive_signals / len(indicator_signals)
        
        # More agreement = better chance of profit
        if agreement > 0.65 or agreement < 0.35:
            # Strong agreement (bullish or bearish)
            profit = random.uniform(0.02, 0.08) if random.random() > 0.3 else random.uniform(-0.03, -0.01)
        else:
            # Weak agreement
            profit = random.uniform(-0.04, 0.04)
        
        # Feed to learning system
        trade_result = {
            'profit': profit,
            'indicators': indicator_signals,
            'symbol': 'BTC',
            'direction': 'LONG' if positive_signals > len(indicators)/2 else 'SHORT'
        }
        
        analyzer.learn_from_trade(trade_result)
        
        if (i + 1) % 10 == 0:
            print(f"✓ Completed {i + 1} trades")
    
    print()
    print("=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    
    summary = analyzer.get_performance_summary()
    print(f"\nTotal Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']*100:.1f}%")
    print(f"Average Profit: {summary['avg_profit']*100:.2f}%")
    print(f"Confidence Threshold: {summary['confidence_threshold']:.2f}")
    print(f"Risk Multiplier: {summary['risk_multiplier']:.2f}")
    
    print(f"\nTop 5 Best Indicators:")
    for indicator, accuracy in summary['best_indicators']:
        print(f"  {indicator:15} - {accuracy*100:.1f}% accuracy")
    
    print()
    print("=" * 70)
    print("✅ LEARNING SYSTEM TEST COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    simulate_trade_outcomes()
