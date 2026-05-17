from datetime import datetime, timezone

from src.data.types import PriceBar
from src.htf_context.trend_detector import TrendDetector
from src.htf_context.types import HTF_TREND_DOWN, HTF_TREND_NEUTRAL, HTF_TREND_UP, TrendConfig


def test_trend_detector_returns_up_down_neutral():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.0, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=1.2, low=0.9, close=1.1, spread=0.1, volume=10),
    ]
    result = TrendDetector.detect(bars, TrendConfig(lookback=2, min_strength=0.0))
    assert result.htf_trend_dir == HTF_TREND_UP

    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.1, high=1.2, low=1.0, close=1.1, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.0, spread=0.1, volume=10),
    ]
    result = TrendDetector.detect(bars, TrendConfig(lookback=2, min_strength=0.0))
    assert result.htf_trend_dir == HTF_TREND_DOWN

    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.0, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.0, spread=0.1, volume=10),
    ]
    result = TrendDetector.detect(bars, TrendConfig(lookback=2, min_strength=0.0))
    assert result.htf_trend_dir == HTF_TREND_NEUTRAL


def test_trend_strength_is_bounded():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=2.0, low=1.0, close=1.0, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=2.0, low=1.0, close=2.0, spread=0.1, volume=10),
    ]
    result = TrendDetector.detect(bars)
    assert 0.0 <= result.htf_trend_strength <= 1.0


def test_trend_detector_returns_neutral_and_reason_when_insufficient():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.0, low=1.0, close=1.0, spread=0.1, volume=10),
    ]
    result = TrendDetector.detect(bars)
    assert result.htf_trend_dir == HTF_TREND_NEUTRAL
    assert result.trend_reason
