from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

from scripts.run_csv_replay_pipeline_dry_run import load_and_prepare_input
from scripts.run_csv_replay_pipeline_dry_run import main
from scripts.run_csv_replay_pipeline_dry_run import row_to_price_bar
from scripts.run_csv_replay_pipeline_dry_run import run_csv_replay_pipeline_dry_run


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _rows_with_warmup_and_replay() -> list[dict[str, object]]:
    return [
        {"timestamp": "2024-01-01 00:00:00", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.2, "spread_pips": 0.2, "volume": 10},
        {"timestamp": "2024-01-01 00:05:00", "open": 100.2, "high": 101.1, "low": 100.0, "close": 100.5, "spread_pips": 0.2, "volume": 12},
        {"timestamp": "2024-01-01 00:10:00", "open": 100.5, "high": 101.3, "low": 100.3, "close": 100.9, "spread_pips": 0.2, "volume": 15},
    ]


class _OkAdapter:
    def __init__(self) -> None:
        self._trace = {}

    def __call__(self, current_index, window):  # noqa: ANN001
        self._trace = {
            "entry_signal": False,
            "exit_signal": False,
            "signal_type": "none",
            "trade_ok": False,
            "decision_reason": "ok",
            "htf_filter_reason": "ok",
        }
        return None

    def get_last_decision_trace(self):  # noqa: ANN201
        return self._trace


class _EntryAdapter:
    def __init__(self) -> None:
        self._trace = {}

    def __call__(self, current_index, window):  # noqa: ANN001
        from src.backtest.backtest_runner import EntryEvent

        self._trace = {
            "entry_signal": True,
            "exit_signal": False,
            "signal_type": "long_entry",
            "trade_ok": True,
            "decision_reason": "entry",
            "htf_filter_reason": "aligned",
        }
        return EntryEvent(
            entry_index=current_index,
            direction="long",
            lot=0.1,
            stop_loss=window[-1].close - 0.01,
            take_profit=window[-1].close + 0.02,
            entry_reason="entry",
            signal_reason="signal",
            risk_reason="risk",
            filter_reason="filter",
        )

    def get_last_decision_trace(self):  # noqa: ANN201
        return self._trace


class _HtfTraceAdapter:
    def __init__(self) -> None:
        self._trace = {}

    def __call__(self, current_index, window):  # noqa: ANN001, ARG002
        self._trace = {
            "entry_signal": False,
            "exit_signal": False,
            "signal_type": "none",
            "trade_ok": False,
            "decision_reason": "htf-trace",
            "htf_filter_enabled": True,
            "htf_timeframe_policy": "H1_only",
            "htf_neutral_policy": "strict",
            "htf_trend_dir": "up",
            "htf_bias": "long_bias",
            "htf_direction_aligned": True,
            "htf_filter_reason": "htf_filter_v1: aligned=true",
            "htf_context_reason": "htf context trace",
        }
        return None

    def get_last_decision_trace(self):  # noqa: ANN201
        return self._trace


class _ErrorAdapter:
    def __call__(self, current_index, window):  # noqa: ANN001, ARG002
        raise RuntimeError("adapter boom")

    def get_last_decision_trace(self):  # noqa: ANN201
        return {}


def test_row_to_price_bar_conversion_and_fallbacks() -> None:
    row = {
        "timestamp": "2024-01-01 00:00:00",
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
    }
    bar = row_to_price_bar(row)
    assert str(bar.timestamp.tzinfo) in {"UTC", "UTC+00:00"}
    assert bar.open == 100.0
    assert bar.high == 101.0
    assert bar.low == 99.0
    assert bar.close == 100.5
    assert bar.spread == 0.0
    assert bar.volume == 0.0


