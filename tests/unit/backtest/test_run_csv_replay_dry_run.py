from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts.run_csv_replay_dry_run import load_and_prepare_input
from scripts.run_csv_replay_dry_run import main
from scripts.run_csv_replay_dry_run import parse_args
from scripts.run_csv_replay_dry_run import split_warmup_replay


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _base_rows() -> list[dict[str, object]]:
    return [
        {"timestamp": "2024-01-01 00:00:00", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5},
        {"timestamp": "2024-01-01 00:05:00", "open": 100.5, "high": 101.2, "low": 100.1, "close": 101.0},
        {"timestamp": "2024-01-01 00:10:00", "open": 101.0, "high": 101.5, "low": 100.8, "close": 101.3},
    ]


def test_parse_args() -> None:
    old = sys.argv
    try:
        sys.argv = [
            "run_csv_replay_dry_run.py",
            "--input-csv",
            "in.csv",
            "--output-dir",
            "out",
            "--run-id",
            "r1",
            "--warmup-start",
            "2024-01-01T00:00:00Z",
            "--replay-start",
            "2024-01-01T00:10:00Z",
            "--replay-end",
            "2024-01-01T01:00:00Z",
            "--expected-timeframe-minutes",
            "5",
        ]
        args = parse_args()
    finally:
        sys.argv = old
    assert args.run_id == "r1"
    assert args.expected_timeframe_minutes == 5


def test_timestamp_utc_normalization(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _base_rows())
    df, _, _ = load_and_prepare_input(csv_path)
    assert str(df["timestamp"].dtype) == "datetime64[ns, UTC]"


def test_split_warmup_replay() -> None:
    rows = _base_rows()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    warmup_start = pd.Timestamp("2024-01-01T00:00:00Z")
    replay_start = pd.Timestamp("2024-01-01T00:10:00Z")
    replay_end = pd.Timestamp("2024-01-01T00:20:00Z")
    warmup, replay = split_warmup_replay(df, warmup_start, replay_start, replay_end)
    assert len(warmup) == 2
    assert len(replay) == 1


def test_main_outputs_replay_only_decision_logs_and_summary(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _base_rows())
    out_dir = tmp_path / "out"
    old = sys.argv
    try:
        sys.argv = [
            "run_csv_replay_dry_run.py",
            "--input-csv",
            str(csv_path),
            "--output-dir",
            str(out_dir),
            "--run-id",
            "r2",
            "--warmup-start",
            "2024-01-01T00:00:00Z",
            "--replay-start",
            "2024-01-01T00:10:00Z",
            "--replay-end",
            "2024-01-01T00:20:00Z",
            "--expected-timeframe-minutes",
            "5",
        ]
        rc = main()
    finally:
        sys.argv = old
    assert rc == 0
    with (out_dir / "near_live_decision_logs.csv").open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["decision_reason"] != ""
    assert rows[0]["timestamp"].endswith("+00:00")
    assert rows[0]["paper_order_action"] == "none"
    assert (out_dir / "near_live_summary.csv").exists()
    assert (out_dir / "near_live_summary.md").exists()


