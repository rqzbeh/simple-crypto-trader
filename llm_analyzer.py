"""
Crypto Market Analyzer - LLM-Powered Analysis Layer
Inspired by AI-Trader's agent-based approach with our proven technical indicators
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class CryptoMarketAnalyzer:
    """
    Advanced market analyzer that combines:
    1. Proven technical indicators (our approach)
    2. LLM reasoning (AI-Trader approach)
    3. Adaptive learning from past trades
    """
    
    def __init__(self, groq_client=None):
        self.groq_client = groq_client
        self.performance_history = []
        self.strategy_adjustments = {
            'indicator_weights': {},
            'risk_multiplier': 1.0,
            'confidence_threshold': 0.3
        }
    
    def analyze_with_llm(self, symbol: str, market_data: Dict, sentiment_data: Dict, 
                        news_articles: List[Dict]) -> Dict[str, Any]:
        """
        Use LLM to analyze market data and make trading decision
        Similar to AI-Trader's agent-based reasoning
        """
        if not self.groq_client:
            return {'llm_available': False}
        
        # Prepare comprehensive market summary for LLM
        indicators = market_data['indicators']
        
        # Extract key signals
        strong_signals = []
        weak_signals = []
        
        for ind_name, ind_data in indicators.items():
            if isinstance(ind_data, dict) and 'signal' in ind_data:
                signal = ind_data['signal']
                if abs(signal) == 1:
                    direction = "BULLISH" if signal > 0 else "BEARISH"
                    strong_signals.append(f"{ind_name.upper()}: {direction}")
                elif signal == 0:
                    weak_signals.append(ind_name.upper())
        
        # Build comprehensive prompt
        prompt = f"""You are an expert cryptocurrency trader analyzing {symbol}.

CURRENT MARKET DATA:
Price: ${market_data['price']:.2f}
Volatility: {market_data['volatility']*100:.2f}% (annualized)
ATR: {market_data['atr_pct']*100:.2f}%

TECHNICAL INDICATORS:
Strong Signals: {', '.join(strong_signals) if strong_signals else 'None'}
Neutral Signals: {', '.join(weak_signals[:5]) if weak_signals else 'None'}

RSI: {indicators['rsi']['value']:.1f} (Oversold<30, Overbought>70)
Stochastic RSI: {indicators['stoch_rsi']['value']:.1f}
MACD Histogram: {indicators['macd']['value']:.4f}
Price vs VWAP: {"Above" if indicators['vwap']['signal'] > 0 else "Below"}
Bollinger Band Position: {indicators['bb']['position']*100:.1f}%
ADX (Trend Strength): {indicators['adx']['value']:.1f} (Strong>25)
Supertrend: {"BULLISH" if indicators['supertrend']['signal'] > 0 else "BEARISH"}

SENTIMENT ANALYSIS:
Score: {sentiment_data.get('score', 0):.2f} (-1 to +1 scale)
News Count: {len(news_articles)} articles
Recent Headlines: {', '.join([a.get('title', '')[:60] for a in news_articles[:3]])}

TASK:
Analyze this data and provide:
1. Trading Direction (LONG/SHORT/NEUTRAL)
2. Confidence Level (0-100%)
3. Key Reasoning (2-3 sentences)
4. Risk Assessment (LOW/MEDIUM/HIGH)
5. Recommended holding period (HOURS/DAYS/WEEK)

