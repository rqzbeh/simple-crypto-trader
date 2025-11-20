"""
Symbol-Specific Trading Strategies
Different cryptocurrencies behave differently - customize strategies per coin
"""

from typing import Dict, Optional
import json
import os

class SymbolStrategyManager:
    """
    Manages symbol-specific trading parameters and strategies
    
    Each cryptocurrency has unique characteristics:
    - BTC: Lower leverage, tighter stops (more stable)
    - DOGE/SHIB: Higher volatility, wider stops
    - ETH/BNB: Medium volatility, balanced approach
    """
    
    def __init__(self, config_file: str = "symbol_strategies.json"):
        self.config_file = config_file
        self.strategies = self._load_strategies()
    
    def _load_strategies(self) -> Dict:
        """Load symbol-specific strategies from config"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default strategies based on coin characteristics
        return {
            "BTC": {
                "name": "Bitcoin - Blue Chip",
                "max_leverage": 8,
                "min_confidence": 0.65,
                "stop_loss_range": [0.8, 2.0],
                "take_profit_range": [2.4, 6.0],
                "volatility_multiplier": 0.9,  # Less aggressive
                "news_weight": 0.85,
                "technical_weight": 0.15,
                "description": "Most stable crypto, lower leverage, tighter stops"
            },
            "ETH": {
                "name": "Ethereum - Blue Chip",
                "max_leverage": 10,
                "min_confidence": 0.60,
                "stop_loss_range": [1.0, 2.5],
                "take_profit_range": [3.0, 7.5],
                "volatility_multiplier": 1.0,
                "news_weight": 0.85,
                "technical_weight": 0.15,
                "description": "Second largest, balanced approach"
            },
            "BNB": {
                "name": "Binance Coin",
                "max_leverage": 10,
                "min_confidence": 0.60,
                "stop_loss_range": [1.0, 2.5],
                "take_profit_range": [3.0, 7.5],
                "volatility_multiplier": 1.0,
                "news_weight": 0.80,
                "technical_weight": 0.20,
                "description": "Exchange token, responds to Binance news"
            },
            "SOL": {
                "name": "Solana - High Growth",
                "max_leverage": 12,
                "min_confidence": 0.55,
                "stop_loss_range": [1.2, 3.0],
                "take_profit_range": [3.6, 9.0],
                "volatility_multiplier": 1.2,
                "news_weight": 0.85,
                "technical_weight": 0.15,
                "description": "High volatility alt, wider stops needed"
            },
            "DOGE": {
                "name": "Dogecoin - Meme Coin",
                "max_leverage": 15,
                "min_confidence": 0.50,
                "stop_loss_range": [1.5, 3.5],
                "take_profit_range": [4.5, 10.5],
                "volatility_multiplier": 1.5,
                "news_weight": 0.90,  # Highly news-driven
                "technical_weight": 0.10,
                "description": "Extreme volatility, social media driven"
            },
            "SHIB": {
                "name": "Shiba Inu - Meme Coin",
                "max_leverage": 15,
                "min_confidence": 0.50,
                "stop_loss_range": [1.5, 3.5],
                "take_profit_range": [4.5, 10.5],
                "volatility_multiplier": 1.5,
                "news_weight": 0.90,
                "technical_weight": 0.10,
                "description": "Extreme volatility, social media driven"
            },
            "XRP": {
                "name": "Ripple - Legal Risk",
                "max_leverage": 10,
                "min_confidence": 0.65,  # Higher confidence needed
                "stop_loss_range": [1.0, 2.5],
                "take_profit_range": [3.0, 7.5],
                "volatility_multiplier": 1.3,
                "news_weight": 0.95,  # Very news sensitive (SEC case)
                "technical_weight": 0.05,
                "description": "Highly reactive to legal news"
            },
            "ADA": {
                "name": "Cardano - Research Driven",
                "max_leverage": 12,
                "min_confidence": 0.55,
                "stop_loss_range": [1.2, 2.8],
                "take_profit_range": [3.6, 8.4],
                "volatility_multiplier": 1.1,
                "news_weight": 0.80,
                "technical_weight": 0.20,
                "description": "Responds to development updates"
            },
            "AVAX": {
                "name": "Avalanche",
                "max_leverage": 12,
                "min_confidence": 0.55,
                "stop_loss_range": [1.2, 3.0],
                "take_profit_range": [3.6, 9.0],
                "volatility_multiplier": 1.2,
                "news_weight": 0.85,
                "technical_weight": 0.15,
                "description": "High growth DeFi platform"
            },
            "LINK": {
                "name": "Chainlink - Oracle Network",
                "max_leverage": 10,
                "min_confidence": 0.60,
                "stop_loss_range": [1.0, 2.5],
                "take_profit_range": [3.0, 7.5],
                "volatility_multiplier": 1.1,
                "news_weight": 0.80,
                "technical_weight": 0.20,
                "description": "Partnership-driven price action"
            },
            "DOT": {
                "name": "Polkadot",
                "max_leverage": 12,
                "min_confidence": 0.55,
                "stop_loss_range": [1.2, 2.8],
                "take_profit_range": [3.6, 8.4],
                "volatility_multiplier": 1.15,
                "news_weight": 0.80,
                "technical_weight": 0.20,
                "description": "Parachain auctions affect price"
            },
            "DEFAULT": {
                "name": "Default Strategy",
                "max_leverage": 10,
                "min_confidence": 0.60,
                "stop_loss_range": [1.0, 2.5],
                "take_profit_range": [3.0, 7.5],
                "volatility_multiplier": 1.0,
                "news_weight": 0.85,
                "technical_weight": 0.15,
                "description": "Balanced approach for unknown symbols"
            }
        }
    
    def get_strategy(self, symbol: str) -> Dict:
        """Get strategy for specific symbol"""
        # Remove -USD suffix if present
        clean_symbol = symbol.replace('-USD', '').replace('USD', '')
        return self.strategies.get(clean_symbol, self.strategies['DEFAULT'])
    
    def adjust_parameters(self, symbol: str, base_params: Dict) -> Dict:
        """
        Adjust trading parameters based on symbol strategy
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'DOGE')
            base_params: Base parameters from main analyzer
        
        Returns:
            Adjusted parameters optimized for this symbol
        """
        strategy = self.get_strategy(symbol)
        adjusted = base_params.copy()
        
        # Adjust leverage
        if 'leverage' in adjusted:
            adjusted['leverage'] = min(adjusted['leverage'], strategy['max_leverage'])
        
        # Adjust confidence requirement
        if 'min_confidence' in adjusted:
            adjusted['min_confidence'] = max(adjusted.get('min_confidence', 0.5), 
                                            strategy['min_confidence'])
        
        # Adjust stop loss based on symbol volatility
        if 'stop_loss_pct' in adjusted:
            sl_min, sl_max = strategy['stop_loss_range']
            current_sl = adjusted['stop_loss_pct']
            # Keep within symbol-specific range
            adjusted['stop_loss_pct'] = max(sl_min, min(sl_max, current_sl))
        
        # Adjust take profit
        if 'take_profit_pct' in adjusted:
            tp_min, tp_max = strategy['take_profit_range']
            current_tp = adjusted['take_profit_pct']
            adjusted['take_profit_pct'] = max(tp_min, min(tp_max, current_tp))
        
        # Adjust volatility sensitivity
        if 'volatility' in adjusted:
            adjusted['volatility'] *= strategy['volatility_multiplier']
        
        return adjusted
    
    def should_trade_symbol(self, symbol: str, confidence: float, 
                           market_conditions: Optional[Dict] = None) -> tuple:
        """
        Determine if symbol should be traded based on its strategy
        
        Returns: (should_trade: bool, reason: str)
        """
        strategy = self.get_strategy(symbol)
        
        # Check minimum confidence
        if confidence < strategy['min_confidence']:
            return False, f"Confidence {confidence:.1%} below {symbol} minimum {strategy['min_confidence']:.1%}"
        
        # Symbol-specific checks
        clean_symbol = symbol.replace('-USD', '').replace('USD', '')
        
        # XRP: Extra caution due to legal issues
        if clean_symbol == 'XRP' and confidence < 0.75:
            return False, "XRP requires >75% confidence due to legal volatility"
        
        # Meme coins: Require very strong signals
        if clean_symbol in ['DOGE', 'SHIB'] and confidence < 0.60:
            return False, f"Meme coin {clean_symbol} requires >60% confidence"
        
        # High volatility check
        if market_conditions:
            volatility = market_conditions.get('volatility', 0)
            if volatility > 0.9 and clean_symbol not in ['DOGE', 'SHIB']:
                return False, f"Volatility {volatility:.1%} too high for {clean_symbol}"
        
        return True, f"Meets {strategy['name']} criteria"
    
    def get_symbol_info(self, symbol: str) -> str:
        """Get formatted info about symbol strategy"""
        strategy = self.get_strategy(symbol)
        return f"""
{strategy['name']}
├─ Max Leverage: {strategy['max_leverage']}x
├─ Min Confidence: {strategy['min_confidence']:.0%}
├─ Stop Loss Range: {strategy['stop_loss_range'][0]:.1f}% - {strategy['stop_loss_range'][1]:.1f}%
├─ Take Profit Range: {strategy['take_profit_range'][0]:.1f}% - {strategy['take_profit_range'][1]:.1f}%
├─ News Weight: {strategy['news_weight']:.0%}
└─ {strategy['description']}
"""
    
    def save_strategies(self):
        """Save current strategies to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.strategies, f, indent=2)
        print(f"[CONFIG] Saved symbol strategies to {self.config_file}")


# Quick test
if __name__ == "__main__":
    manager = SymbolStrategyManager()
    
    print("Symbol-Specific Strategies Test\n")
    print("=" * 60)
    
    test_symbols = ['BTC', 'DOGE', 'ETH', 'XRP']
    
    for symbol in test_symbols:
        print(manager.get_symbol_info(symbol))
        
        # Test parameter adjustment
        base_params = {
            'leverage': 15,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 6.0,
            'min_confidence': 0.5
        }
        
        adjusted = manager.adjust_parameters(symbol, base_params)
        print(f"Base params: {base_params}")
        print(f"Adjusted for {symbol}: {adjusted}")
        
        # Test trade decision
        should_trade, reason = manager.should_trade_symbol(symbol, 0.65)
        print(f"Trade {symbol} at 65% confidence? {should_trade} - {reason}")
        print("=" * 60 + "\n")
