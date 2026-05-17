from datetime import datetime, timezone

from src.backtest.backtest_logger_adapter import BacktestLoggerAdapter
from src.backtest.types import BacktestTrade


def test_backtest_logger_adapter_trade_to_dict_contains_pnl_fields():
    trade = BacktestTrade(
        direction="long",
        entry_price=100.0,
        exit_price=101.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        exit_time=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        pnl=1.0,
        realized_pnl=1.0,
        exit_reason="take_profit",
    )
    record = BacktestLoggerAdapter.to_trade_log(trade=trade, stop_loss=99.0, take_profit=101.0)

    assert record["order_result"] == "filled"
    assert record["pnl"] == 1.0
    assert record["realized_pnl"] == 1.0
    assert record["exit_reason"]

