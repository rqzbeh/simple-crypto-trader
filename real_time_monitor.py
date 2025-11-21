"""
Real-Time Monitoring System for Active Trades
Track open positions, price movements, and exit signals
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
from collections import defaultdict

class TradeMonitor:
    """
    Real-time monitoring for active trades
    
    Features:
    - Track open positions
    - Monitor stop loss / take profit levels
    - Alert on price movements
    - Auto-exit recommendations
    - Performance tracking
    """
    
    def __init__(self, positions_file: str = "active_positions.json"):
        self.positions_file = positions_file
        self.positions = self._load_positions()
        self.alerts = []
    
    def _load_positions(self) -> List[Dict]:
        """Load active positions"""
        if os.path.exists(self.positions_file):
            try:
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_positions(self):
        """Save positions to file"""
        with open(self.positions_file, 'w') as f:
            json.dump(self.positions, f, indent=2)
    
    def add_position(self, symbol: str, direction: str, entry_price: float,
                    stop_loss: float, take_profit: float, leverage: int,
                    confidence: float, signal_time: str, reasoning: str = ""):
        """
        Add new position to monitoring
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC-USD')
            direction: 'LONG' or 'SHORT'
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            leverage: Leverage used
            confidence: Signal confidence (0-1)
            signal_time: Timestamp of signal
            reasoning: AI reasoning for trade
        """
        position = {
            'id': f"{symbol}_{int(time.time())}",
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'leverage': leverage,
            'confidence': confidence,
            'entry_time': signal_time,
            'reasoning': reasoning,
            'status': 'ACTIVE',
            'current_price': entry_price,
            'current_pnl_pct': 0.0,
            'max_profit_pct': 0.0,
            'max_loss_pct': 0.0,
            'alerts': []
        }
        
        self.positions.append(position)
        self._save_positions()
        print(f"[MONITOR] Added {symbol} {direction} position to monitoring")
        return position['id']
    
    def update_prices(self) -> List[Dict]:
        """
        Update current prices for all active positions
        Returns list of positions with alerts
        """
        alerts = []
        
        for position in self.positions:
            if position['status'] != 'ACTIVE':
                continue
            
            try:
                # Get current price
                ticker = yf.Ticker(position['symbol'])
                current_data = ticker.history(period='1d', interval='1m')
                
                if current_data.empty:
                    continue
                
                current_price = current_data['Close'].iloc[-1]
                position['current_price'] = current_price
                position['last_update'] = datetime.now().isoformat()
                
                # Calculate PnL
                entry = position['entry_price']
                direction = position['direction']
                
                if direction == 'LONG':
                    pnl_pct = ((current_price - entry) / entry) * 100
                elif direction == 'SHORT':
                    pnl_pct = ((entry - current_price) / entry) * 100
                else:
                    pnl_pct = 0
                
                position['current_pnl_pct'] = pnl_pct
                
                # Track max profit/loss
                position['max_profit_pct'] = max(position['max_profit_pct'], pnl_pct)
                position['max_loss_pct'] = min(position['max_loss_pct'], pnl_pct)
                
                # Check for exit conditions
                alert = self._check_exit_conditions(position)
                if alert:
                    alerts.append(alert)
                
            except Exception as e:
                print(f"[MONITOR] Error updating {position['symbol']}: {e}")
        
        self._save_positions()
        return alerts
    
    def _check_exit_conditions(self, position: Dict) -> Optional[Dict]:
        """Check if position should be exited"""
        current_price = position['current_price']
        entry_price = position['entry_price']
        sl = position['stop_loss']
        tp = position['take_profit']
        direction = position['direction']
        
        # Stop Loss Hit
        if direction == 'LONG' and current_price <= sl:
            return {
                'type': 'STOP_LOSS',
                'position_id': position['id'],
                'symbol': position['symbol'],
                'message': f"🛑 STOP LOSS HIT: {position['symbol']} at ${current_price:.4f}",
                'action': 'EXIT_NOW',
                'pnl_pct': position['current_pnl_pct']
            }
        
        if direction == 'SHORT' and current_price >= sl:
            return {
                'type': 'STOP_LOSS',
                'position_id': position['id'],
                'symbol': position['symbol'],
                'message': f"🛑 STOP LOSS HIT: {position['symbol']} at ${current_price:.4f}",
                'action': 'EXIT_NOW',
                'pnl_pct': position['current_pnl_pct']
            }
        
        # Take Profit Hit
        if direction == 'LONG' and current_price >= tp:
            return {
                'type': 'TAKE_PROFIT',
                'position_id': position['id'],
                'symbol': position['symbol'],
                'message': f"🎯 TAKE PROFIT HIT: {position['symbol']} at ${current_price:.4f}",
                'action': 'EXIT_NOW',
                'pnl_pct': position['current_pnl_pct']
            }
        
        if direction == 'SHORT' and current_price <= tp:
            return {
                'type': 'TAKE_PROFIT',
                'position_id': position['id'],
                'symbol': position['symbol'],
                'message': f"🎯 TAKE PROFIT HIT: {position['symbol']} at ${current_price:.4f}",
                'action': 'EXIT_NOW',
                'pnl_pct': position['current_pnl_pct']
            }
        
        # Near stop loss warning (within 10%)
        if direction == 'LONG':
            distance_to_sl = ((current_price - sl) / entry_price) * 100
            if 0 < distance_to_sl < 0.5:  # Within 0.5% of SL
                return {
                    'type': 'WARNING',
                    'position_id': position['id'],
                    'symbol': position['symbol'],
                    'message': f"⚠️  NEAR STOP LOSS: {position['symbol']} ({distance_to_sl:.2f}% away)",
                    'action': 'MONITOR_CLOSELY',
                    'pnl_pct': position['current_pnl_pct']
                }
        
        if direction == 'SHORT':
            distance_to_sl = ((sl - current_price) / entry_price) * 100
            if 0 < distance_to_sl < 0.5:
                return {
                    'type': 'WARNING',
                    'position_id': position['id'],
                    'symbol': position['symbol'],
                    'message': f"⚠️  NEAR STOP LOSS: {position['symbol']} ({distance_to_sl:.2f}% away)",
                    'action': 'MONITOR_CLOSELY',
                    'pnl_pct': position['current_pnl_pct']
                }
        
        # Time-based exit (2 hours max)
        entry_time = datetime.fromisoformat(position['entry_time'])
        time_elapsed = datetime.now() - entry_time
        
        if time_elapsed > timedelta(hours=2):
            return {
                'type': 'TIME_EXIT',
                'position_id': position['id'],
                'symbol': position['symbol'],
                'message': f"⏰ TIME LIMIT: {position['symbol']} (2 hours elapsed)",
                'action': 'CONSIDER_EXIT',
                'pnl_pct': position['current_pnl_pct']
            }
        
        return None
    
    def close_position(self, position_id: str, exit_price: float, 
                      reason: str = "Manual") -> Dict:
        """
        Close a position
        
        Returns:
            Trade summary
        """
        position = next((p for p in self.positions if p['id'] == position_id), None)
        
        if not position:
            return {'error': 'Position not found'}
        
        # Calculate final PnL
        entry = position['entry_price']
        direction = position['direction']
        leverage = position['leverage']
        
        if direction == 'LONG':
            pnl_pct = ((exit_price - entry) / entry) * 100
        else:
            pnl_pct = ((entry - exit_price) / entry) * 100
        
        leveraged_pnl = pnl_pct * leverage
        
        # Update position
        position['status'] = 'CLOSED'
        position['exit_price'] = exit_price
        position['exit_time'] = datetime.now().isoformat()
        position['exit_reason'] = reason
        position['final_pnl_pct'] = pnl_pct
        position['leveraged_pnl_pct'] = leveraged_pnl
        
        self._save_positions()
        
        return {
            'symbol': position['symbol'],
            'direction': direction,
            'entry_price': entry,
            'exit_price': exit_price,
            'pnl_pct': pnl_pct,
            'leveraged_pnl_pct': leveraged_pnl,
            'duration': position.get('exit_time', '')
        }
    
    def get_active_positions(self) -> List[Dict]:
        """Get all active positions"""
        return [p for p in self.positions if p['status'] == 'ACTIVE']
    
    def print_dashboard(self):
        """Print real-time monitoring dashboard"""
        active = self.get_active_positions()
        
        if not active:
            print("\n📊 No active positions being monitored")
            return
        
        print("\n" + "=" * 80)
        print("📊 REAL-TIME POSITION MONITOR")
        print("=" * 80)
        
        total_pnl = sum(p['current_pnl_pct'] * p['leverage'] for p in active)
        
        print(f"\nActive Positions: {len(active)}")
        print(f"Total PnL (Leveraged): {total_pnl:+.2f}%\n")
        
        for i, pos in enumerate(active, 1):
            symbol = pos['symbol']
            direction = pos['direction']
            entry = pos['entry_price']
            current = pos['current_price']
            pnl = pos['current_pnl_pct']
            lev_pnl = pnl * pos['leverage']
            
            # Time elapsed
            entry_time = datetime.fromisoformat(pos['entry_time'])
            elapsed = datetime.now() - entry_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            
            # Distance to SL/TP
            sl_dist = abs(current - pos['stop_loss']) / entry * 100
            tp_dist = abs(pos['take_profit'] - current) / entry * 100
            
            status_emoji = "🟢" if lev_pnl > 0 else "🔴" if lev_pnl < 0 else "⚪"
            
            print(f"{status_emoji} Position #{i}: {symbol} {direction}")
            print(f"   Entry: ${entry:.4f} | Current: ${current:.4f}")
            print(f"   PnL: {pnl:+.2f}% | Leveraged ({pos['leverage']}x): {lev_pnl:+.2f}%")
            print(f"   Time: {hours}h {minutes}m | Max Gain: {pos['max_profit_pct']:+.2f}% | Max Loss: {pos['max_loss_pct']:+.2f}%")
            print(f"   Distance to SL: {sl_dist:.2f}% | Distance to TP: {tp_dist:.2f}%")
            print(f"   Confidence: {pos['confidence']:.1%}")
            if pos.get('reasoning'):
                print(f"   Reason: {pos['reasoning'][:60]}...")
            print()
        
        print("=" * 80)


# Quick test
if __name__ == "__main__":
    monitor = TradeMonitor()
    
    print("🧪 REAL-TIME MONITOR TEST\n")
    
    # Show current dashboard
    monitor.print_dashboard()
    
    # Update prices
    print("\n📡 Updating prices...")
    alerts = monitor.update_prices()
    
    if alerts:
        print("\n🚨 ALERTS:")
        for alert in alerts:
            print(f"   {alert['message']}")
            print(f"   Action: {alert['action']}")
            print(f"   PnL: {alert['pnl_pct']:+.2f}%\n")
    
    # Show updated dashboard
    monitor.print_dashboard()