def test_duplicate_gap_out_of_order_warnings(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars_warn.csv"
    rows = [
        {"timestamp": "2024-01-01 00:00:00", "open": 100, "high": 101, "low": 99, "close": 100.5},
        {"timestamp": "2024-01-01 00:05:00", "open": 100.5, "high": 101.1, "low": 100, "close": 100.7},
        {"timestamp": "2024-01-01 00:30:00", "open": 100.7, "high": 101.2, "low": 100.2, "close": 101.0},
        {"timestamp": "2024-01-01 00:15:00", "open": 101.0, "high": 101.3, "low": 100.6, "close": 100.9},
        {"timestamp": "2024-01-01 00:30:00", "open": 100.9, "high": 101.0, "low": 100.4, "close": 100.8},
    ]
    _write_csv(csv_path, rows)
    out_dir = tmp_path / "out_warn"
    old = sys.argv
    try:
        sys.argv = [
            "run_csv_replay_dry_run.py",
            "--input-csv",
            str(csv_path),
            "--output-dir",
            str(out_dir),
            "--run-id",
            "r_warn",
            "--warmup-start",
            "2024-01-01T00:00:00Z",
            "--replay-start",
            "2024-01-01T00:10:00Z",
            "--replay-end",
            "2024-01-01T00:40:00Z",
            "--expected-timeframe-minutes",
            "5",
        ]
        rc = main()
    finally:
        sys.argv = old
    assert rc == 0
    with (out_dir / "near_live_validation_warnings.csv").open("r", encoding="utf-8", newline="") as f:
        warn_rows = list(csv.DictReader(f))
    warning_types = {r["warning_type"] for r in warn_rows}
    assert "duplicate_timestamp" in warning_types
    assert "data_gap" in warning_types
    assert "out_of_order_timestamp" in warning_types
    data_gap_rows = [r for r in warn_rows if r["warning_type"] == "data_gap"]
    assert data_gap_rows
    assert data_gap_rows[0]["gap_class"] in {"ordinary_missing_bar_gap", "expected_weekend_gap", "unknown_gap"}


def test_weekend_gap_classification(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars_weekend_gap.csv"
    rows = [
        {"timestamp": "2024-01-05 16:55:00", "open": 100, "high": 101, "low": 99, "close": 100.5},
        {"timestamp": "2024-01-07 17:05:00", "open": 100.5, "high": 101.2, "low": 100.1, "close": 101.0},
    ]
    _write_csv(csv_path, rows)
    out_dir = tmp_path / "out_weekend_gap"
    old = sys.argv
    try:
        sys.argv = [
            "run_csv_replay_dry_run.py",
            "--input-csv",
            str(csv_path),
            "--output-dir",
            str(out_dir),
            "--run-id",
            "r_weekend",
            "--warmup-start",
            "2024-01-05T00:00:00Z",
            "--replay-start",
            "2024-01-05T00:00:00Z",
            "--replay-end",
            "2024-01-08T00:00:00Z",
            "--expected-timeframe-minutes",
            "5",
        ]
        rc = main()
    finally:
        sys.argv = old
    assert rc == 0
    with (out_dir / "near_live_validation_warnings.csv").open("r", encoding="utf-8", newline="") as f:
        warn_rows = list(csv.DictReader(f))
    gap = next(r for r in warn_rows if r["warning_type"] == "data_gap")
    assert gap["gap_class"] == "expected_weekend_gap"
    assert gap["expected_gap_flag"] == "True"
    assert gap["gap_requires_investigation"] == "False"


def test_ordinary_missing_bar_gap_classification(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars_ordinary_gap.csv"
    rows = [
        {"timestamp": "2024-01-03 00:00:00", "open": 100, "high": 101, "low": 99, "close": 100.5},
        {"timestamp": "2024-01-03 00:20:00", "open": 100.5, "high": 101.2, "low": 100.1, "close": 101.0},
    ]
    _write_csv(csv_path, rows)
    out_dir = tmp_path / "out_ordinary_gap"
    old = sys.argv
    try:
        sys.argv = [
            "run_csv_replay_dry_run.py",
            "--input-csv",
            str(csv_path),
            "--output-dir",
            str(out_dir),
            "--run-id",
            "r_ordinary",
            "--warmup-start",
            "2024-01-03T00:00:00Z",
            "--replay-start",
            "2024-01-03T00:00:00Z",
            "--replay-end",
            "2024-01-03T01:00:00Z",
            "--expected-timeframe-minutes",
            "5",
        ]
        rc = main()
    finally:
        sys.argv = old
    assert rc == 0
    with (out_dir / "near_live_validation_warnings.csv").open("r", encoding="utf-8", newline="") as f:
        warn_rows = list(csv.DictReader(f))
    gap = next(r for r in warn_rows if r["warning_type"] == "data_gap")
    assert gap["gap_class"] == "ordinary_missing_bar_gap"
    assert gap["expected_gap_flag"] == "False"
    assert gap["gap_requires_investigation"] == "True"


def test_missing_required_columns_raises_error(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing.csv"
    rows = [{"timestamp": "2024-01-01 00:00:00", "open": 100, "high": 101, "low": 99}]
    _write_csv(csv_path, rows)
    out_dir = tmp_path / "out"
    old = sys.argv
    try:
        sys.argv = [
            "run_csv_replay_dry_run.py",
            "--input-csv",
            str(csv_path),
            "--output-dir",
            str(out_dir),
            "--run-id",
            "r_err",
            "--warmup-start",
            "2024-01-01T00:00:00Z",
            "--replay-start",
            "2024-01-01T00:10:00Z",
            "--replay-end",
            "2024-01-01T00:20:00Z",
        ]
        with pytest.raises(ValueError, match="Missing required columns"):
            main()
    finally:
        sys.argv = old
