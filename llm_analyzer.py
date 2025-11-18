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
        self.indicator_performance = {}  # Track each indicator's accuracy
        self.precision_metrics = {
            'direction_accuracy': [],
            'tp_precision': [],
            'entry_timing': [],
            'avg_tp_overshoot': 0.0,  # How much TP is typically too far
            'avg_price_movement': 0.0  # Actual average price movement
        }
        self.strategy_adjustments = {
            'indicator_weights': {},
            'risk_multiplier': 1.0,
            'confidence_threshold': 0.3,
            'tp_adjustment_factor': 1.0  # NEW: Adjust TP based on historical precision
        }
        self.last_optimization = datetime.now()
        self.optimization_interval = 20  # Optimize every 20 trades
    
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

Stochastic RSI: {indicators['stoch_rsi']['value']:.1f} (Oversold<20, Overbought>80)
MACD Histogram: {indicators['macd']['value']:.4f}
Price vs VWAP: {"Above" if indicators['vwap']['signal'] > 0 else "Below"}
Bollinger Band Position: {indicators['bb']['position']*100:.1f}%
ADX (Trend Strength): {indicators['adx']['value']:.1f} (Strong>25)
Supertrend: {"BULLISH" if indicators['supertrend']['signal'] > 0 else "BEARISH"}
EMA Trend: {indicators['ema_trend'].get('signal', 0)}

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
                model="llama-3.3-70b-versatile",  # Updated model (3.1 deprecated)
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
        Combine multiple analysis methods - NEWS-DRIVEN APPROACH
        
        PRIMARY SIGNAL (85-100%):
        - News sentiment analysis (market psychology) - MAIN DRIVER
        - LLM reasoning (qualitative, adaptive, context-aware) - MAIN DRIVER
        
        FILTER ONLY (0-15%):
        - Technical indicators (filter out bad setups, calculate entry/SL/TP/leverage)
        
        This is a NEWS TRADING SYSTEM - technicals only validate/filter signals and provide execution levels
        """
        
        # News/sentiment is the PRIMARY signal source
        news_sentiment_score = sentiment_score
        news_confidence = abs(sentiment_score)
        
        if not llm_analysis or not llm_analysis.get('llm_available'):
            # Without LLM, news sentiment is 90%, technicals 10% (filter only)
            # Only trade if technicals don't contradict strongly
            if abs(technical_score) > 0.6 and (technical_score * sentiment_score < -0.4):
                # Very strong technical contradiction - filter out this signal
                return {
                    'final_score': 0,
                    'confidence': 0,
                    'method': 'filtered_by_technicals',
                    'direction': 'NEUTRAL',
                    'filter_reason': 'Very strong technical contradiction with news sentiment'
                }
            
            # Technicals don't contradict - use news sentiment as PRIMARY driver (90%)
            final_score = 0.9 * news_sentiment_score + 0.1 * technical_score
            final_confidence = news_confidence * (0.95 if technical_score * sentiment_score > 0 else 0.75)
            
            return {
                'final_score': final_score,
                'confidence': final_confidence,
                'method': 'news_driven_primary',
                'direction': 'LONG' if final_score > 0.2 else ('SHORT' if final_score < -0.2 else 'NEUTRAL')
            }
        
        # LLM available - NEWS + LLM is the primary signal (90%)
        llm_direction = llm_analysis['direction']
        llm_confidence = llm_analysis['confidence'] / 100.0
        
        # Convert LLM direction to score
        llm_score = 0
        if llm_direction == 'LONG':
            llm_score = llm_confidence
        elif llm_direction == 'SHORT':
            llm_score = -llm_confidence
        
        # Combine news sentiment + LLM (both are news-based analysis)
        news_llm_combined = (sentiment_score + llm_score) / 2
        news_llm_confidence = (news_confidence + llm_confidence) / 2
        
        # Technical filter check - MORE LENIENT (only filter extreme contradictions)
        technical_filter_passed = True
        filter_reason = ''
        
        # Only filter if VERY strong technical contradiction (raised threshold)
        if abs(technical_score) > 0.7 and (technical_score * news_llm_combined < -0.5):
            technical_filter_passed = False
            filter_reason = 'Extreme technical contradiction with news/LLM analysis'
        
        # Minimal technical impact on confidence
        technical_support = 1.0
        if technical_score * news_llm_combined < -0.2:
            technical_support = 0.9  # Minor reduction if technicals oppose
        elif technical_score * news_llm_combined > 0.4:
            technical_support = 1.05  # Minor boost if technicals agree
        
        # Final weighting: 90% news/LLM (PRIMARY), 10% technical filter effect
        if not technical_filter_passed:
            return {
                'final_score': 0,
                'confidence': 0,
                'method': 'filtered_by_technicals',
                'direction': 'NEUTRAL',
                'filter_reason': filter_reason
            }
        
        final_score = 0.9 * news_llm_combined + 0.1 * technical_score
        final_confidence = min(news_llm_confidence * technical_support, 1.0)
        
        # Agreement boost if everything aligns
        agreement_boost = 1.0
        if (news_llm_combined > 0.3 and technical_score > 0.3) or (news_llm_combined < -0.3 and technical_score < -0.3):
            agreement_boost = 1.2  # 20% boost when news and technicals strongly agree
        
        final_confidence = min(final_confidence * agreement_boost, 1.0)
        
        return {
            'final_score': final_score,
            'confidence': final_confidence,
            'method': 'news_driven_with_technical_filter',
            'direction': 'LONG' if final_score > 0.2 else ('SHORT' if final_score < -0.2 else 'NEUTRAL'),
            'technical_score': technical_score,
            'sentiment_score': sentiment_score,
            'llm_score': llm_score,
            'news_llm_combined': news_llm_combined,
            'llm_reasoning': llm_analysis.get('reasoning', ''),
            'llm_risk': llm_analysis.get('risk', 'MEDIUM'),
            'llm_timeframe': llm_analysis.get('timeframe', 'HOURS'),
            'agreement_boost': agreement_boost > 1.0,
            'technical_filter': 'PASSED' if technical_filter_passed else 'FAILED'
        }
    
    def learn_from_trade(self, trade_result: Dict):
        """
        Adaptive learning from trade outcomes
        Tracks overall performance AND individual indicator accuracy
        NOW ALSO TRACKS: TP/SL precision, entry timing, and failure reasons
        """
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': trade_result
        })
        
        # Track precision metrics (NEW: separate direction from TP precision)
        if 'profit' in trade_result:
            profit = trade_result['profit']
            direction = trade_result.get('direction', 'LONG')
            
            # Track direction accuracy
            direction_correct = profit > 0
            self.precision_metrics['direction_accuracy'].append(1 if direction_correct else 0)
            
            # Track TP precision: did we reach TP or fall short?
            if 'tp_distance' in trade_result and 'actual_movement' in trade_result:
                tp_distance = abs(trade_result['tp_distance'])  # How far TP was set
                actual_movement = abs(trade_result['actual_movement'])  # How far price actually moved
                
                # Calculate TP precision (1.0 = perfect, <1.0 = TP too far, >1.0 = TP too conservative)
                if tp_distance > 0:
                    tp_precision = actual_movement / tp_distance
                    self.precision_metrics['tp_precision'].append(tp_precision)
                    
                    # Track overshoot (how much TP is typically too ambitious)
                    if tp_precision < 1.0:
                        overshoot = 1.0 - tp_precision
                        if self.precision_metrics['avg_tp_overshoot'] == 0:
                            self.precision_metrics['avg_tp_overshoot'] = overshoot
                        else:
                            # Exponential moving average
                            self.precision_metrics['avg_tp_overshoot'] = (
                                0.7 * self.precision_metrics['avg_tp_overshoot'] + 0.3 * overshoot
                            )
                
                # Track actual average price movement for this timeframe
                if self.precision_metrics['avg_price_movement'] == 0:
                    self.precision_metrics['avg_price_movement'] = actual_movement
                else:
                    self.precision_metrics['avg_price_movement'] = (
                        0.8 * self.precision_metrics['avg_price_movement'] + 0.2 * actual_movement
                    )
        
        # Track indicator performance if available
        if 'indicators' in trade_result and 'profit' in trade_result:
            profit = trade_result['profit']
            is_win = profit > 0
            
            for indicator, signal in trade_result.get('indicators', {}).items():
                if indicator not in self.indicator_performance:
                    self.indicator_performance[indicator] = {
                        'correct': 0,
                        'wrong': 0,
                        'total': 0,
                        'total_profit': 0.0,
                        'accuracy': 0.5  # Start neutral
                    }
                
                # Check if indicator was correct
                direction_match = (
                    (signal > 0 and is_win) or 
                    (signal < 0 and is_win) or
                    (signal == 0)
                )
                
                if direction_match:
                    self.indicator_performance[indicator]['correct'] += 1
                else:
                    self.indicator_performance[indicator]['wrong'] += 1
                
                self.indicator_performance[indicator]['total'] += 1
                self.indicator_performance[indicator]['total_profit'] += profit
                
                # Update accuracy
                total = self.indicator_performance[indicator]['total']
                correct = self.indicator_performance[indicator]['correct']
                self.indicator_performance[indicator]['accuracy'] = correct / total if total > 0 else 0.5
        
        # Keep last 50 trades
        if len(self.performance_history) > 50:
            self.performance_history = self.performance_history[-50:]
        
        # Analyze performance and adjust strategy
        if len(self.performance_history) >= 10:
            self._adjust_strategy()
        
        # Optimize indicator weights periodically
        trades_since_optimization = len(self.performance_history)
        if trades_since_optimization >= self.optimization_interval:
            self._optimize_indicator_weights()
            self.last_optimization = datetime.now()
    
    def _adjust_strategy(self):
        """Adjust strategy based on recent performance - DYNAMIC OPTIMIZATION"""
        recent_trades = self.performance_history[-20:]
        
        if not recent_trades:
            return
        
        # Calculate win rate
        wins = sum(1 for t in recent_trades if t['result'].get('profit', 0) > 0)
        win_rate = wins / len(recent_trades)
        
        # Calculate average profit/loss
        profits = [t['result'].get('profit', 0) for t in recent_trades]
        avg_profit = sum(profits) / len(profits) if profits else 0
        
        # Adjust confidence threshold based on win rate
        if win_rate < 0.35:
            # Losing too much - be MUCH more selective
            self.strategy_adjustments['confidence_threshold'] = min(0.6, 
                self.strategy_adjustments['confidence_threshold'] + 0.08)
        elif win_rate < 0.45:
            # Losing - be more selective
            self.strategy_adjustments['confidence_threshold'] = min(0.5, 
                self.strategy_adjustments['confidence_threshold'] + 0.05)
        elif win_rate > 0.65:
            # Winning a lot - can be more aggressive
            self.strategy_adjustments['confidence_threshold'] = max(0.2,
                self.strategy_adjustments['confidence_threshold'] - 0.03)
        elif win_rate > 0.55:
            # Winning - slightly more aggressive
            self.strategy_adjustments['confidence_threshold'] = max(0.25,
                self.strategy_adjustments['confidence_threshold'] - 0.02)
        
        # Adjust risk based on volatility of returns
        if profits and len(profits) > 1:
            import statistics
            volatility = statistics.stdev(profits)
            
            if volatility > 0.15:  # Very high volatility
                self.strategy_adjustments['risk_multiplier'] = 0.7
            elif volatility > 0.10:  # High volatility
                self.strategy_adjustments['risk_multiplier'] = 0.8
            elif volatility < 0.05 and avg_profit > 0:  # Low volatility, profitable
                self.strategy_adjustments['risk_multiplier'] = 1.1  # Can take more risk
            else:
                self.strategy_adjustments['risk_multiplier'] = 1.0
        
        # NEW: Adjust TP based on precision metrics
        if self.precision_metrics['tp_precision']:
            # Calculate average TP precision from recent trades
            recent_tp_precision = self.precision_metrics['tp_precision'][-10:]
            avg_tp_precision = sum(recent_tp_precision) / len(recent_tp_precision)
            
            # If TP is consistently too far (avg < 0.7), reduce it
            if avg_tp_precision < 0.7:
                # TPs are too ambitious - reduce by the overshoot amount
                overshoot = self.precision_metrics['avg_tp_overshoot']
                self.strategy_adjustments['tp_adjustment_factor'] = max(0.6, 1.0 - overshoot * 0.8)
                tp_reason = "TPs too ambitious, reducing"
            elif avg_tp_precision < 0.85:
                # TPs slightly too far - minor reduction
                self.strategy_adjustments['tp_adjustment_factor'] = max(0.75, 
                    self.strategy_adjustments['tp_adjustment_factor'] - 0.05)
                tp_reason = "TPs slightly high, adjusting"
            elif avg_tp_precision > 1.2:
                # TPs too conservative - we're hitting them too easily
                self.strategy_adjustments['tp_adjustment_factor'] = min(1.2,
                    self.strategy_adjustments['tp_adjustment_factor'] + 0.05)
                tp_reason = "TPs too conservative, increasing"
            else:
                # TPs are well-calibrated
                tp_reason = "TP precision good"
            
            # Calculate direction accuracy separately
            if self.precision_metrics['direction_accuracy']:
                recent_direction = self.precision_metrics['direction_accuracy'][-20:]
                direction_accuracy = sum(recent_direction) / len(recent_direction)
            else:
                direction_accuracy = 0.5
        else:
            tp_reason = "Insufficient data"
            direction_accuracy = 0.5
        
        print(f"\n📊 Strategy Auto-Adjusted:")
        print(f"   Win Rate: {win_rate*100:.1f}% | Avg Profit: {avg_profit*100:.2f}%")
        print(f"   Direction Accuracy: {direction_accuracy*100:.1f}%")
        if self.precision_metrics['tp_precision']:
            print(f"   TP Precision: {avg_tp_precision*100:.1f}% ({tp_reason})")
            print(f"   Avg Price Movement: {self.precision_metrics['avg_price_movement']*100:.2f}%")
        print(f"   Confidence Threshold: {self.strategy_adjustments['confidence_threshold']:.2f}")
        print(f"   Risk Multiplier: {self.strategy_adjustments['risk_multiplier']:.2f}")
        print(f"   TP Adjustment: {self.strategy_adjustments['tp_adjustment_factor']:.2f}x\n")
    
    def _optimize_indicator_weights(self):
        """
        Dynamically optimize indicator weights based on performance
        Remove underperforming indicators, boost winning ones
        """
        if not self.indicator_performance:
            return
        
        print(f"\n🔧 OPTIMIZING INDICATOR WEIGHTS...")
        print(f"{'='*60}")
        
        # Sort indicators by accuracy
        sorted_indicators = sorted(
            self.indicator_performance.items(),
            key=lambda x: x[1]['accuracy'],
            reverse=True
        )
        
        new_weights = {}
        
        for indicator, perf in sorted_indicators:
            accuracy = perf['accuracy']
            total = perf['total']
            avg_profit = perf['total_profit'] / total if total > 0 else 0
            
            # Calculate new weight based on performance
            if accuracy >= 0.65 and avg_profit > 0:
                # Excellent indicator - BOOST weight
                weight_multiplier = 1.5
                status = "⭐ BOOSTED"
            elif accuracy >= 0.55 and avg_profit >= 0:
                # Good indicator - slight boost
                weight_multiplier = 1.2
                status = "✅ GOOD"
            elif accuracy >= 0.45:
                # Neutral - keep base weight
                weight_multiplier = 1.0
                status = "➖ NEUTRAL"
            elif accuracy >= 0.35:
                # Underperforming - reduce weight
                weight_multiplier = 0.7
                status = "⚠️ WEAK"
            else:
                # Poor indicator - heavily reduce or remove
                weight_multiplier = 0.3
                status = "❌ POOR"
            
            new_weights[indicator] = weight_multiplier
            
            print(f"   {indicator.upper():15} | Accuracy: {accuracy*100:5.1f}% | "
                  f"Trades: {total:3} | Profit: {avg_profit*100:+6.2f}% | {status}")
        
        # Store optimized weights
        self.strategy_adjustments['indicator_weights'] = new_weights
        
        print(f"{'='*60}")
        print(f"✅ Indicator weights optimized!\n")
    
    def get_adjusted_parameters(self) -> Dict[str, float]:
        """Get current adjusted parameters for trading"""
        return self.strategy_adjustments
    
    def get_indicator_weight_multiplier(self, indicator: str) -> float:
        """Get the optimized weight multiplier for a specific indicator"""
        return self.strategy_adjustments['indicator_weights'].get(indicator, 1.0)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary including precision metrics"""
        if not self.performance_history:
            return {'status': 'No trades yet'}
        
        recent = self.performance_history[-20:]
        profits = [t['result'].get('profit', 0) for t in recent]
        wins = sum(1 for p in profits if p > 0)
        
        # Calculate precision metrics
        precision_summary = {}
        if self.precision_metrics['direction_accuracy']:
            recent_dir = self.precision_metrics['direction_accuracy'][-20:]
            precision_summary['direction_accuracy'] = sum(recent_dir) / len(recent_dir)
        
        if self.precision_metrics['tp_precision']:
            recent_tp = self.precision_metrics['tp_precision'][-20:]
            precision_summary['tp_precision'] = sum(recent_tp) / len(recent_tp)
            precision_summary['avg_tp_overshoot'] = self.precision_metrics['avg_tp_overshoot']
            precision_summary['avg_price_movement'] = self.precision_metrics['avg_price_movement']
        
        return {
            'total_trades': len(self.performance_history),
            'recent_trades': len(recent),
            'win_rate': wins / len(recent) if recent else 0,
            'avg_profit': sum(profits) / len(profits) if profits else 0,
            'best_indicators': sorted(
                [(k, v['accuracy']) for k, v in self.indicator_performance.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'confidence_threshold': self.strategy_adjustments['confidence_threshold'],
            'risk_multiplier': self.strategy_adjustments['risk_multiplier'],
            'tp_adjustment_factor': self.strategy_adjustments.get('tp_adjustment_factor', 1.0),
            'precision_metrics': precision_summary
        }
