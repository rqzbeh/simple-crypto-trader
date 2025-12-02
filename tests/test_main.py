import types

import numpy as np
import pandas as pd
import pytest
import yfinance as yf

# The tests import the module under test. Importing the module will execute some
# top-level initialization code (e.g., logging setup). The tests then use
# monkeypatch to intercept calls such as yfinance.Ticker.history and the LLM client.
import main as m


# Helper: small deterministic OHLCV DataFrame for tests
def create_sample_ohlcv(num_points: int = 120):
    # Use a deterministic sequence for reproducibility
    idx = pd.date_range(end=pd.Timestamp.now(), periods=num_points, freq="H")
    base = np.linspace(100, 110, num_points)
    df = pd.DataFrame(
        {
            "Open": base * 0.998,
            "High": base * 1.002,
            "Low": base * 0.997,
            "Close": base,
            "Volume": (1000 + np.arange(num_points)).astype(float),
        },
        index=idx,
    )
    return df


class FakeTicker:
    """Fake yfinance.Ticker replacement returning a synthetic DataFrame."""

    def __init__(self, symbol: str):
        self.symbol = symbol

    def history(self, period: str = "30d", interval: str = "1h"):
        return create_sample_ohlcv(120)


class FakeLLMClient:
    """Fake LLM client that returns a pre-defined chat text response."""

    def __init__(self, response_text: str):
        self._response = response_text

    def chat(self, messages=None, **kwargs):
        # Return a simplified string response consistent with prompt parsing expectations
        return self._response


class FakeNewsCache:
    """Minimal fake that satisfies NewsCache needs for tests."""

    def __init__(self):
        # Keep a shallow store for added analyses if needed for verification
        self.added = []

    def filter_new_articles(self, articles):
        # Return articles as new and no cached articles
        return articles, []

    def add_analysis(self, article, sentiment_score, reasoning):
        self.added.append((article, sentiment_score, reasoning))

    def get_stats(self):
        return {"total_cached": len(self.added), "will_reset_in_hours": 24}


class FakeSocialMonitor:
    """Fake Social Monitor returns an empty signals list or a simple structure."""

    def get_all_social_signals(self):
        # A minimal list representation - aggregate_social_sentiment may accept [] and return fallback
        return []


@pytest.fixture(autouse=True)
def reset_main_state(monkeypatch):
    """
    Ensure that we don't use a real yfinance client and replace the LLM client
    and other global dependencies with safe fakes. PyTest will use this fixture
    automatically for each test.
    """
    # Replace yfinance Ticker with our fake
    monkeypatch.setattr(yf, "Ticker", FakeTicker)

    # Stub the candlestick analysis used by get_market_data so we don't rely on external libs
    monkeypatch.setattr(
        m,
        "get_all_candlestick_indicators",
        lambda df: {"atr": {"percent": 0.01}, "candlestick": {"signal": 0.0}},
    )

    # Replace the news cache to avoid persistent file operations
    monkeypatch.setattr(m, "get_news_cache", lambda: FakeNewsCache())

    # Replace Social Media Monitor to avoid API calls and rate limits
    monkeypatch.setattr(m, "SocialMediaMonitor", FakeSocialMonitor)

    # Ensure cached functions are cleared if previously used
    try:
        m.get_market_data.cache_clear()
    except Exception:
        # Not fatal; cache may not exist in some contexts
        pass

    yield

    # No special teardown required; monkeypatch will revert global monkeypatches


def test_get_market_data_returns_expected_keys_and_types(monkeypatch):
    """
    Test that get_market_data returns a dict that contains price, volatility,
    atr_pct, and indicators and that the types are as expected.
    """
    # Call the function under test
    symbol = "BTC-USD"
    m.get_market_data.cache_clear()
    result = m.get_market_data(symbol)

    assert isinstance(result, dict), "get_market_data should return a dictionary"
    assert "price" in result and isinstance(result["price"], float), (
        "price must be present and float"
    )
    assert "volatility" in result and isinstance(result["volatility"], float), (
        "volatility must be present and float"
    )
    assert "atr_pct" in result and isinstance(result["atr_pct"], float), (
        "atr_pct must be present and float"
    )
    assert "indicators" in result and isinstance(result["indicators"], dict), (
        "indicators must be present and a dict"
    )


def test_analyze_sentiment_with_llm_normalizes_100_scale(monkeypatch):
    """
    When the LLM returns a large-scale score such as 45 (assumed -100..100 scale),
    analyze_sentiment_with_llm should normalize to 0.45 (scale -1..1)
    """
    # Stub LLM client to return a 'SCORE' in 0..100 range
    monkeypatch.setattr(
        m, "llm_client", FakeLLMClient("SCORE: 45\nREASON: Very bullish changes.")
    )

    # Articles to analyze
    articles = [
        {
            "title": "Major adoption news",
            "description": "Large player buys millions in BTC.",
            "publishedAt": "2025-12-02T12:00:00Z",
            "source": "DEMO",
        }
    ]

    # Run sentiment analysis
    result = m.analyze_sentiment_with_llm(articles, symbol="BTC")
    assert result is not None and isinstance(result, tuple), (
        "analyze_sentiment_with_llm should return a tuple"
    )
    score, reasoning = result
    # Score should be a float and normalized (45 -> 0.45)
    assert isinstance(score, float), "Score should be a float"
    assert abs(score - 0.45) < 1e-8, f"Normalized score expected 0.45, got {score}"


def test_analyze_sentiment_with_llm_linear_scale_01(monkeypatch):
    """
    When the LLM returns a score already in -1..1 range (e.g., 0.8),
    analyze_sentiment_with_llm should return the same value (no division by 100).
    """
    monkeypatch.setattr(
        m, "llm_client", FakeLLMClient("SCORE: 0.8\nREASON: Mildly bullish.")
    )
    articles = [
        {
            "title": "Upgrade success",
            "description": "A successful network upgrade for a major chain.",
            "publishedAt": "2025-12-02T12:00:00Z",
            "source": "DEMO",
        }
    ]

    result = m.analyze_sentiment_with_llm(articles, symbol="ETH")
    assert result is not None and isinstance(result, tuple)
    score, _ = result
    assert abs(score - 0.8) < 1e-8, f"Expected score 0.8, got {score}"


def test_analyze_sentiment_with_llm_returns_none_if_no_llm(monkeypatch):
    """
    When llm_client is None, the function should return None and a meaningful message
    indicating that AI is unavailable (no trade signals).
    """
    monkeypatch.setattr(m, "llm_client", None)
    articles = [
        {
            "title": "News again",
            "description": "Some neutral news",
            "publishedAt": "2025-12-02T12:00:00Z",
            "source": "DEMO",
        }
    ]

    result = m.analyze_sentiment_with_llm(articles, symbol="BTC")
    assert result is not None and isinstance(result, tuple)
    score, reason = result
    assert score is None, "Should return None when the LLM client is not available"
    assert isinstance(reason, str) and "AI unavailable" in reason
