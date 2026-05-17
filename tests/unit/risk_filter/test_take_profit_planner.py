from src.risk_filter.take_profit_planner import TakeProfitPlanner
from src.risk_filter.types import TakeProfitConfig
from src.signal.types import SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY


def test_take_profit_planner_returns_long_entry_take_profit():
    config = TakeProfitConfig(fixed_take_profit_distance=0.02)
    result = TakeProfitPlanner.plan(SIGNAL_LONG_ENTRY, 1.2345, config)

    assert result.take_profit == 1.2545
    assert result.take_profit > 1.2345
    assert "fixed_sl_tp" in result.take_profit_reason


def test_take_profit_planner_returns_short_entry_take_profit():
    config = TakeProfitConfig(fixed_take_profit_distance=0.02)
    result = TakeProfitPlanner.plan(SIGNAL_SHORT_ENTRY, 1.2345, config)

    assert result.take_profit == 1.2145
    assert result.take_profit < 1.2345
    assert "fixed_sl_tp" in result.take_profit_reason


def test_take_profit_planner_returns_none_when_distance_invalid():
    config = TakeProfitConfig(fixed_take_profit_distance=0.0)
    result = TakeProfitPlanner.plan(SIGNAL_LONG_ENTRY, 1.2345, config)

    assert result.take_profit is None
    assert "invalid_take_profit" in result.take_profit_reason
