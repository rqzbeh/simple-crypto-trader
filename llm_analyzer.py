"""
Crypto Market Analyzer - LLM-Powered Analysis Layer
Inspired by AI-Trader's agent-based approach with our proven technical indicators
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import ADAPTIVE_LIMITS

class CryptoMarketAnalyzer:
    """
    Advanced market analyzer that combines:
    1. Proven technical indicators (our approach)
    2. LLM reasoning (AI-Trader approach)
    3. Adaptive learning from past trades
    """
    
    LEARNING_DATA_FILE = 'learning_state.json'
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.performance_history = []
        self.indicator_performance = {}  # Track each indicator's accuracy
        self.precision_metrics = {
            'direction_accuracy': [],
            'tp_precision': [],
            'entry_timing': [],
            'avg_tp_overshoot': 0.0,  # How much TP is typically too far
            'avg_price_movement': 0.0,  # Actual average price movement
            # Track failure reasons
            'entry_not_reached_count': 0,  # How often entry price isn't reached
            'sl_hit_early_count': 0,  # How often SL hit before TP could be reached
            'tp_too_far_count': 0,  # How often direction correct but TP not reached
            'wrong_direction_count': 0,  # How often direction prediction was wrong
            'total_trades': 0,
            # Candlestick-specific metrics
            'candlestick_accuracy': [],  # Track candlestick pattern accuracy
            'pattern_success_rate': {},  # Track success rate per pattern type
            # Streak tracking for momentum
            'current_win_streak': 0,
            'current_loss_streak': 0,
            'max_win_streak': 0,
            'max_loss_streak': 0,
        }
        self.strategy_adjustments = {
            'indicator_weights': {},
            'risk_multiplier': 1.0,
            'confidence_threshold': 0.3,
            'tp_adjustment_factor': 1.0,  # Adjust TP based on historical precision
            'entry_adjustment_factor': 1.0,  # Adjust entry proximity
            'sl_adjustment_factor': 1.0,  # Adjust SL width
            # Dynamic news/sentiment parameters (adaptive)
            # Initialize with midpoints of adaptive bounds
            'expected_return_per_sentiment': sum(ADAPTIVE_LIMITS['expected_return_per_sentiment'])/2,
            'news_impact_multiplier': sum(ADAPTIVE_LIMITS['news_impact_multiplier'])/2,
            'max_news_bonus': sum(ADAPTIVE_LIMITS['max_news_bonus'])/2,
            # Dynamic leverage & daily risk limits (adaptive)
            'dynamic_max_leverage': ADAPTIVE_LIMITS['dynamic_max_leverage'][1],
            'daily_risk_limit': sum(ADAPTIVE_LIMITS['daily_risk_limit'])/2,
            # Candlestick-specific adjustments for 2h trading
            'candlestick_confidence_boost': 1.0,  # Boost confidence based on pattern reliability
            'pattern_tp_multiplier': 1.0,  # Adjust TP specifically for candlestick patterns
            'pattern_sl_multiplier': 1.0,  # Adjust SL specifically for candlestick patterns
        }
        self.last_optimization = datetime.now()
        self.optimization_interval = 20  # Optimize every 20 trades
        
        # Load previous learning state if exists
        self._load_learning_state()
    
    def _load_learning_state(self):
        """Load learning state from file to persist across script runs"""
        try:
            if os.path.exists(self.LEARNING_DATA_FILE):
                with open(self.LEARNING_DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                # Restore learning data
                self.performance_history = data.get('performance_history', [])
                self.indicator_performance = data.get('indicator_performance', {})
                
                # Load precision metrics with backward compatibility
                loaded_metrics = data.get('precision_metrics', {})
                for key in self.precision_metrics:
                    if key in loaded_metrics:
                        self.precision_metrics[key] = loaded_metrics[key]
                
                # Load strategy adjustments with backward compatibility
                loaded_adjustments = data.get('strategy_adjustments', {})
                for key in self.strategy_adjustments:
                    if key in loaded_adjustments:
                        self.strategy_adjustments[key] = loaded_adjustments[key]
                
                # Parse last_optimization datetime
                last_opt = data.get('last_optimization')
                if last_opt:
                    self.last_optimization = datetime.fromisoformat(last_opt)
                
                print(f"📚 Loaded learning state: {len(self.performance_history)} trades, "
                      f"{self.precision_metrics['total_trades']} total verified")
        except Exception as e:
            print(f"⚠️  Could not load learning state: {e}")
    
    def _save_learning_state(self):
        """Save learning state to file to persist across script runs"""
        try:
            data = {
                'performance_history': self.performance_history,
                'indicator_performance': self.indicator_performance,
                'precision_metrics': self.precision_metrics,
                'strategy_adjustments': self.strategy_adjustments,
                'last_optimization': self.last_optimization.isoformat(),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.LEARNING_DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save learning state: {e}")
    
    def analyze_with_llm(self, symbol: str, market_data: Dict, sentiment_data: Dict, 
                        news_articles: List[Dict]) -> Dict[str, Any]:
        """
        Use LLM to analyze market data and make trading decision
        Similar to AI-Trader's agent-based reasoning
        """
        if not self.llm_client:
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

CANDLESTICK PATTERN ANALYSIS:
Signal: {', '.join(strong_signals) if strong_signals else 'None'}
Patterns Detected: {indicators.get('candlestick', {}).get('patterns', [])}
Confidence: {indicators.get('candlestick', {}).get('confidence', 0)*100:.1f}%
Description: {indicators.get('candlestick', {}).get('description', 'No significant patterns')}

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
            # Use multi-provider LLM - automatically handles failover
            response = self.llm_client.chat(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=500,  # Use max_tokens instead of num_predict
                timeout=15  # Longer timeout for Cloudflare 70B model
            )
            
            # Parse LLM response
            analysis = self._parse_llm_response(response)
            analysis['raw_response'] = response
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
        NOW ENHANCED TO TRACK:
        - Entry not reached (entry price too far)
        - SL hit early (SL too tight)
        - TP too far (direction correct but target unreachable)
        - Wrong direction (prediction error)
        """
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': trade_result
        })
        
        # Track total trades
        self.precision_metrics['total_trades'] += 1
        
        # NEW: Track failure reasons to learn different adjustment strategies
        failure_reason = trade_result.get('failure_reason')
        entry_reached = trade_result.get('entry_reached', True)
        
        if not entry_reached:
            # Entry price was never reached
            self.precision_metrics['entry_not_reached_count'] += 1
        elif failure_reason == 'sl_hit':
            # Stop loss hit before trend could work
            self.precision_metrics['sl_hit_early_count'] += 1
        elif failure_reason == 'tp_not_reached':
            # Direction correct but TP too far
            self.precision_metrics['tp_too_far_count'] += 1
        elif failure_reason == 'wrong_direction':
            # Direction prediction was wrong
            self.precision_metrics['wrong_direction_count'] += 1
        
        # Track precision metrics (separate direction from TP precision)
        if 'profit' in trade_result:
            profit = trade_result['profit']
            direction = trade_result.get('direction', 'LONG')
            
            # Track direction accuracy (only if entry was reached)
            if entry_reached:
                direction_correct = profit > 0
                self.precision_metrics['direction_accuracy'].append(1 if direction_correct else 0)
            
            # Track TP precision: did we reach TP or fall short?
            # Use max_favorable_move to see how close we got
            if entry_reached and 'tp_distance' in trade_result:
                tp_distance = abs(trade_result['tp_distance'])  # How far TP was set
                
                # Use max favorable move if available, otherwise actual movement
                if 'max_favorable_move' in trade_result:
                    best_movement = abs(trade_result['max_favorable_move'])
                else:
                    best_movement = abs(trade_result.get('actual_movement', 0))
                
                # Calculate TP precision (1.0 = perfect, <1.0 = TP too far, >1.0 = TP too conservative)
                if tp_distance > 0:
                    tp_precision = best_movement / tp_distance
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
                    self.precision_metrics['avg_price_movement'] = best_movement
                else:
                    self.precision_metrics['avg_price_movement'] = (
                        0.8 * self.precision_metrics['avg_price_movement'] + 0.2 * best_movement
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
        
        # Adaptive dynamic parameter tuning
        self._adjust_dynamic_parameters()

        # Save learning state after each trade (persists across script runs)
        self._save_learning_state()
    
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
        
        # Update streaks
        if profits and profits[-1] > 0:
            self.precision_metrics['current_win_streak'] += 1
            self.precision_metrics['current_loss_streak'] = 0
            self.precision_metrics['max_win_streak'] = max(
                self.precision_metrics['max_win_streak'],
                self.precision_metrics['current_win_streak']
            )
        elif profits and profits[-1] < 0:
            self.precision_metrics['current_loss_streak'] += 1
            self.precision_metrics['current_win_streak'] = 0
            self.precision_metrics['max_loss_streak'] = max(
                self.precision_metrics['max_loss_streak'],
                self.precision_metrics['current_loss_streak']
            )
        
        # More aggressive threshold adjustment on loss streaks
        loss_streak = self.precision_metrics['current_loss_streak']
        if loss_streak >= 3:
            # On bad streak - be VERY selective
            self.strategy_adjustments['confidence_threshold'] = min(0.65,
                self.strategy_adjustments['confidence_threshold'] + 0.10)
        elif win_rate < 0.35:
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
        
        # NEW: Adjust entry based on entry_not_reached failures
        total = self.precision_metrics['total_trades']
        if total >= 10:
            entry_fail_rate = self.precision_metrics['entry_not_reached_count'] / total
            
            if entry_fail_rate > 0.3:
                # Too many trades not opening - entry prices too far
                # Gradual adjustment: reduce by 10% each time (not fixed to 0.5x)
                current = self.strategy_adjustments['entry_adjustment_factor']
                self.strategy_adjustments['entry_adjustment_factor'] = max(0.7, current - 0.1)
                entry_reason = f"Entry too far ({entry_fail_rate*100:.0f}%), reducing gradually"
            elif entry_fail_rate > 0.15:
                # Moderate failures - small adjustment
                current = self.strategy_adjustments['entry_adjustment_factor']
                self.strategy_adjustments['entry_adjustment_factor'] = max(0.85, current - 0.05)
                entry_reason = f"Entry slightly far ({entry_fail_rate*100:.0f}%), minor adjustment"
            elif entry_fail_rate <= 0.05:
                # Excellent rate - DON'T CHANGE IT! It's working well
                # Only slowly recover toward 1.0 if we had reduced it before
                current = self.strategy_adjustments['entry_adjustment_factor']
                if current < 1.0:
                    # Gradually return to baseline (1.0) if we're below it
                    self.strategy_adjustments['entry_adjustment_factor'] = min(1.0, current + 0.02)
                    entry_reason = f"Entry working well ({entry_fail_rate*100:.0f}%), slowly returning to baseline"
                else:
                    # Already at baseline (1.0), don't touch it!
                    entry_reason = f"Entry excellent ({entry_fail_rate*100:.0f}%), maintaining"
            else:
                entry_reason = f"Entry timing acceptable ({entry_fail_rate*100:.0f}%)"
        else:
            entry_reason = "Insufficient data"
        
        # NEW: Adjust SL based on sl_hit_early failures
        if total >= 10:
            sl_early_rate = self.precision_metrics['sl_hit_early_count'] / total
            
            if sl_early_rate > 0.3:
                # Too many SL hits - stops too tight
                # Gradual widening: add 10% each time
                current = self.strategy_adjustments['sl_adjustment_factor']
                self.strategy_adjustments['sl_adjustment_factor'] = min(1.5, current + 0.1)
                sl_reason = f"SL hit often ({sl_early_rate*100:.0f}%), widening gradually"
            elif sl_early_rate > 0.15:
                # Moderate SL hits - small adjustment
                current = self.strategy_adjustments['sl_adjustment_factor']
                self.strategy_adjustments['sl_adjustment_factor'] = min(1.3, current + 0.05)
                sl_reason = f"SL hit moderately ({sl_early_rate*100:.0f}%), minor widening"
            elif sl_early_rate < 0.08 and direction_accuracy > 0.65:
                # Very few SL hits AND good direction - can CAUTIOUSLY tighten
                # But only if we widened stops before (returning to baseline)
                current = self.strategy_adjustments['sl_adjustment_factor']
                if current > 1.0:
                    # Gradually return to baseline if we had widened before
                    self.strategy_adjustments['sl_adjustment_factor'] = max(1.0, current - 0.03)
                    sl_reason = f"SL working well ({sl_early_rate*100:.0f}%), slowly returning to baseline"
                else:
                    # Already at or below baseline - don't tighten further!
                    sl_reason = f"SL excellent ({sl_early_rate*100:.0f}%), maintaining"
            else:
                sl_reason = "SL width acceptable"
        else:
            sl_reason = "Insufficient data"
        
        print(f"\n📊 Strategy Auto-Adjusted:")
        print(f"   Win Rate: {win_rate*100:.1f}% | Avg Profit: {avg_profit*100:.2f}%")
        print(f"   Direction Accuracy: {direction_accuracy*100:.1f}%")
        if self.precision_metrics['tp_precision']:
            print(f"   TP Precision: {avg_tp_precision*100:.1f}% ({tp_reason})")
            print(f"   Avg Price Movement: {self.precision_metrics['avg_price_movement']*100:.2f}%")
        print(f"   Confidence Threshold: {self.strategy_adjustments['confidence_threshold']:.2f}")
        print(f"   Risk Multiplier: {self.strategy_adjustments['risk_multiplier']:.2f}")
        print(f"   TP Adjustment: {self.strategy_adjustments['tp_adjustment_factor']:.2f}x")
        if total >= 10:
            print(f"   Entry Adjustment: {self.strategy_adjustments['entry_adjustment_factor']:.2f}x ({entry_reason})")
            print(f"   SL Adjustment: {self.strategy_adjustments['sl_adjustment_factor']:.2f}x ({sl_reason})")
            print(f"   Failure Breakdown:")
            print(f"     • Entry not reached: {entry_fail_rate*100:.1f}%")
            print(f"     • SL hit early: {sl_early_rate*100:.1f}%")
            tp_fail_rate = self.precision_metrics['tp_too_far_count'] / total
            wrong_dir_rate = self.precision_metrics['wrong_direction_count'] / total
            print(f"     • TP too far: {tp_fail_rate*100:.1f}%")
            print(f"     • Wrong direction: {wrong_dir_rate*100:.1f}%")
        print()
    
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
            'precision_metrics': precision_summary,
            # Dynamic adaptive parameters exposure
            'expected_return_per_sentiment': self.strategy_adjustments.get('expected_return_per_sentiment'),
            'news_impact_multiplier': self.strategy_adjustments.get('news_impact_multiplier'),
            'max_news_bonus': self.strategy_adjustments.get('max_news_bonus'),
            'dynamic_max_leverage': self.strategy_adjustments.get('dynamic_max_leverage'),
            'daily_risk_limit': self.strategy_adjustments.get('daily_risk_limit'),
        }

    def _adjust_dynamic_parameters(self):
        """Adaptive tuning of news impact, expected return, leverage and risk limits.
        Adjustments based on failure pattern ratios and win rate.
        Safe bounds enforced to prevent runaway changes.
        """
        # Anomaly / warm-up guard: require minimum sample size before adapting
        total_trades_global = len(self.performance_history)
        if total_trades_global < 15:
            return  # Not enough data yet for meaningful adaptation

        total = max(1, self.precision_metrics['total_trades'])
        enr = self.precision_metrics['entry_not_reached_count'] / total
        slh = self.precision_metrics['sl_hit_early_count'] / total
        tpf = self.precision_metrics['tp_too_far_count'] / total
        wdg = self.precision_metrics['wrong_direction_count'] / total

        # Recent performance slice
        win_rate = 0.0
        if self.performance_history:
            recent = self.performance_history[-40:]
            wins = sum(1 for t in recent if t['result'].get('profit', 0) > 0)
            win_rate = wins / len(recent) if recent else 0

        avg_profit = 0.0
        if self.performance_history:
            profits = [t['result'].get('profit', 0) for t in self.performance_history[-40:]]
            avg_profit = sum(profits) / len(profits) if profits else 0.0

        erps = self.strategy_adjustments['expected_return_per_sentiment']
        nim = self.strategy_adjustments['news_impact_multiplier']
        mnb = self.strategy_adjustments['max_news_bonus']
        lev_cap = self.strategy_adjustments['dynamic_max_leverage']
        risk_lim = self.strategy_adjustments['daily_risk_limit']
        sl_adj = self.strategy_adjustments['sl_adjustment_factor']
        tp_adj = self.strategy_adjustments['tp_adjustment_factor']

        # Entry failures -> reduce expected return slightly (closer targets)
        if enr > 0.15:
            erps *= 0.97
        elif enr < 0.05 and win_rate > 0.55:
            erps = min(erps * 1.02, 0.08)

        # TP too far -> reduce expected return & max bonus
        if tpf > 0.12:
            erps *= 0.95
            mnb *= 0.93
            tp_adj = max(0.8, tp_adj * 0.95)
        elif tpf < 0.05 and win_rate > 0.55:
            mnb = min(mnb * 1.05, 0.10)
            tp_adj = min(tp_adj * 1.03, 1.3)

        # SL early hits -> widen stops (increase sl_adj) & reduce leverage cap
        if slh > 0.12:
            sl_adj = min(sl_adj * 1.05, 1.4)
            lev_cap = max(4, lev_cap - 1)
        elif slh < 0.05 and win_rate > 0.6:
            sl_adj = max(0.9, sl_adj * 0.97)

        # Wrong direction -> raise confidence threshold & reduce leverage
        if wdg > 0.2:
            self.strategy_adjustments['confidence_threshold'] = min(0.6, self.strategy_adjustments['confidence_threshold'] + 0.05)
            lev_cap = max(3, lev_cap - 2)
        elif wdg < 0.08 and win_rate > 0.55:
            self.strategy_adjustments['confidence_threshold'] = max(0.25, self.strategy_adjustments['confidence_threshold'] - 0.02)

        # Sustained losses tighten daily risk limit; good performance allows mild expansion
        if win_rate < 0.35 and total >= 25:
            risk_lim = max(0.03, risk_lim * 0.95)
        elif win_rate > 0.55 and avg_profit > 0.01:
            risk_lim = min(0.07, risk_lim * 1.02)

        # Bounds
        erps = max(*ADAPTIVE_LIMITS['expected_return_per_sentiment']) if erps > ADAPTIVE_LIMITS['expected_return_per_sentiment'][1] else max(ADAPTIVE_LIMITS['expected_return_per_sentiment'][0], erps)
        nim = max(*ADAPTIVE_LIMITS['news_impact_multiplier']) if nim > ADAPTIVE_LIMITS['news_impact_multiplier'][1] else max(ADAPTIVE_LIMITS['news_impact_multiplier'][0], nim)
        mnb = max(*ADAPTIVE_LIMITS['max_news_bonus']) if mnb > ADAPTIVE_LIMITS['max_news_bonus'][1] else max(ADAPTIVE_LIMITS['max_news_bonus'][0], mnb)
        lev_cap = max(ADAPTIVE_LIMITS['dynamic_max_leverage'][0], min(lev_cap, ADAPTIVE_LIMITS['dynamic_max_leverage'][1]))
        sl_adj = max(ADAPTIVE_LIMITS['sl_adjustment_factor'][0], min(sl_adj, ADAPTIVE_LIMITS['sl_adjustment_factor'][1]))
        tp_adj = max(ADAPTIVE_LIMITS['tp_adjustment_factor'][0], min(tp_adj, ADAPTIVE_LIMITS['tp_adjustment_factor'][1]))
        risk_lim = max(ADAPTIVE_LIMITS['daily_risk_limit'][0], min(risk_lim, ADAPTIVE_LIMITS['daily_risk_limit'][1]))

        # Persist (capture old/new for logging before assignment)
        old_values = {
            'expected_return_per_sentiment': self.strategy_adjustments['expected_return_per_sentiment'],
            'news_impact_multiplier': self.strategy_adjustments['news_impact_multiplier'],
            'max_news_bonus': self.strategy_adjustments['max_news_bonus'],
            'dynamic_max_leverage': self.strategy_adjustments['dynamic_max_leverage'],
            'daily_risk_limit': self.strategy_adjustments['daily_risk_limit'],
            'sl_adjustment_factor': self.strategy_adjustments['sl_adjustment_factor'],
            'tp_adjustment_factor': self.strategy_adjustments['tp_adjustment_factor']
        }
        self.strategy_adjustments['expected_return_per_sentiment'] = round(erps, 5)
        self.strategy_adjustments['news_impact_multiplier'] = round(nim, 5)
        self.strategy_adjustments['max_news_bonus'] = round(mnb, 5)
        self.strategy_adjustments['dynamic_max_leverage'] = lev_cap
        self.strategy_adjustments['daily_risk_limit'] = round(risk_lim, 5)
        self.strategy_adjustments['sl_adjustment_factor'] = round(sl_adj, 5)
        self.strategy_adjustments['tp_adjustment_factor'] = round(tp_adj, 5)

        # Logging adaptive changes (only if any value changed)
        new_values = {
            'expected_return_per_sentiment': self.strategy_adjustments['expected_return_per_sentiment'],
            'news_impact_multiplier': self.strategy_adjustments['news_impact_multiplier'],
            'max_news_bonus': self.strategy_adjustments['max_news_bonus'],
            'dynamic_max_leverage': self.strategy_adjustments['dynamic_max_leverage'],
            'daily_risk_limit': self.strategy_adjustments['daily_risk_limit'],
            'sl_adjustment_factor': self.strategy_adjustments['sl_adjustment_factor'],
            'tp_adjustment_factor': self.strategy_adjustments['tp_adjustment_factor']
        }
        if old_values != new_values:
            try:
                os.makedirs('logs', exist_ok=True)
                # Rotate if file exceeds ~1MB
                log_path = 'logs/adaptive_changes.jsonl'
                if os.path.exists(log_path) and os.path.getsize(log_path) > 1_000_000:
                    import time as _t
                    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    rotated = f'logs/adaptive_changes_{ts}.jsonl'
                    try:
                        os.replace(log_path, rotated)
                    except Exception:
                        pass
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat()+ 'Z',
                    'metrics': {
                        'enr': round(enr, 4),
                        'slh': round(slh, 4),
                        'tpf': round(tpf, 4),
                        'wdg': round(wdg, 4),
                        'win_rate': round(win_rate, 4),
                        'avg_profit': round(avg_profit, 5)
                    },
                    'old': old_values,
                    'new': new_values
                }
                with open('logs/adaptive_changes.jsonl', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass

