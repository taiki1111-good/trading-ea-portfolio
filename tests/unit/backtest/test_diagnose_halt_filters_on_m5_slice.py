from __future__ import annotations

import csv
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.diagnose_halt_filters_on_m5_slice import build_halted_entry_candidates
from scripts.diagnose_halt_filters_on_m5_slice import detect_price_shock_triggers
from scripts.diagnose_halt_filters_on_m5_slice import detect_volatility_spike_triggers
from scripts.diagnose_halt_filters_on_m5_slice import load_entry_candidates
from scripts.diagnose_halt_filters_on_m5_slice import load_m5_slice
from scripts.diagnose_halt_filters_on_m5_slice import merge_halt_windows
from scripts.diagnose_halt_filters_on_m5_slice import run_diagnostic
from scripts.diagnose_halt_filters_on_m5_slice import summarize


def _bar(ts: datetime, o: float, h: float, l: float, c: float) -> dict[str, object]:
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c, "spread": None, "volume": None}


def _base_time() -> datetime:
    return datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_detects_m5_shock() -> None:
    t0 = _base_time()
    bars = [
        _bar(t0, 100.00, 100.10, 100.00, 100.05),
        _bar(t0 + timedelta(minutes=5), 100.05, 100.50, 100.00, 100.10),
    ]
    triggers = detect_price_shock_triggers(bars, pip_size=0.01, shock_m5_pips=40, shock_m15_pips=999, cooldown_minutes_after_shock=15)
    assert any(t.halt_source == "m5_range" for t in triggers)


def test_detects_m15_shock_rolling3() -> None:
    t0 = _base_time()
    bars = [
        _bar(t0, 100.00, 100.10, 100.00, 100.05),
        _bar(t0 + timedelta(minutes=5), 100.05, 100.15, 100.00, 100.10),
        _bar(t0 + timedelta(minutes=10), 100.10, 100.80, 99.90, 100.20),
    ]
    triggers = detect_price_shock_triggers(bars, pip_size=0.01, shock_m5_pips=999, shock_m15_pips=70, cooldown_minutes_after_shock=15)
    assert any(t.halt_source == "m15_equivalent_rolling3" for t in triggers)


def test_detects_volatility_spike_by_atr_ratio() -> None:
    t0 = _base_time()
    bars = [
        _bar(t0 + timedelta(minutes=5 * i), 100 + i * 0.01, 100.10 + i * 0.01, 100.00 + i * 0.01, 100.05 + i * 0.01)
        for i in range(8)
    ]
    bars[-1] = _bar(t0 + timedelta(minutes=35), 100.07, 101.30, 99.80, 100.90)

    triggers = detect_volatility_spike_triggers(
        bars=bars,
        pip_size=0.01,
        atr_window=3,
        atr_median_window=3,
        atr_ratio_threshold=1.5,
        range_ratio_threshold=99,
        cooldown_minutes_after_volatility_spike=10,
    )
    assert any((t.atr_ratio or 0) > 1.5 for t in triggers)


def test_detects_volatility_spike_by_range_ratio() -> None:
    t0 = _base_time()
    bars = [
        _bar(t0 + timedelta(minutes=5 * i), 100, 100.10, 100.00, 100.05)
        for i in range(6)
    ]
    bars[-1] = _bar(t0 + timedelta(minutes=25), 100.00, 100.80, 100.00, 100.05)

    triggers = detect_volatility_spike_triggers(
        bars=bars,
        pip_size=0.01,
        atr_window=10,
        atr_median_window=3,
        atr_ratio_threshold=99,
        range_ratio_threshold=3.0,
        cooldown_minutes_after_volatility_spike=10,
    )
    assert any((t.range_ratio or 0) > 3.0 for t in triggers)


def test_merges_overlapping_or_contiguous_windows() -> None:
    t0 = _base_time()
    bars = [
        _bar(t0, 100, 100.6, 100.0, 100.1),
        _bar(t0 + timedelta(minutes=5), 100, 100.7, 100.1, 100.2),
        _bar(t0 + timedelta(minutes=10), 100, 100.8, 100.2, 100.3),
    ]
    shock = detect_price_shock_triggers(bars, pip_size=0.01, shock_m5_pips=40, shock_m15_pips=80, cooldown_minutes_after_shock=10)
    merged = merge_halt_windows(shock)
    assert len(merged) == 1
    assert "price_shock_halt" in merged[0].halt_reason


def test_extracts_entries_inside_halt_windows() -> None:
    t0 = _base_time()
    bars = [_bar(t0, 100, 100.8, 99.9, 100.2)]
    windows = merge_halt_windows(
        detect_price_shock_triggers(bars, pip_size=0.01, shock_m5_pips=50, shock_m15_pips=999, cooldown_minutes_after_shock=20)
    )
    entries = [
        {
            "entry_time": t0 + timedelta(minutes=10),
            "signal_type": "long_entry",
            "trade_id": "t1",
            "pnl": -5.0,
        }
    ]
    from scripts.diagnose_halt_filters_on_m5_slice import EntryCandidate

    halted = build_halted_entry_candidates([EntryCandidate(**entries[0])], windows, pip_size=0.01)
    assert len(halted) == 1
    assert halted[0]["would_be_halted"] is True


