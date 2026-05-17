from datetime import datetime, timezone

from src.data.types import PriceBar
from src.htf_context.assembler import ContextAssembler
from src.htf_context.support_detector import SupportDetector
from src.htf_context.resistance_detector import ResistanceDetector
from src.htf_context.trend_detector import TrendDetector
from src.htf_context.types import (
    HTF_BIAS_LONG,
    HTF_BIAS_NEUTRAL,
    HTF_BIAS_SHORT,
    HTF_TREND_DOWN,
    HTF_TREND_UP,
    ResistanceConfig,
    SupportConfig,
    TrendConfig,
)


def test_context_assembler_produces_long_bias_when_up_and_resistance_ok():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.3, low=1.0, close=1.0, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=1.4, low=1.0, close=1.2, spread=0.1, volume=10),
    ]
    trend = TrendDetector.detect(bars, TrendConfig(lookback=2, min_strength=0.0))
    resistance = ResistanceDetector.detect(bars, ResistanceConfig(lookback=2, min_distance=0.1))
    support = SupportDetector.detect(bars, SupportConfig(lookback=2, min_distance=0.1))
    result = ContextAssembler.assemble(trend, resistance, support)

    assert result.htf_bias == HTF_BIAS_LONG
    assert result.htf_trend_dir == HTF_TREND_UP
    assert result.htf_context_reason


def test_context_assembler_produces_short_bias_when_down_and_support_ok():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.2, high=1.2, low=1.0, close=1.2, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.2, high=1.2, low=1.0, close=1.05, spread=0.1, volume=10),
    ]
    trend = TrendDetector.detect(bars, TrendConfig(lookback=2, min_strength=0.0))
    resistance = ResistanceDetector.detect(bars, ResistanceConfig(lookback=2, min_distance=0.1))
    support = SupportDetector.detect(bars, SupportConfig(lookback=2, min_distance=0.02))
    result = ContextAssembler.assemble(trend, resistance, support)

    assert result.htf_bias == HTF_BIAS_SHORT
    assert result.htf_trend_dir == HTF_TREND_DOWN
    assert "recent_low" in result.htf_context_reason


def test_context_assembler_defaults_to_neutral():
    bars = [
        PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.0, spread=0.1, volume=10),
        PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.0, high=1.05, low=0.9, close=1.02, spread=0.1, volume=10),
    ]
    trend = TrendDetector.detect(bars, TrendConfig(lookback=2, min_strength=0.3))
    resistance = ResistanceDetector.detect(bars, ResistanceConfig(lookback=2, min_distance=0.3))
    support = SupportDetector.detect(bars, SupportConfig(lookback=2, min_distance=0.3))
    result = ContextAssembler.assemble(trend, resistance, support, sub_reasons=["test reason"])

    assert result.htf_bias == HTF_BIAS_NEUTRAL
    assert result.htf_context_reason
