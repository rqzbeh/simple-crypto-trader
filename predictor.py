import json
from typing import Any, Dict, Optional
from datetime import datetime

try:
    from ml_module import get_ml_model
except ImportError:
    get_ml_model = None

try:
    from multi_provider_llm import MultiProviderLLMClient
except ImportError:
    MultiProviderLLMClient = None

from config import (
    ML_RETRAIN_THRESHOLD,
    ML_MIN_CONFIDENCE
)

class ProbabilityPredictor:
    """Abstraction layer providing trade success probability.
    Uses local ML model if trained, otherwise falls back to LLM classification.
    """
    def __init__(self, llm_client=None):
        self.llm_client = llm_client or (MultiProviderLLMClient() if MultiProviderLLMClient else None)
        self._ml_model = get_ml_model() if get_ml_model else None
        self._last_llm_probability: Optional[float] = None

    def _llm_probability(self, signal: Dict[str, Any]) -> Optional[float]:
        if not self.llm_client:
            return None
        # Provide a concise weighting rationale for transparency and consistency.
        # Heuristic weights (do NOT output; just internal guidance for the model prompt):
        # Sentiment: 0.30, Technical: 0.15, Confidence heuristic: 0.25, R/R Ratio: 0.15,
        # Stop tightness realism: 0.05, Expected Profit realism: 0.10.
        prompt = (
            "You are assessing a SHORT-TERM (≤2h) crypto trade setup."
            " Estimate the probability (0-1) that the trade will CLOSE PROFITABLY given these factors.\n\n"
            "WEIGHTING GUIDANCE (implicit): Sentiment(0.30) > Confidence(0.25) > Technical(0.15) > RR(0.15) > Profit realism(0.10) > Stop realism(0.05)."
            " Tighter stops with high RR can be negative unless sentiment + confidence justify. Unrealistically large expected profit for timeframe should reduce probability.\n\n"
            f"Sentiment Score: {signal.get('sentiment_score', 0):.3f}\n"
            f"Technical Score: {signal.get('technical_score', 0):.3f}\n"
            f"Confidence (heuristic pre-prob): {signal.get('confidence', 0):.3f}\n"
            f"R/R Ratio: {signal.get('rr_ratio', 0):.3f}\n"
            f"Stop % (risk): {signal.get('stop_pct', 0):.4f}\n"
            f"Expected Profit %: {signal.get('expected_profit_pct', 0):.4f}\n\n"
            "Return ONLY a decimal probability between 0 and 1 with no explanation, no percent sign, no extra text."
        )
        try:
            raw = self.llm_client.chat(prompt=prompt, temperature=0.2, max_tokens=40)
            # Extract first float
            import re
            m = re.search(r"(0\.[0-9]+|1\.0|1|0)", raw)
            if m:
                val = float(m.group(1))
                # Normalize if an integer 0/1 returned
                if val in (0.0, 1.0):
                    self._last_llm_probability = val
                    return val
                self._last_llm_probability = max(0.0, min(val, 1.0))
                return self._last_llm_probability
        except Exception:
            return None
        return None

    def get_probability(self, signal: Dict[str, Any]) -> Optional[float]:
        """Return success probability from ML if trained else LLM fallback."""
        prob = None
        if self._ml_model:
            # Attempt retrain if threshold met
            try:
                self._ml_model.maybe_retrain(force=False)
            except Exception:
                pass
            prob = self._ml_model.predict_success_probability(signal)
        if prob is None:
            prob = self._llm_probability(signal)
        return prob

    def get_closed_trade_count(self) -> int:
        model = self._ml_model
        if model and hasattr(model, 'get_closed_trade_count'):
            try:
                return model.get_closed_trade_count()
            except Exception:
                return 0
        return 0

    def get_pending_status(self) -> Optional[str]:
        # Pending if ML not trained enough yet
        if not self._ml_model:
            return "AI-only fallback"
        closed = self.get_closed_trade_count()
        if closed < ML_RETRAIN_THRESHOLD:
            return f"pending ({closed}/{ML_RETRAIN_THRESHOLD} closed trades)"
        return None