def test_pipeline_adapter_ok_called_for_each_replay_bar(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    df, dup, ooo = load_and_prepare_input(csv_path)
    res = run_csv_replay_pipeline_dry_run(
        df=df,
        duplicate_timestamps=dup,
        out_of_order_timestamps=ooo,
        run_id="r_ok",
        warmup_start=pd.Timestamp("2024-01-01T00:00:00Z"),
        replay_start=pd.Timestamp("2024-01-01T00:05:00Z"),
        replay_end=pd.Timestamp("2024-01-01T00:15:00Z"),
        expected_timeframe_minutes=5,
        adapter=_OkAdapter(),
    )
    assert res.summary["pipeline_adapter_called_count"] == res.summary["replay_bar_count"]
    assert all(r["pipeline_adapter_status"] == "ok" for r in res.decision_logs)
    assert len(res.decision_logs) == res.summary["replay_bar_count"]
    assert all("htf_filter_enabled" in r for r in res.decision_logs)
    assert all("htf_timeframe_policy" in r for r in res.decision_logs)
    assert all("htf_neutral_policy" in r for r in res.decision_logs)
    assert all("htf_trend_dir" in r for r in res.decision_logs)
    assert all("htf_bias" in r for r in res.decision_logs)
    assert all("htf_direction_aligned" in r for r in res.decision_logs)
    assert all("htf_filter_reason" in r for r in res.decision_logs)
    assert all("htf_context_reason" in r for r in res.decision_logs)
    assert all(r["htf_filter_enabled"] is False for r in res.decision_logs)
    assert all(r["htf_timeframe_policy"] == "" for r in res.decision_logs)
    assert all(r["htf_neutral_policy"] == "" for r in res.decision_logs)
    assert all(r["htf_trend_dir"] == "" for r in res.decision_logs)
    assert all(r["htf_bias"] == "" for r in res.decision_logs)
    assert all(r["htf_direction_aligned"] is False for r in res.decision_logs)
    assert all(r["htf_filter_reason"] == "ok" for r in res.decision_logs)
    assert all(r["htf_context_reason"] == "" for r in res.decision_logs)


def test_trace_htf_fields_are_written_to_decision_logs(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    df, dup, ooo = load_and_prepare_input(csv_path)
    res = run_csv_replay_pipeline_dry_run(
        df=df,
        duplicate_timestamps=dup,
        out_of_order_timestamps=ooo,
        run_id="r_htf",
        warmup_start=pd.Timestamp("2024-01-01T00:00:00Z"),
        replay_start=pd.Timestamp("2024-01-01T00:05:00Z"),
        replay_end=pd.Timestamp("2024-01-01T00:15:00Z"),
        expected_timeframe_minutes=5,
        adapter=_HtfTraceAdapter(),
    )
    assert len(res.decision_logs) == res.summary["replay_bar_count"]
    row = res.decision_logs[0]
    assert row["htf_filter_enabled"] is True
    assert row["htf_timeframe_policy"] == "H1_only"
    assert row["htf_neutral_policy"] == "strict"
    assert row["htf_trend_dir"] == "up"
    assert row["htf_bias"] == "long_bias"
    assert row["htf_direction_aligned"] is True
    assert row["htf_filter_reason"] == "htf_filter_v1: aligned=true"
    assert row["htf_context_reason"] == "htf context trace"


def test_entry_event_sets_paper_candidate_and_no_real_order(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    df, dup, ooo = load_and_prepare_input(csv_path)
    res = run_csv_replay_pipeline_dry_run(
        df=df,
        duplicate_timestamps=dup,
        out_of_order_timestamps=ooo,
        run_id="r_entry",
        warmup_start=pd.Timestamp("2024-01-01T00:00:00Z"),
        replay_start=pd.Timestamp("2024-01-01T00:05:00Z"),
        replay_end=pd.Timestamp("2024-01-01T00:15:00Z"),
        expected_timeframe_minutes=5,
        adapter=_EntryAdapter(),
    )
    assert any(r["paper_order_action"] == "paper_candidate" for r in res.decision_logs)
    assert all(r["real_order_sent"] is False for r in res.decision_logs)
    assert all(r["broker_order_id"] == "" for r in res.decision_logs)
    assert all(r["no_real_order_integrity_ok"] is True for r in res.decision_logs)


def test_adapter_exception_records_error_and_continues(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    df, dup, ooo = load_and_prepare_input(csv_path)
    res = run_csv_replay_pipeline_dry_run(
        df=df,
        duplicate_timestamps=dup,
        out_of_order_timestamps=ooo,
        run_id="r_err",
        warmup_start=pd.Timestamp("2024-01-01T00:00:00Z"),
        replay_start=pd.Timestamp("2024-01-01T00:05:00Z"),
        replay_end=pd.Timestamp("2024-01-01T00:15:00Z"),
        expected_timeframe_minutes=5,
        adapter=_ErrorAdapter(),
    )
    assert len(res.decision_logs) == res.summary["replay_bar_count"]
    assert any(r["pipeline_adapter_status"] == "error" for r in res.decision_logs)
    assert res.summary["pipeline_adapter_error_count"] == 2
    assert any(e["event_type"] == "pipeline_adapter_error" for e in res.event_logs)


def test_no_real_order_integrity_counts_zero(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    df, dup, ooo = load_and_prepare_input(csv_path)
    res = run_csv_replay_pipeline_dry_run(
        df=df,
        duplicate_timestamps=dup,
        out_of_order_timestamps=ooo,
        run_id="r_integrity",
        warmup_start=pd.Timestamp("2024-01-01T00:00:00Z"),
        replay_start=pd.Timestamp("2024-01-01T00:05:00Z"),
        replay_end=pd.Timestamp("2024-01-01T00:15:00Z"),
        expected_timeframe_minutes=5,
        adapter=_OkAdapter(),
    )
    assert res.summary["real_order_sent_count"] == 0
    assert res.summary["no_real_order_integrity_violation_count"] == 0


def test_main_writes_all_output_files(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    out_dir = tmp_path / "out"
    old = sys.argv
    try:
        sys.argv = [
            "run_csv_replay_pipeline_dry_run.py",
            "--input-csv",
            str(csv_path),
            "--output-dir",
            str(out_dir),
            "--run-id",
            "r_main",
            "--warmup-start",
            "2024-01-01T00:00:00Z",
            "--replay-start",
            "2024-01-01T00:05:00Z",
            "--replay-end",
            "2024-01-01T00:15:00Z",
            "--expected-timeframe-minutes",
            "5",
        ]
        rc = main()
    finally:
        sys.argv = old
    assert rc == 0
    assert (out_dir / "near_live_decision_logs.csv").exists()
    assert (out_dir / "near_live_event_logs.csv").exists()
    assert (out_dir / "near_live_state_logs.csv").exists()
    assert (out_dir / "near_live_validation_warnings.csv").exists()
    assert (out_dir / "near_live_summary.csv").exists()
    assert (out_dir / "near_live_summary.md").exists()

    with (out_dir / "near_live_decision_logs.csv").open("r", encoding="utf-8", newline="") as f:
        decision_header = csv.DictReader(f).fieldnames or []
    assert "htf_filter_enabled" in decision_header
    assert "htf_timeframe_policy" in decision_header
    assert "htf_neutral_policy" in decision_header
    assert "htf_trend_dir" in decision_header
    assert "htf_bias" in decision_header
    assert "htf_direction_aligned" in decision_header
    assert "htf_filter_reason" in decision_header
    assert "htf_context_reason" in decision_header

    with (out_dir / "near_live_summary.csv").open("r", encoding="utf-8", newline="") as f:
        summary = list(csv.DictReader(f))[0]
    assert int(summary["decision_log_count"]) == int(summary["replay_bar_count"])
    assert "pipeline_adapter_called_count" in summary
    assert "pipeline_adapter_error_count" in summary
    assert "pipeline_adapter_skipped_count" in summary
    assert "entry_signal_true_count" in summary
    assert "trade_ok_true_count" in summary
    assert "paper_order_candidate_count" in summary
    assert "real_order_sent_count" in summary
    assert "no_real_order_integrity_violation_count" in summary
    assert "warning_count" in summary
    assert "duplicate_bar_count" in summary
    assert "data_gap_count" in summary
    assert "expected_weekend_gap_count" in summary
    assert "ordinary_missing_bar_gap_count" in summary
    assert "unknown_gap_count" in summary
