"""
Ensemble Signal Generator - Combines multiple analysis methods for better accuracy
Uses voting system and confidence weighting
"""

from typing import Dict, List, Tuple
import statistics

class EnsembleSignalGenerator:
    """
    Ensemble learning for crypto signals
    Combines:
    1. AI sentiment analysis
    2. Technical indicators
    3. Candlestick patterns
    4. Historical performance patterns
    """
    
    def __init__(self, market_analyzer=None):
        self.market_analyzer = market_analyzer
        self.min_agreement = 0.6  # 60% of methods must agree
    
    def generate_ensemble_signal(self, 
                                 sentiment_score: float,
                                 technical_score: float,
                                 market_data: Dict,
                                 symbol: str) -> Tuple[str, float, Dict]:
        """
        Generate signal using ensemble voting
        Returns: (direction, confidence, analysis_breakdown)
        """
        
        votes = []
        confidences = []
        reasons = []
        
        # Vote 1: AI Sentiment (highest weight = 40%)
        if sentiment_score > 0.3:
            votes.append('LONG')
            confidences.append(abs(sentiment_score) * 0.4)
            reasons.append(f"AI Sentiment: {sentiment_score:+.2f} (Bullish)")
        elif sentiment_score < -0.3:
            votes.append('SHORT')
            confidences.append(abs(sentiment_score) * 0.4)
            reasons.append(f"AI Sentiment: {sentiment_score:+.2f} (Bearish)")
        else:
            votes.append('NEUTRAL')
            confidences.append(0.1)
            reasons.append(f"AI Sentiment: {sentiment_score:+.2f} (Neutral)")
        
        # Vote 2: Technical Indicators (weight = 30%)
        if technical_score > 0.4:
            votes.append('LONG')
            confidences.append(abs(technical_score) * 0.3)
            reasons.append(f"Technicals: {technical_score:+.2f} (Bullish)")
        elif technical_score < -0.4:
            votes.append('SHORT')
            confidences.append(abs(technical_score) * 0.3)
            reasons.append(f"Technicals: {technical_score:+.2f} (Bearish)")
        else:
            votes.append('NEUTRAL')
            confidences.append(0.05)
            reasons.append(f"Technicals: {technical_score:+.2f} (Neutral)")
        
        # Vote 3: Candlestick Patterns (weight = 20%)
        candlestick_data = market_data.get('indicators', {}).get('candlestick', {})
        candlestick_signal = candlestick_data.get('signal', 0)
        candlestick_conf = candlestick_data.get('confidence', 0)
        
        if candlestick_signal > 0 and candlestick_conf > 0.5:
            votes.append('LONG')
            confidences.append(candlestick_conf * 0.2)
            reasons.append(f"Candlestick: Bullish pattern ({candlestick_conf*100:.0f}%)")
        elif candlestick_signal < 0 and candlestick_conf > 0.5:
            votes.append('SHORT')
            confidences.append(candlestick_conf * 0.2)
            reasons.append(f"Candlestick: Bearish pattern ({candlestick_conf*100:.0f}%)")
        else:
            votes.append('NEUTRAL')
            confidences.append(0.05)
            reasons.append("Candlestick: No clear pattern")
        
        # Vote 4: Volatility Check (weight = 10%)
        volatility = market_data.get('volatility', 0)
        if volatility > 0.8:  # High volatility = risky
            confidences[-1] *= 0.7  # Reduce last confidence
            reasons.append(f"⚠️ High Volatility: {volatility*100:.1f}% (reduced confidence)")
        elif volatility < 0.3:  # Low volatility = safer
            confidences[-1] *= 1.1  # Slight boost
            reasons.append(f"✅ Low Volatility: {volatility*100:.1f}% (safer)")
        
        # Tally votes
        long_votes = votes.count('LONG')
        short_votes = votes.count('SHORT')
        neutral_votes = votes.count('NEUTRAL')
        total_votes = len(votes)
        
        # Determine consensus
        if long_votes >= total_votes * self.min_agreement:
            direction = 'LONG'
            base_confidence = long_votes / total_votes
        elif short_votes >= total_votes * self.min_agreement:
            direction = 'SHORT'
            base_confidence = short_votes / total_votes
        else:
            direction = 'NEUTRAL'
            base_confidence = 0.3  # Low confidence for no consensus
        
        # Weight confidence by component confidences
        weighted_confidence = sum(confidences)
        
        # Apply learning adjustments if available
        if self.market_analyzer:
            adjustments = self.market_analyzer.get_adjusted_parameters()
            conf_threshold = adjustments.get('confidence_threshold', 0.3)
            
            # Check if meets minimum threshold
            if weighted_confidence < conf_threshold:
                direction = 'NEUTRAL'
                reasons.append(f"❌ Below threshold: {weighted_confidence:.2f} < {conf_threshold:.2f}")
        
        # Cap confidence at 0.95
        final_confidence = min(weighted_confidence, 0.95)
        
        analysis_breakdown = {
            'votes': {
                'LONG': long_votes,
                'SHORT': short_votes,
                'NEUTRAL': neutral_votes
            },
            'vote_percentage': {
                'LONG': long_votes / total_votes,
                'SHORT': short_votes / total_votes,
                'NEUTRAL': neutral_votes / total_votes
            },
            'reasons': reasons,
            'weighted_confidence': weighted_confidence,
            'base_confidence': base_confidence,
            'volatility': volatility
        }
        
        return direction, final_confidence, analysis_breakdown
    
    def explain_signal(self, analysis: Dict) -> str:
        """Generate human-readable explanation of signal"""
        reasons = analysis.get('reasons', [])
        votes = analysis.get('votes', {})
        
        explanation = "Ensemble Analysis:\n"
        explanation += f"  Votes: LONG={votes.get('LONG', 0)}, "
        explanation += f"SHORT={votes.get('SHORT', 0)}, "
        explanation += f"NEUTRAL={votes.get('NEUTRAL', 0)}\n"
        explanation += "\n  Breakdown:\n"
        
        for reason in reasons:
            explanation += f"    • {reason}\n"
        
        return explanation
