from pathlib import Path

import pytest

from src.backtest.backtest_runner import BacktestRunner, EntryEvent
from src.backtest.types import BacktestConfig
from src.data.price_loader import PriceDataLoader


FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def _run_one(price_fixture: Path, config: BacktestConfig, entry: EntryEvent):
    price_frame = PriceDataLoader.load_from_csv(str(price_fixture), timeframe="H1")

    def provider(i, window):
        _ = window
        if i == entry.entry_index:
            return entry
        return None

    return BacktestRunner.run(price_frame=price_frame, config=config, entry_event_provider=provider)


def test_scenario_long_win_take_profit():
    result = _run_one(
        FIXTURE_DIR / "backtest_minimal_long_win.csv",
        BacktestConfig(run_id="sc_long_win", max_holding_bars=10),
        EntryEvent(entry_index=0, direction="long", lot=1.0, stop_loss=99.0, take_profit=101.0, entry_reason="scenario"),
    )
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "take_profit"
    assert result.trades[0].realized_pnl > 0


def test_scenario_long_loss_stop_loss():
    result = _run_one(
        FIXTURE_DIR / "backtest_minimal_long_loss.csv",
        BacktestConfig(run_id="sc_long_loss", max_holding_bars=10),
        EntryEvent(entry_index=0, direction="long", lot=1.0, stop_loss=99.0, take_profit=101.0, entry_reason="scenario"),
    )
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "stop_loss"
    assert result.trades[0].realized_pnl < 0


def test_scenario_short_win_take_profit():
    result = _run_one(
        FIXTURE_DIR / "backtest_minimal_short_win.csv",
        BacktestConfig(run_id="sc_short_win", max_holding_bars=10),
        EntryEvent(entry_index=0, direction="short", lot=1.0, stop_loss=101.0, take_profit=99.0, entry_reason="scenario"),
    )
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "take_profit"
    assert result.trades[0].realized_pnl > 0


def test_scenario_short_loss_stop_loss():
    result = _run_one(
        FIXTURE_DIR / "backtest_minimal_short_loss.csv",
        BacktestConfig(run_id="sc_short_loss", max_holding_bars=10),
        EntryEvent(entry_index=0, direction="short", lot=1.0, stop_loss=101.0, take_profit=99.0, entry_reason="scenario"),
    )
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "stop_loss"
    assert result.trades[0].realized_pnl < 0


def test_scenario_max_holding_bars_close_exit():
    result = _run_one(
        FIXTURE_DIR / "backtest_minimal_max_holding.csv",
        BacktestConfig(run_id="sc_max_hold", max_holding_bars=1),
        EntryEvent(entry_index=0, direction="long", lot=1.0, stop_loss=99.0, take_profit=101.0, entry_reason="scenario"),
    )
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "close"
    assert result.trades[0].realized_pnl == pytest.approx(0.2)
