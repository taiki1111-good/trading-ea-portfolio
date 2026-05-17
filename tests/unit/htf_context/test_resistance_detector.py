from datetime import datetime, timezone

from src.data.types import PriceBar
from src.htf_context.resistance_detector import ResistanceDetector
from src.htf_context.types import ResistanceConfig


def test_resistance_detector_returns_true_for_far_resistance():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.0, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=1.2, low=0.9, close=1.0, spread=0.1, volume=10),
    ]
    result = ResistanceDetector.detect(bars, ResistanceConfig(lookback=2, min_distance=0.1))
    assert result.htf_resistance_ok
    assert "recent_high" in result.resistance_reason


def test_resistance_detector_returns_false_when_close_near_high():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.0, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.95, close=1.09, spread=0.1, volume=10),
    ]
    result = ResistanceDetector.detect(bars, ResistanceConfig(lookback=2, min_distance=0.02))
    assert not result.htf_resistance_ok
    assert "distance" in result.resistance_reason


def test_resistance_detector_returns_false_with_insufficient_input():
    result = ResistanceDetector.detect([])
    assert not result.htf_resistance_ok
    assert result.resistance_reason