def _write_logs_for_dedup(tmp_path: Path) -> tuple[Path, Path]:
    trade_logs = tmp_path / "trade_logs.csv"
    decision_logs = tmp_path / "decision_logs.csv"

    with trade_logs.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "pnl"])
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:00:00+00:00",
                "signal_type": "long_entry",
                "trade_id": "A",
                "pnl": "-3",
            }
        )

    with decision_logs.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "entry_signal", "trade_ok"])
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:00:00+00:00",
                "signal_type": "long_entry",
                "trade_id": "A",
                "entry_signal": "true",
                "trade_ok": "true",
            }
        )
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:05:00+00:00",
                "signal_type": "short_entry",
                "trade_id": "",
                "entry_signal": "true",
                "trade_ok": "false",
            }
        )
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:05:00+00:00",
                "signal_type": "short_entry",
                "trade_id": "",
                "entry_signal": "true",
                "trade_ok": "false",
            }
        )

    return trade_logs, decision_logs


def test_dedup_by_trade_id_or_entry_time_signal(tmp_path: Path) -> None:
    trade_logs, decision_logs = _write_logs_for_dedup(tmp_path)
    entries, _warnings = load_entry_candidates(trade_logs, decision_logs)
    assert len(entries) == 2


def test_summary_avoided_missed_and_net_effect() -> None:
    from scripts.diagnose_halt_filters_on_m5_slice import HaltWindow

    t0 = _base_time()
    windows = [
        HaltWindow(t0, t0 + timedelta(minutes=10), "price_shock_halt", "m5_range", t0, 50.0, None, None, 10)
    ]
    halted_entries = [
        {
            "counterfactual_pnl": -0.04,
        },
        {
            "counterfactual_pnl": 0.025,
        },
    ]
    summary = summarize(windows, halted_entries, pip_size=0.01)
    assert summary["avoided_loss_pips"] == 4.0
    assert summary["missed_profit_pips"] == 2.5
    assert summary["net_counterfactual_effect_pips"] == 1.5


def test_summary_converts_positive_pnl_to_pips() -> None:
    summary = summarize(
        halt_windows=[],
        halted_entries=[{"counterfactual_pnl": 0.10}],
        pip_size=0.01,
    )
    assert summary["missed_profit_pips"] == 10.0


def test_summary_converts_negative_pnl_to_pips() -> None:
    summary = summarize(
        halt_windows=[],
        halted_entries=[{"counterfactual_pnl": -0.05}],
        pip_size=0.01,
    )
    assert summary["avoided_loss_pips"] == 5.0


def test_summary_net_effect_is_avoided_minus_missed() -> None:
    summary = summarize(
        halt_windows=[],
        halted_entries=[{"counterfactual_pnl": -0.05}, {"counterfactual_pnl": 0.10}],
        pip_size=0.01,
    )
    assert summary["net_counterfactual_effect_pips"] == -5.0


