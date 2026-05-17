import pytest

from src.evaluator import MetricsCalculator


def test_metrics_calculator_computes_basic_metrics():
    trade_logs = [
        {"pnl": 10.0},
        {"pnl": -5.0},
        {"realized_pnl": 2.0},
    ]

    result = MetricsCalculator.calculate(trade_logs)

    assert result.trade_count == 3
    assert result.win_rate == 2 / 3
    assert result.average_pnl == pytest.approx((10.0 + -5.0 + 2.0) / 3)
    assert result.profit_factor == pytest.approx(12.0 / 5.0)
    assert result.max_drawdown == pytest.approx(5.0)
    assert result.evaluation_reason.startswith("Metrics computed")


def test_metrics_calculator_returns_reason_if_pnl_missing():
    trade_logs = [
        {"order_result": "filled"},
        {"signal_type": "long_entry"},
    ]

    result = MetricsCalculator.calculate(trade_logs)

    assert result.trade_count == 2
    assert result.win_rate is None
    assert result.average_pnl is None
    assert result.profit_factor is None
    assert result.max_drawdown is None
    assert "pnl or realized_pnl missing" in result.evaluation_warnings[0]
