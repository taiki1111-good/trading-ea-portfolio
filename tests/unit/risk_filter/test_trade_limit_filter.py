from src.risk_filter.trade_limit_filter import TradeLimitFilter
from src.risk_filter.types import TradeLimitConfig


def test_trade_limit_filter_rejects_when_daily_trade_count_reached():
    config = TradeLimitConfig(max_daily_trades=3, max_losing_streak=5)
    result = TradeLimitFilter.check(3, 0, config)

    assert result.limit_ok is False
    assert result.max_trade_reached_flag is True
    assert "daily trade count" in result.limit_filter_reason


def test_trade_limit_filter_rejects_when_losing_streak_reached():
    config = TradeLimitConfig(max_daily_trades=5, max_losing_streak=2)
    result = TradeLimitFilter.check(1, 2, config)

    assert result.limit_ok is False
    assert result.max_trade_reached_flag is False
    assert "losing streak" in result.limit_filter_reason