Format your response as:
DIRECTION: [LONG/SHORT/NEUTRAL]
CONFIDENCE: [0-100]
REASONING: [Your analysis]
RISK: [LOW/MEDIUM/HIGH]
TIMEFRAME: [HOURS/DAYS/WEEK]"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Larger model for better analysis
                messages=[{
                    "role": "system",
                    "content": "You are an expert cryptocurrency trader with deep knowledge of technical analysis, market psychology, and risk management."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            
            # Parse LLM response
            analysis = self._parse_llm_response(result)
            analysis['raw_response'] = result
            analysis['llm_available'] = True
            
            return analysis
            
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return {'llm_available': False, 'error': str(e)}
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse structured LLM response"""
        import re
        
        parsed = {
            'direction': 'NEUTRAL',
            'confidence': 50,
            'reasoning': '',
            'risk': 'MEDIUM',
            'timeframe': 'HOURS'
        }
        
        # Extract direction
        direction_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NEUTRAL)', response, re.I)
        if direction_match:
            parsed['direction'] = direction_match.group(1).upper()
        
        # Extract confidence
        confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', response)
        if confidence_match:
            parsed['confidence'] = int(confidence_match.group(1))
        
        # Extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=RISK:|$)', response, re.S)
        if reasoning_match:
            parsed['reasoning'] = reasoning_match.group(1).strip()[:300]
        
        # Extract risk
        risk_match = re.search(r'RISK:\s*(LOW|MEDIUM|HIGH)', response, re.I)
        if risk_match:
            parsed['risk'] = risk_match.group(1).upper()
        
        # Extract timeframe
        timeframe_match = re.search(r'TIMEFRAME:\s*(HOURS|DAYS|WEEK)', response, re.I)
        if timeframe_match:
            parsed['timeframe'] = timeframe_match.group(1).upper()
        
        return parsed
    
    def combine_analyses(self, technical_score: float, sentiment_score: float, 
                        llm_analysis: Optional[Dict]) -> Dict[str, Any]:
        """
        Combine multiple analysis methods
        - Technical indicators (proven, quantitative)
        - Sentiment analysis (market psychology)
        - LLM reasoning (qualitative, adaptive)
        """
        
        # Start with technical + sentiment
        base_score = (technical_score + sentiment_score) / 2
        base_confidence = abs(base_score)
        
        if not llm_analysis or not llm_analysis.get('llm_available'):
            return {
                'final_score': base_score,
                'confidence': base_confidence,
                'method': 'technical_sentiment',
                'direction': 'LONG' if base_score > 0.2 else ('SHORT' if base_score < -0.2 else 'NEUTRAL')
            }
        
        # LLM available - use it to enhance decision
        llm_direction = llm_analysis['direction']
        llm_confidence = llm_analysis['confidence'] / 100.0
        
        # Convert LLM direction to score
        llm_score = 0
        if llm_direction == 'LONG':
            llm_score = llm_confidence
        elif llm_direction == 'SHORT':
            llm_score = -llm_confidence
        
        # Weighted combination (60% quantitative, 40% LLM reasoning)
        # This balances proven indicators with adaptive AI reasoning
        final_score = 0.6 * base_score + 0.4 * llm_score
        
        # Confidence boost if all agree
        agreement_boost = 1.0
        if (base_score > 0.2 and llm_score > 0.2) or (base_score < -0.2 and llm_score < -0.2):
            agreement_boost = 1.3  # 30% boost when all methods agree
        
        final_confidence = min((base_confidence * 0.6 + llm_confidence * 0.4) * agreement_boost, 1.0)
        
        return {
            'final_score': final_score,
            'confidence': final_confidence,
            'method': 'combined',
            'direction': 'LONG' if final_score > 0.2 else ('SHORT' if final_score < -0.2 else 'NEUTRAL'),
            'technical_score': technical_score,
            'sentiment_score': sentiment_score,
            'llm_score': llm_score,
            'llm_reasoning': llm_analysis.get('reasoning', ''),
            'llm_risk': llm_analysis.get('risk', 'MEDIUM'),
            'llm_timeframe': llm_analysis.get('timeframe', 'HOURS'),
            'agreement_boost': agreement_boost > 1.0
        }
    
    def learn_from_trade(self, trade_result: Dict):
        """
        Adaptive learning from trade outcomes
        Similar to AI-Trader's self-optimization
        """
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': trade_result
        })
        
        # Keep last 50 trades
        if len(self.performance_history) > 50:
            self.performance_history = self.performance_history[-50:]
        
        # Analyze performance and adjust
        if len(self.performance_history) >= 10:
            self._adjust_strategy()
    
    def _adjust_strategy(self):
        """Adjust strategy based on recent performance"""
        recent_trades = self.performance_history[-20:]
        
        # Calculate win rate
        wins = sum(1 for t in recent_trades if t['result'].get('profit', 0) > 0)
        win_rate = wins / len(recent_trades)
        
        # Adjust confidence threshold
        if win_rate < 0.4:
            # Losing more - be more selective
            self.strategy_adjustments['confidence_threshold'] = min(0.5, 
                self.strategy_adjustments['confidence_threshold'] + 0.05)
        elif win_rate > 0.6:
            # Winning more - can be slightly more aggressive
            self.strategy_adjustments['confidence_threshold'] = max(0.25,
                self.strategy_adjustments['confidence_threshold'] - 0.02)
        
        # Adjust risk based on volatility of returns
        profits = [t['result'].get('profit', 0) for t in recent_trades]
        if profits:
            import statistics
            volatility = statistics.stdev(profits) if len(profits) > 1 else 0
            if volatility > 0.1:  # High volatility
                self.strategy_adjustments['risk_multiplier'] = 0.8  # Reduce risk
            else:
                self.strategy_adjustments['risk_multiplier'] = 1.0
        
        print(f"Strategy adjusted - Confidence threshold: {self.strategy_adjustments['confidence_threshold']:.2f}, Risk multiplier: {self.strategy_adjustments['risk_multiplier']:.2f}")
    
    def get_adjusted_parameters(self) -> Dict[str, float]:
        """Get current adjusted parameters for trading"""
        return self.strategy_adjustments
