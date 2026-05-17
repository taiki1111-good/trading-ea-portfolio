from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.backtest.backtest_runner import BacktestRunner, EntryEvent
from src.backtest.types import BacktestConfig
from src.data.types import PriceBar
from src.data.price_loader import PriceDataLoader


FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"
PRICE_FIXTURE = FIXTURE_DIR / "backtest_minimal_long_win.csv"


def test_backtest_runner_generates_at_least_one_trade():
    price_frame = PriceDataLoader.load_from_csv(str(PRICE_FIXTURE), timeframe="H1")
    config = BacktestConfig(run_id="unit_backtest_runner", max_holding_bars=10)

    def provider(i, window):
        assert len(window) == i + 1
        assert window[-1].timestamp == price_frame[i].timestamp
        if i == 0:
            return EntryEvent(
                entry_index=0,
                direction="long",
                lot=1.0,
                stop_loss=99.0,
                take_profit=101.0,
                entry_reason="unit_test_entry",
            )
        return None

    result = BacktestRunner.run(price_frame=price_frame, config=config, entry_event_provider=provider)
    assert len(result.trades) >= 1
    assert len(result.trade_logs) >= 1
    assert result.trade_logs[0]["exit_reason"]
    assert result.trade_logs[0]["entry_reason"] == "unit_test_entry"
    assert result.trade_logs[0]["signal_reason"] == ""
    assert result.trade_logs[0]["risk_reason"] == ""
    assert result.trade_logs[0]["filter_reason"] == ""
    assert result.trade_logs[0]["fallback_used"] is False
    assert result.trade_logs[0]["structure_source"] == ""
    assert result.trade_logs[0]["entry_time"]
    assert result.trade_logs[0]["exit_time"]


def test_backtest_runner_does_not_exit_on_entry_bar_even_if_intrabar_levels_hit():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = [
        # Entry bar: both SL/TP would be hit intrabar, but exit must be suppressed on entry bar.
        PriceBar(timestamp=t0, open=100.0, high=101.2, low=98.8, close=100.0, spread=0.2, volume=100.0),
        # Next bar: TP hit, SL not hit -> exit should happen here as take_profit.
        PriceBar(timestamp=t0 + timedelta(hours=1), open=100.0, high=101.2, low=99.5, close=100.8, spread=0.2, volume=100.0),
    ]
    config = BacktestConfig(run_id="unit_intrabar", max_holding_bars=10)

    def provider(i, window):
        assert len(window) == i + 1
        assert window[-1] is bars[i]
        if i == 0:
            return EntryEvent(
                entry_index=0,
                direction="long",
                lot=1.0,
                stop_loss=99.0,
                take_profit=101.0,
                entry_reason="unit_intrabar_entry",
            )
        return None

    result = BacktestRunner.run(price_frame=bars, config=config, entry_event_provider=provider)
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "take_profit"
    assert result.trades[0].exit_time == bars[1].timestamp


def test_backtest_runner_propagates_reason_fields_from_entry_event_to_trade_log():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = [
        PriceBar(timestamp=t0, open=100.0, high=100.5, low=99.8, close=100.0, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=100.0, high=101.5, low=99.9, close=101.0, spread=0.2, volume=100.0),
    ]
    config = BacktestConfig(run_id="unit_reason_propagation", max_holding_bars=10)

    def provider(i, window):
        assert len(window) == i + 1
        if i == 0:
            return EntryEvent(
                entry_index=0,
                direction="long",
                lot=1.0,
                stop_loss=99.0,
                take_profit=101.0,
                entry_reason="entry_by_pipeline",
                signal_reason="signal_third_wave_break",
                risk_reason="fixed_sl_tp | placeholder_fixed_lot",
                filter_reason="all risk filters passed",
                fallback_used=True,
                structure_source="heuristic_fallback",
            )
        return None

    result = BacktestRunner.run(price_frame=bars, config=config, entry_event_provider=provider)
    assert len(result.trade_logs) == 1
    trade_log = result.trade_logs[0]
    assert trade_log["entry_reason"] == "entry_by_pipeline"
    assert trade_log["signal_reason"] == "signal_third_wave_break"
    assert trade_log["risk_reason"] == "fixed_sl_tp | placeholder_fixed_lot"
    assert trade_log["filter_reason"] == "all risk filters passed"
    assert trade_log["fallback_used"] is True
    assert trade_log["structure_source"] == "heuristic_fallback"
