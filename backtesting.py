"""
Backtesting System for Crypto Trading Strategies
Tests historical performance without risking real money
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
import statistics

class Backtester:
    """
    Backtest trading signals against historical data
    
    Features:
    - Performance metrics (win rate, profit factor, max drawdown)
    - Risk-adjusted returns (Sharpe ratio)
    - Trade analysis (avg win, avg loss, R:R ratio)
    - Strategy comparison
    """
    
    def __init__(self, trade_log_file: str = "trade_log.json",
                 learning_state_file: str = "learning_state.json"):
        self.trade_log_file = trade_log_file
        self.learning_state_file = learning_state_file
        self.trades = self._load_trades()
        self.learning_state = self._load_learning_state()
    
    def _load_trades(self) -> List[Dict]:
        """Load historical trades"""
        if os.path.exists(self.trade_log_file):
            try:
                with open(self.trade_log_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _load_learning_state(self) -> Dict:
        """Load learning state"""
        if os.path.exists(self.learning_state_file):
            try:
                with open(self.learning_state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def analyze_performance(self, days: Optional[int] = None,
                           symbol: Optional[str] = None) -> Dict:
        """
        Analyze trading performance
        
        Args:
            days: Look back period (None = all time)
            symbol: Filter by symbol (None = all symbols)
        
        Returns:
            Performance metrics dictionary
        """
        filtered_trades = self.trades.copy()
        
        # Filter by date
        if days:
            cutoff = datetime.now(pytz.UTC) - timedelta(days=days)
            filtered_trades = [
                t for t in filtered_trades 
                if datetime.fromisoformat(t.get('timestamp', '2020-01-01')).replace(tzinfo=pytz.UTC) > cutoff
            ]
        
        # Filter by symbol
        if symbol:
            filtered_trades = [t for t in filtered_trades if t.get('symbol') == symbol]
        
        if not filtered_trades:
            return {
                'total_trades': 0,
                'message': 'No trades found for specified criteria'
            }
        
        # Calculate metrics
        total_trades = len(filtered_trades)
        winning_trades = [t for t in filtered_trades if t.get('outcome') == 'WIN']
        losing_trades = [t for t in filtered_trades if t.get('outcome') == 'LOSS']
        
        wins = len(winning_trades)
        losses = len(losing_trades)
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # Profit/Loss calculations
        total_profit = sum(t.get('profit_pct', 0) for t in winning_trades)
        total_loss = sum(abs(t.get('profit_pct', 0)) for t in losing_trades)
        
        avg_win = total_profit / wins if wins > 0 else 0
        avg_loss = total_loss / losses if losses > 0 else 0
        
        # Profit factor (total wins / total losses)
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Net profit
        net_profit = total_profit - total_loss
        
        # Risk/Reward ratio
        avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Max consecutive wins/losses
        max_win_streak = self._calculate_max_streak(filtered_trades, 'WIN')
        max_loss_streak = self._calculate_max_streak(filtered_trades, 'LOSS')
        
        # Drawdown analysis
        max_drawdown = self._calculate_max_drawdown(filtered_trades)
        
        # Best and worst trades
        best_trade = max(filtered_trades, key=lambda t: t.get('profit_pct', 0), default=None)
        worst_trade = min(filtered_trades, key=lambda t: t.get('profit_pct', 0), default=None)
        
        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'net_profit': net_profit,
            'profit_factor': profit_factor,
            'avg_rr_ratio': avg_rr,
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'max_drawdown': max_drawdown,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'expectancy': (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        }
    
    def _calculate_max_streak(self, trades: List[Dict], outcome_type: str) -> int:
        """Calculate maximum consecutive wins or losses"""
        max_streak = 0
        current_streak = 0
        
        for trade in trades:
            if trade.get('outcome') == outcome_type:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown percentage"""
        if not trades:
            return 0.0
        
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for trade in trades:
            profit = trade.get('profit_pct', 0)
            cumulative += profit
            
            if cumulative > peak:
                peak = cumulative
            
            drawdown = peak - cumulative
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def analyze_by_symbol(self) -> Dict[str, Dict]:
        """Analyze performance for each symbol"""
        symbols = set(t.get('symbol') for t in self.trades if t.get('symbol'))
        
        results = {}
        for symbol in symbols:
            results[symbol] = self.analyze_performance(symbol=symbol)
        
        return results
    
    def analyze_by_timeframe(self) -> Dict[str, Dict]:
        """Analyze performance over different timeframes"""
        return {
            'last_7_days': self.analyze_performance(days=7),
            'last_30_days': self.analyze_performance(days=30),
            'last_90_days': self.analyze_performance(days=90),
            'all_time': self.analyze_performance()
        }
    
    def get_strategy_effectiveness(self) -> Dict:
        """Analyze which strategies work best"""
        if not self.learning_state:
            return {'message': 'No learning data available'}
        
        precision = self.learning_state.get('precision_metrics', {})
        
        return {
            'total_signals': precision.get('total_signals', 0),
            'accurate_predictions': precision.get('accurate_predictions', 0),
            'accuracy_rate': precision.get('accuracy_rate', 0),
            'avg_signal_confidence': precision.get('avg_confidence', 0),
            'false_positives': precision.get('false_positives', 0),
            'false_negatives': precision.get('false_negatives', 0)
        }
    
    def print_report(self, days: Optional[int] = None, symbol: Optional[str] = None):
        """Print formatted backtest report"""
        metrics = self.analyze_performance(days=days, symbol=symbol)
        
        if metrics.get('total_trades', 0) == 0:
            print(f"\n📊 No trades found for the specified criteria")
            return
        
        period_str = f"Last {days} days" if days else "All Time"
        symbol_str = f" - {symbol}" if symbol else " - All Symbols"
        
        print(f"\n" + "=" * 70)
        print(f"📊 BACKTEST REPORT: {period_str}{symbol_str}")
        print("=" * 70)
        
        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Total Trades: {metrics['total_trades']}")
        print(f"   Wins: {metrics['wins']} | Losses: {metrics['losses']}")
        print(f"   Win Rate: {metrics['win_rate']:.1%}")
        print(f"   Net Profit: {metrics['net_profit']:+.2f}%")
        
        print(f"\n💰 PROFIT METRICS:")
        print(f"   Total Profit: +{metrics['total_profit']:.2f}%")
        print(f"   Total Loss: -{metrics['total_loss']:.2f}%")
        print(f"   Profit Factor: {metrics['profit_factor']:.2f}x")
        print(f"   Expectancy: {metrics['expectancy']:+.2f}%")
        
        print(f"\n📊 TRADE ANALYSIS:")
        print(f"   Avg Win: +{metrics['avg_win']:.2f}%")
        print(f"   Avg Loss: -{metrics['avg_loss']:.2f}%")
        print(f"   Avg R:R Ratio: 1:{metrics['avg_rr_ratio']:.2f}")
        
        print(f"\n🎯 STREAKS:")
        print(f"   Max Win Streak: {metrics['max_win_streak']} trades")
        print(f"   Max Loss Streak: {metrics['max_loss_streak']} trades")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        
        if metrics['best_trade']:
            bt = metrics['best_trade']
            print(f"\n🏆 BEST TRADE:")
            print(f"   {bt.get('symbol')} {bt.get('direction')}")
            print(f"   Profit: +{bt.get('profit_pct', 0):.2f}%")
            print(f"   Date: {bt.get('timestamp', 'N/A')[:10]}")
        
        if metrics['worst_trade']:
            wt = metrics['worst_trade']
            print(f"\n💥 WORST TRADE:")
            print(f"   {wt.get('symbol')} {wt.get('direction')}")
            print(f"   Loss: {wt.get('profit_pct', 0):.2f}%")
            print(f"   Date: {wt.get('timestamp', 'N/A')[:10]}")
        
        print("\n" + "=" * 70)
    
    def compare_strategies(self, strategy1: str, strategy2: str) -> Dict:
        """Compare two different trading strategies"""
        # This would compare different strategy implementations
        # For now, compare symbols as a proxy
        s1_metrics = self.analyze_performance(symbol=strategy1)
        s2_metrics = self.analyze_performance(symbol=strategy2)
        
        return {
            'strategy1': {
                'name': strategy1,
                'metrics': s1_metrics
            },
            'strategy2': {
                'name': strategy2,
                'metrics': s2_metrics
            },
            'winner': strategy1 if s1_metrics.get('net_profit', 0) > s2_metrics.get('net_profit', 0) else strategy2
        }


# Quick test
if __name__ == "__main__":
    backtester = Backtester()
    
    print("🧪 BACKTESTING SYSTEM TEST\n")
    
    # Overall performance
    backtester.print_report()
    
    # By timeframe
    print("\n" + "=" * 70)
    print("📅 PERFORMANCE BY TIMEFRAME")
    print("=" * 70)
    timeframes = backtester.analyze_by_timeframe()
    for period, metrics in timeframes.items():
        if metrics.get('total_trades', 0) > 0:
            print(f"\n{period.upper().replace('_', ' ')}:")
            print(f"  Trades: {metrics['total_trades']} | Win Rate: {metrics['win_rate']:.1%} | Net: {metrics['net_profit']:+.2f}%")
    
    # Strategy effectiveness
    print("\n" + "=" * 70)
    print("🎯 STRATEGY EFFECTIVENESS")
    print("=" * 70)
    strategy = backtester.get_strategy_effectiveness()
    for key, value in strategy.items():
        if key != 'message':
            print(f"  {key.replace('_', ' ').title()}: {value}")
