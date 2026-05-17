from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from scripts.analyze_counterfactual_exits import TradeRecord
from scripts.replay_counterfactual_exits_m1 import M1Bar
from scripts.replay_counterfactual_exits_m1 import load_m1_bars_in_range
from scripts.replay_counterfactual_exits_m1 import run_m1_replay


def _build_bars() -> tuple[list[M1Bar], dict[datetime, int]]:
    start = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    bars = []
    for i in range(8):
        ts = start + timedelta(minutes=i)
        bars.append(M1Bar(ts, 100.0, 100.2 + 0.05 * i, 99.8 - 0.02 * i, 100.0 + 0.01 * i))
    return bars, {b.timestamp: i for i, b in enumerate(bars)}


def test_load_m1_bars_in_range_minimal(tmp_path) -> None:
    p = tmp_path / "m1.csv"
    p.write_text("\n".join([
        "2024.01.01,00:00,100,101,99,100.5,1",
        "2024.01.01,00:01,100.5,101.2,100.1,100.8,1",
    ]) + "\n", encoding="utf-8")
    s = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    e = datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc)
    bars, idx = load_m1_bars_in_range(p, s, e)
    assert len(bars) == 2
    assert bars[0].timestamp in idx


def test_entry_same_m1_bar_no_exit() -> None:
    bars, idx = _build_bars()
    t = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 102.0, bars[1].timestamp, "", 0.0)
    rows, _ = run_m1_replay([t], bars, idx, "baseline_fixed_exit", 3)
    assert rows[0]["accepted_entry"] is True
    assert int(rows[0]["holding_minutes"]) >= 1


def test_position_open_skips_next_entry() -> None:
    bars, idx = _build_bars()
    t1 = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 105.0, bars[3].timestamp, "", 0.0)
    t2 = TradeRecord(1, "short_entry", "short", bars[1].timestamp, 100.0, 101.0, 98.0, bars[4].timestamp, "", 0.0)
    rows, summary = run_m1_replay([t1, t2], bars, idx, "baseline_fixed_exit", 3)
    assert summary["skipped_due_to_open_position_count"] == 1
    assert any(r["skipped_reason"] == "skipped_due_to_open_position" for r in rows)


def test_max_holding_minutes_not_exceeded() -> None:
    bars, idx = _build_bars()
    t = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 90.0, 110.0, bars[-1].timestamp, "", 0.0)
    rows, summary = run_m1_replay([t], bars, idx, "baseline_fixed_exit", 2)
    assert int(rows[0]["holding_minutes"]) <= 2
    assert summary["max_holding_minutes"] <= 2


def test_long_short_pnl_sign() -> None:
    bars = [
        M1Bar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        M1Bar(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), 100, 101.2, 99.8, 101),
        M1Bar(datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc), 101, 101.1, 100.4, 100.7),
        M1Bar(datetime(2024, 1, 1, 0, 3, tzinfo=timezone.utc), 100.7, 100.8, 98.7, 99),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    long_t = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 101.0, bars[1].timestamp, "", 0.0)
    short_t = TradeRecord(1, "short_entry", "short", bars[2].timestamp, 100.7, 102.0, 99.0, bars[3].timestamp, "", 0.0)
    rows, _ = run_m1_replay([long_t, short_t], bars, idx, "baseline_fixed_exit", 2)
    accepted = [r for r in rows if r["accepted_entry"]]
    assert float(accepted[0]["m1_replay_pnl"]) > 0
    assert float(accepted[1]["m1_replay_pnl"]) > 0


def test_simple_trailing_runs_on_m1() -> None:
    bars, idx = _build_bars()
    t = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 103.0, bars[-1].timestamp, "", 0.0)
    rows, summary = run_m1_replay([t], bars, idx, "simple_trailing_after_1R", 5)
    assert rows[0]["accepted_entry"] is True
    assert summary["accepted_trade_count"] == 1


def test_bar_timestamp_mode_uses_entry_time_directly() -> None:
    bars = [
        M1Bar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        M1Bar(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), 100, 100.2, 98.8, 99),
        M1Bar(datetime(2024, 1, 1, 0, 6, tzinfo=timezone.utc), 99, 99.2, 98.7, 99),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    t = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 101.0, bars[1].timestamp, "", 0.0)
    rows, _ = run_m1_replay([t], bars, idx, "baseline_fixed_exit", 10, entry_time_mode="bar_timestamp", entry_timeframe_minutes=5)
    assert rows[0]["m1_exit_time"] == bars[1].timestamp.isoformat()


def test_m5_close_mode_starts_after_entry_plus_5_minutes() -> None:
    bars = [
        M1Bar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        M1Bar(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), 100, 100.2, 98.8, 99),
        M1Bar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 99, 100.1, 99.2, 99.7),
        M1Bar(datetime(2024, 1, 1, 0, 6, tzinfo=timezone.utc), 99.7, 100.8, 99.6, 100.4),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    t = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 100.5, bars[-1].timestamp, "", 0.0)
    rows, _ = run_m1_replay([t], bars, idx, "baseline_fixed_exit", 10, entry_time_mode="m5_close", entry_timeframe_minutes=5)
    assert rows[0]["entry_effective_time"] == bars[2].timestamp.isoformat()
    assert rows[0]["m1_exit_time"] == bars[3].timestamp.isoformat()


def test_m5_close_mode_does_not_use_pre_effective_entry_bars() -> None:
    bars = [
        M1Bar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        M1Bar(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), 100, 100.1, 98.5, 99),
        M1Bar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 99, 99.8, 99.2, 99.5),
        M1Bar(datetime(2024, 1, 1, 0, 6, tzinfo=timezone.utc), 99.5, 100.7, 99.4, 100.6),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    t = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 100.6, bars[-1].timestamp, "", 0.0)
    rows, _ = run_m1_replay([t], bars, idx, "baseline_fixed_exit", 10, entry_time_mode="m5_close", entry_timeframe_minutes=5)
    assert rows[0]["m1_exit_reason"] == "take_profit"
    assert rows[0]["m1_exit_time"] == bars[3].timestamp.isoformat()


def test_invalid_or_missing_dat_errors(tmp_path) -> None:
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        load_m1_bars_in_range(missing, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc))

    broken = tmp_path / "broken.csv"
    broken.write_text("2024.01.01,00:00,100,101\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected 7 columns"):
        load_m1_bars_in_range(broken, datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc))