def test_missing_required_columns_raise_clear_error(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("timestamp,open,high,low\n2024-01-01T00:00:00Z,1,2,0.5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        load_m5_slice(bad_csv)


def _write_simple_m5_csv(path: Path) -> None:
    rows = [
        ["timestamp", "open", "high", "low", "close"],
        ["2024-01-01T00:00:00Z", "100.00", "100.70", "100.00", "100.30"],
        ["2024-01-01T00:05:00Z", "100.30", "100.60", "100.10", "100.20"],
        ["2024-01-01T00:10:00Z", "100.20", "100.40", "100.00", "100.10"],
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def _base_args(tmp_path: Path) -> Namespace:
    return Namespace(
        input_csv=str(tmp_path / "m5.csv"),
        decision_logs=str(tmp_path / "decision_logs.csv"),
        trade_logs=str(tmp_path / "trade_logs.csv"),
        output_dir=str(tmp_path / "out"),
        shock_m5_pips=40.0,
        shock_m15_pips=80.0,
        atr_window=2,
        atr_median_window=2,
        atr_ratio_threshold=2.0,
        range_ratio_threshold=2.0,
        cooldown_minutes_after_shock=10,
        cooldown_minutes_after_volatility_spike=10,
        instrument="USDJPY",
        pip_size=0.01,
        enable_price_shock=None,
        enable_volatility_spike=None,
    )


def test_trade_logs_valid_and_decision_logs_missing_columns_still_succeeds(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    with (tmp_path / "trade_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "pnl"])
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:05:00+00:00",
                "signal_type": "long_entry",
                "trade_id": "T1",
                "pnl": "-2.0",
            }
        )
    with (tmp_path / "decision_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "entry_signal"])
        writer.writeheader()
        writer.writerow({"timestamp": "2024-01-01T00:05:00+00:00", "entry_signal": "true"})

    result = run_diagnostic(_base_args(tmp_path))
    assert Path(result["halted_entries_csv"]).exists()


def test_decision_logs_skipped_warning_written_to_summary_md(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    with (tmp_path / "trade_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "pnl"])
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:05:00+00:00",
                "signal_type": "long_entry",
                "trade_id": "T1",
                "pnl": "-2.0",
            }
        )
    with (tmp_path / "decision_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp"])
        writer.writeheader()
        writer.writerow({"timestamp": "2024-01-01T00:05:00+00:00"})

    result = run_diagnostic(_base_args(tmp_path))
    summary_md = Path(result["summary_md"]).read_text(encoding="utf-8")
    assert "## Warnings" in summary_md
    assert "decision_logs missing required columns and skipped" in summary_md


def test_halted_entry_candidates_csv_has_counterfactual_pips(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    with (tmp_path / "trade_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "pnl"])
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:05:00+00:00",
                "signal_type": "long_entry",
                "trade_id": "T1",
                "pnl": "0.10",
            }
        )
    with (tmp_path / "decision_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp"])
        writer.writeheader()
        writer.writerow({"timestamp": "2024-01-01T00:05:00+00:00"})

    result = run_diagnostic(_base_args(tmp_path))
    rows = list(csv.DictReader(Path(result["halted_entries_csv"]).open("r", encoding="utf-8", newline="")))
    assert "counterfactual_pips" in rows[0]
    assert float(rows[0]["counterfactual_pips"]) == 10.0


def test_decision_logs_with_required_columns_are_used_as_supplement(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    with (tmp_path / "trade_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "pnl"])
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:05:00+00:00",
                "signal_type": "long_entry",
                "trade_id": "T1",
                "pnl": "-2.0",
            }
        )
    with (tmp_path / "decision_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["entry_time", "signal_type", "trade_id", "entry_signal", "trade_ok"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:10:00+00:00",
                "signal_type": "short_entry",
                "trade_id": "",
                "entry_signal": "true",
                "trade_ok": "false",
            }
        )
    entries, warnings = load_entry_candidates(tmp_path / "trade_logs.csv", tmp_path / "decision_logs.csv")
    assert len(entries) == 2
    assert warnings == []


def test_error_when_trade_logs_unusable_and_decision_logs_missing_required_columns(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    with (tmp_path / "trade_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "pnl"])
        writer.writeheader()
    with (tmp_path / "decision_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp"])
        writer.writeheader()
        writer.writerow({"timestamp": "2024-01-01T00:00:00+00:00"})

    with pytest.raises(ValueError, match="decision_logs missing required columns"):
        run_diagnostic(_base_args(tmp_path))


def _write_trade_and_decision_for_toggle(tmp_path: Path) -> None:
    with (tmp_path / "trade_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_time", "signal_type", "trade_id", "pnl"])
        writer.writeheader()
        writer.writerow(
            {
                "entry_time": "2024-01-01T00:05:00+00:00",
                "signal_type": "long_entry",
                "trade_id": "T1",
                "pnl": "-0.02",
            }
        )
    with (tmp_path / "decision_logs.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp"])
        writer.writeheader()
        writer.writerow({"timestamp": "2024-01-01T00:05:00+00:00"})


def test_default_enables_both_filters(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    _write_trade_and_decision_for_toggle(tmp_path)
    args = _base_args(tmp_path)
    result = run_diagnostic(args)
    assert result["summary"]["enabled_filters"] == "price_shock_halt|volatility_spike_halt"


def test_enable_price_shock_only(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    _write_trade_and_decision_for_toggle(tmp_path)
    args = _base_args(tmp_path)
    args.enable_price_shock = True
    args.enable_volatility_spike = None
    result = run_diagnostic(args)
    assert result["summary"]["enabled_filters"] == "price_shock_halt"


def test_enable_volatility_spike_only(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    _write_trade_and_decision_for_toggle(tmp_path)
    args = _base_args(tmp_path)
    args.enable_price_shock = None
    args.enable_volatility_spike = True
    result = run_diagnostic(args)
    assert result["summary"]["enabled_filters"] == "volatility_spike_halt"


def test_summary_outputs_include_enabled_filters(tmp_path: Path) -> None:
    _write_simple_m5_csv(tmp_path / "m5.csv")
    _write_trade_and_decision_for_toggle(tmp_path)
    args = _base_args(tmp_path)
    result = run_diagnostic(args)
    summary_csv_rows = list(
        csv.DictReader(Path(result["summary_csv"]).open("r", encoding="utf-8", newline=""))
    )
    assert "enabled_filters" in summary_csv_rows[0]
    summary_md = Path(result["summary_md"]).read_text(encoding="utf-8")
    assert "enabled_filters:" in summary_md
