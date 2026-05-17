from datetime import datetime, timezone

from src.data.types import PriceBar
from src.htf_context.support_detector import SupportDetector
from src.htf_context.types import SupportConfig


def test_support_detector_returns_true_for_far_support():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.2, low=1.0, close=1.1, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.1, high=1.3, low=1.05, close=1.2, spread=0.1, volume=10),
    ]
    result = SupportDetector.detect(bars, SupportConfig(lookback=2, min_distance=0.1))
    assert result.htf_support_ok
    assert "recent_low" in result.support_reason


def test_support_detector_returns_false_when_close_near_low():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.2, low=1.0, close=1.1, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.1, high=1.25, low=1.09, close=1.1, spread=0.1, volume=10),
    ]
    result = SupportDetector.detect(bars, SupportConfig(lookback=2, min_distance=0.15))
    assert not result.htf_support_ok
    assert "distance" in result.support_reason


def test_support_detector_returns_false_with_insufficient_input():
    result = SupportDetector.detect([])
    assert not result.htf_support_ok
    assert result.support_reason
