from datetime import datetime, timezone

from src.data.types import PriceBar
from src.ltf_structure.swing_extractor import SwingExtractor
from src.ltf_structure.types import SwingConfig


def test_swing_extractor_returns_high_and_low_points():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.00, high=1.01, low=0.99, close=1.00, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), open=1.00, high=1.03, low=0.98, close=1.02, spread=0.1, volume=11),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), open=1.02, high=1.05, low=0.97, close=1.04, spread=0.1, volume=12),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 15, tzinfo=timezone.utc), open=1.04, high=1.04, low=0.95, close=0.96, spread=0.1, volume=13),
    ]

    result = SwingExtractor.extract(bars, SwingConfig(window=2, causal=True))

    assert result.swing_points
    assert any(point.swing_type == "high" for point in result.swing_points)
    assert any(point.swing_type == "low" for point in result.swing_points)
    assert result.swing_reason


def test_swing_extractor_returns_empty_and_reason_when_not_enough_bars():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.00, high=1.01, low=0.99, close=1.00, spread=0.1, volume=10),
    ]

    result = SwingExtractor.extract(bars, SwingConfig(window=2, causal=True))

    assert result.swing_points == []
    assert result.swing_reason
