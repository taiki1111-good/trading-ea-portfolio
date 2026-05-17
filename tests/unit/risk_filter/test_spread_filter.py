from src.risk_filter.spread_filter import SpreadFilter
from src.risk_filter.types import SpreadFilterConfig


def test_spread_filter_allows_max_spread():
    config = SpreadFilterConfig(max_spread_pips=2.5)
    result = SpreadFilter.check(2.5, config)

    assert result.spread_ok is True
    assert "within allowed" in result.spread_filter_reason


def test_spread_filter_rejects_above_max_spread():
    config = SpreadFilterConfig(max_spread_pips=2.5)
    result = SpreadFilter.check(2.6, config)

    assert result.spread_ok is False
    assert "exceeds max allowed" in result.spread_filter_reason


def test_spread_filter_rejects_negative_spread():
    config = SpreadFilterConfig(max_spread_pips=2.5)
    result = SpreadFilter.check(-0.1, config)

    assert result.spread_ok is False
    assert "invalid spread" in result.spread_filter_reason
