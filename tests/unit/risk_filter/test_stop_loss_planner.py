from src.risk_filter.stop_loss_planner import StopLossPlanner
from src.risk_filter.types import StopLossConfig
from src.signal.types import SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY


def test_stop_loss_planner_returns_long_entry_stop_loss():
    config = StopLossConfig(fixed_stop_distance=0.01)
    result = StopLossPlanner.plan(SIGNAL_LONG_ENTRY, 1.2345, config)

    assert result.stop_loss == 1.2245
    assert result.stop_loss < 1.2345
    assert "fixed_sl_tp" in result.stop_loss_reason


def test_stop_loss_planner_returns_short_entry_stop_loss():
    config = StopLossConfig(fixed_stop_distance=0.01)
    result = StopLossPlanner.plan(SIGNAL_SHORT_ENTRY, 1.2345, config)

    assert result.stop_loss == 1.2445
    assert result.stop_loss > 1.2345
    assert "fixed_sl_tp" in result.stop_loss_reason


def test_stop_loss_planner_returns_none_when_distance_invalid():
    config = StopLossConfig(fixed_stop_distance=0.0)
    result = StopLossPlanner.plan(SIGNAL_LONG_ENTRY, 1.2345, config)

    assert result.stop_loss is None
    assert "invalid_stop_loss" in result.stop_loss_reason
