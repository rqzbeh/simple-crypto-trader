import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib

from config import (
    ML_MODEL_FILE,
    ML_SCALER_FILE,
    ML_MIN_CONFIDENCE,
    ML_RETRAIN_THRESHOLD,
    TRADE_LOG_FILE
)

class TradeOutcomeModel:
    """RandomForest-based model predicting probability a trade will be profitable.
    Trains incrementally on closed trades from TRADE_LOG_FILE.
    """

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.last_train_count: int = 0
        self._prob_cache: Dict[Any, float] = {}
        self._cache_max = 500
        self._load()

    def _load(self):
        try:
            if os.path.exists(ML_MODEL_FILE):
                self.model = joblib.load(ML_MODEL_FILE)
            if os.path.exists(ML_SCALER_FILE):
                self.scaler = joblib.load(ML_SCALER_FILE)
        except Exception:
            self.model = None
            self.scaler = None

    def _save(self):
        if self.model:
            joblib.dump(self.model, ML_MODEL_FILE)
        if self.scaler:
            joblib.dump(self.scaler, ML_SCALER_FILE)

    def _load_dataset(self) -> pd.DataFrame:
        if not os.path.exists(TRADE_LOG_FILE):
            return pd.DataFrame()
        try:
            with open(TRADE_LOG_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            return pd.DataFrame()

        rows = []
        for t in data:
            if t.get('status') not in ['closed', 'won', 'lost', 'completed', 'stopped']:
                continue
            # Look for profit in actual_profit field (used by main.py) or result.profit (legacy)
            profit = t.get('actual_profit', t.get('result', {}).get('profit', 0))
            # Binary label: profit > 0 => success
            label = 1 if profit > 0 else 0
            rows.append({
                'sentiment_score': t.get('sentiment_score', 0),
                'technical_score': t.get('technical_score', 0),
                'confidence': t.get('confidence', 0),
                'rr_ratio': t.get('rr_ratio', 0),
                'stop_pct': t.get('stop_pct', 0),
                'expected_profit_pct': t.get('expected_profit_pct', 0),
                'leverage': t.get('leverage', 0),
                'label': label
            })
        return pd.DataFrame(rows)

    def maybe_retrain(self, force: bool = False) -> bool:
        df = self._load_dataset()
        if df.empty:
            return False
        if len(df) < ML_RETRAIN_THRESHOLD and not force:
            return False
        if not force and self.last_train_count == len(df):
            return False

        X = df.drop('label', axis=1).to_numpy()
        y = df['label'].to_numpy()

        # Initialize scaler if needed
        if self.scaler is None:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.fit_transform(X)  # retrain scaler for drift

        self.model = RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            min_samples_leaf=3,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_scaled, y)
        preds = self.model.predict(X_scaled)
        acc = accuracy_score(y, preds)
        self.last_train_count = len(df)
        self._save()
        # Clear probability cache after retrain (model changed)
        self._prob_cache.clear()
        print(f"[ML] Model retrained on {len(df)} trades | acc={acc:.3f}")
        return True

    def predict_success_probability(self, signal: Dict[str, Any]) -> Optional[float]:
        if not self.model or not self.scaler:
            return None
        try:
            feat_tuple = (
                round(signal.get('sentiment_score', 0), 5),
                round(signal.get('technical_score', 0), 5),
                round(signal.get('confidence', 0), 5),
                round(signal.get('rr_ratio', 0), 5),
                round(signal.get('stop_pct', 0), 5),
                round(signal.get('expected_profit_pct', 0), 5),
                round(signal.get('leverage', 0), 5)
            )
            if feat_tuple in self._prob_cache:
                return self._prob_cache[feat_tuple]
            features = np.array([list(feat_tuple)])
            Xs = self.scaler.transform(features)
            prob = float(self.model.predict_proba(Xs)[0][1])
            # Maintain bounded cache size
            if len(self._prob_cache) >= self._cache_max:
                # Remove an arbitrary (FIFO not guaranteed) item
                self._prob_cache.pop(next(iter(self._prob_cache)))
            self._prob_cache[feat_tuple] = prob
            return prob
        except Exception as e:
            print(f"[ML] prediction error: {e}")
            return None

    def get_closed_trade_count(self) -> int:
        """Return number of closed trades available for training."""
        df = self._load_dataset()
        return len(df)

# Singleton accessor
_ml_instance: Optional[TradeOutcomeModel] = None

def get_ml_model() -> TradeOutcomeModel:
    global _ml_instance
    if _ml_instance is None:
        _ml_instance = TradeOutcomeModel()
    return _ml_instance
