from datetime import datetime, timezone

from src.data.types import PriceBar
from src.ltf_structure.breakout_detector import BreakoutDetector
from src.ltf_structure.types import SwingPoint


def test_breakout_detector_ignores_current_bar_swing_high_level():
    price_frame = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.00, high=1.03, low=0.99, close=1.01, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), open=1.01, high=1.10, low=1.00, close=1.08, spread=0.1, volume=11),
    ]
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.02, swing_type="high"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=1.10, swing_type="high"),
    ]

    result = BreakoutDetector.detect(price_frame, swing_points)

    assert result.breakout_flag is True
    assert result.breakout_direction == "long"
    assert result.breakout_level == 1.02
    assert result.breakout_reason


def test_breakout_detector_returns_long_breakout_against_prior_swing_high():
    price_frame = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.00, high=1.03, low=0.99, close=1.00, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), open=1.00, high=1.04, low=0.99, close=1.06, spread=0.1, volume=11),
    ]
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.05, swing_type="high"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=1.07, swing_type="high"),
    ]

    result = BreakoutDetector.detect(price_frame, swing_points)

    assert result.breakout_flag is True
    assert result.breakout_direction == "long"
    assert result.breakout_level == 1.05
    assert result.breakout_reason


def test_breakout_detector_ignores_current_bar_swing_low_level():
    price_frame = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.10, high=1.12, low=1.02, close=1.08, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), open=1.08, high=1.09, low=0.97, close=0.98, spread=0.1, volume=11),
    ]
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.00, swing_type="low"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=0.97, swing_type="low"),
    ]

    result = BreakoutDetector.detect(price_frame, swing_points)

    assert result.breakout_flag is True
    assert result.breakout_direction == "short"
    assert result.breakout_level == 1.00
    assert result.breakout_reason


def test_breakout_detector_returns_short_breakout_against_prior_swing_low():
    price_frame = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.10, high=1.12, low=1.02, close=1.08, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), open=1.08, high=1.09, low=0.97, close=0.95, spread=0.1, volume=11),
    ]
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.00, swing_type="low"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=0.96, swing_type="low"),
    ]

    result = BreakoutDetector.detect(price_frame, swing_points)

    assert result.breakout_flag is True
    assert result.breakout_direction == "short"
    assert result.breakout_level == 1.00
    assert result.breakout_reason


def test_breakout_detector_returns_neutral_when_no_prior_swing_points():
    price_frame = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.00, high=1.04, low=0.98, close=1.01, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), open=1.01, high=1.03, low=0.99, close=1.02, spread=0.1, volume=11),
    ]
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=1.05, swing_type="high"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=0.98, swing_type="low"),
    ]

    result = BreakoutDetector.detect(price_frame, swing_points)

    assert result.breakout_flag is False
    assert result.breakout_direction == "neutral"
    assert result.breakout_level == 0.0
    assert "no prior swing high/low" in result.breakout_reason


def test_breakout_detector_returns_neutral_when_no_breakout():
    price_frame = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.00, high=1.04, low=0.98, close=1.01, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), open=1.01, high=1.03, low=0.99, close=1.02, spread=0.1, volume=11),
    ]
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.05, swing_type="high"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=0.98, swing_type="low"),
    ]

    result = BreakoutDetector.detect(price_frame, swing_points)

    assert result.breakout_flag is False
    assert result.breakout_direction == "neutral"
    assert result.breakout_reason
