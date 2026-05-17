from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

from scripts.run_htf_diagnostic_comparison import main
from scripts.run_htf_diagnostic_comparison import _add_entry_set_diff_summary
from scripts.run_htf_diagnostic_comparison import _add_accepted_entry_set_diff_summary
from scripts.run_htf_diagnostic_comparison import _add_htf_rejected_entry_set_summary
from scripts.run_htf_diagnostic_comparison import _extract_entry_set
from scripts.run_htf_diagnostic_comparison import _extract_accepted_entry_set
from scripts.run_htf_diagnostic_comparison import _extract_htf_rejected_entry_set
from scripts.run_htf_diagnostic_comparison import run_htf_diagnostic_comparison


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


def test_run_htf_diagnostic_comparison_creates_three_condition_outputs(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    out_dir = tmp_path / "out"

    rows = run_htf_diagnostic_comparison(
        input_csv=csv_path,
        output_dir=out_dir,
        run_id="r_cmp",
        warmup_start=pd.Timestamp("2024-01-01T00:00:00Z"),
        replay_start=pd.Timestamp("2024-01-01T00:05:00Z"),
        replay_end=pd.Timestamp("2024-01-01T00:15:00Z"),
        expected_timeframe_minutes=5,
    )

    assert len(rows) == 3
    condition_names = {r["condition"] for r in rows}
    assert condition_names == {"htf_off", "htf_permissive", "htf_strict"}

    for name in condition_names:
        condition_dir = out_dir / name
        assert condition_dir.exists()
        assert (condition_dir / "near_live_decision_logs.csv").exists()
        assert (condition_dir / "near_live_summary.csv").exists()
        with (condition_dir / "near_live_summary.csv").open("r", encoding="utf-8", newline="") as f:
            summary = list(csv.DictReader(f))[0]
        assert summary["real_order_sent_count"] == "0"
        assert summary["no_real_order_integrity_violation_count"] == "0"

    assert (out_dir / "htf_diagnostic_comparison_summary.csv").exists()
    assert (out_dir / "htf_diagnostic_comparison_summary.md").exists()

    with (out_dir / "htf_diagnostic_comparison_summary.csv").open("r", encoding="utf-8", newline="") as f:
        summary_rows = list(csv.DictReader(f))
    assert len(summary_rows) == 3
    by_name = {r["condition"]: r for r in summary_rows}
    assert by_name["htf_off"]["htf_filter_enabled"] == "False"
    assert by_name["htf_permissive"]["htf_filter_enabled"] == "True"
    assert by_name["htf_strict"]["htf_filter_enabled"] == "True"
    assert by_name["htf_permissive"]["htf_neutral_policy"] == "permissive"
    assert by_name["htf_strict"]["htf_neutral_policy"] == "strict"
    assert all(r["replay_bar_count"] == r["decision_log_count"] for r in summary_rows)
    assert all(r["real_order_sent_count"] == "0" for r in summary_rows)
    assert all(r["no_real_order_integrity_violation_count"] == "0" for r in summary_rows)


def test_main_writes_outputs(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, _rows_with_warmup_and_replay())
    out_dir = tmp_path / "out_main"

    old = sys.argv
    try:
        sys.argv = [
            "run_htf_diagnostic_comparison.py",
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
    assert (out_dir / "htf_off" / "near_live_decision_logs.csv").exists()
    assert (out_dir / "htf_permissive" / "near_live_decision_logs.csv").exists()
    assert (out_dir / "htf_strict" / "near_live_decision_logs.csv").exists()
    assert (out_dir / "htf_diagnostic_comparison_summary.csv").exists()
    assert (out_dir / "htf_diagnostic_comparison_summary.md").exists()


def test_add_entry_set_diff_summary_uses_htf_off_as_baseline() -> None:
    summary_rows = [
        {"condition": "htf_off"},
        {"condition": "htf_permissive"},
        {"condition": "htf_strict"},
    ]
    entry_sets_by_condition = {
        "htf_off": {
            ("2024-01-01 00:05:00+00:00", "long_entry"),
            ("2024-01-01 00:10:00+00:00", "short_entry"),
        },
        "htf_permissive": {
            ("2024-01-01 00:10:00+00:00", "short_entry"),
            ("2024-01-01 00:15:00+00:00", "long_entry"),
        },
        "htf_strict": {
            ("2024-01-01 00:10:00+00:00", "short_entry"),
        },
    }

    _add_entry_set_diff_summary(summary_rows, entry_sets_by_condition)
    by_name = {r["condition"]: r for r in summary_rows}

    assert by_name["htf_off"]["entry_set_count"] == 2
    assert by_name["htf_off"]["entry_set_only_in_htf_off_count"] == 0
    assert by_name["htf_off"]["entry_set_only_in_condition_count"] == 0
    assert by_name["htf_off"]["entry_set_intersection_count"] == 2
    assert by_name["htf_off"]["entry_set_removed_vs_htf_off_count"] == 0
    assert by_name["htf_off"]["entry_set_added_vs_htf_off_count"] == 0

    assert by_name["htf_permissive"]["entry_set_count"] == 2
    assert by_name["htf_permissive"]["entry_set_only_in_htf_off_count"] == 1
    assert by_name["htf_permissive"]["entry_set_only_in_condition_count"] == 1
    assert by_name["htf_permissive"]["entry_set_intersection_count"] == 1
    assert by_name["htf_permissive"]["entry_set_removed_vs_htf_off_count"] == 1
    assert by_name["htf_permissive"]["entry_set_added_vs_htf_off_count"] == 1

    assert by_name["htf_strict"]["entry_set_count"] == 1
    assert by_name["htf_strict"]["entry_set_only_in_htf_off_count"] == 1
    assert by_name["htf_strict"]["entry_set_only_in_condition_count"] == 0
    assert by_name["htf_strict"]["entry_set_intersection_count"] == 1
    assert by_name["htf_strict"]["entry_set_removed_vs_htf_off_count"] == 1
    assert by_name["htf_strict"]["entry_set_added_vs_htf_off_count"] == 0


def test_candidate_accepted_and_rejected_sets_are_summarized_separately() -> None:
    htf_off_logs = [
        {"timestamp": "2024-01-01 00:05:00+00:00", "signal_type": "long_entry", "entry_signal": True, "trade_ok": True, "htf_filter_enabled": False, "htf_direction_aligned": True},
        {"timestamp": "2024-01-01 00:10:00+00:00", "signal_type": "short_entry", "entry_signal": True, "trade_ok": True, "htf_filter_enabled": False, "htf_direction_aligned": True},
    ]
    htf_permissive_logs = [
        {"timestamp": "2024-01-01 00:05:00+00:00", "signal_type": "long_entry", "entry_signal": True, "trade_ok": True, "htf_filter_enabled": True, "htf_direction_aligned": True},
        {"timestamp": "2024-01-01 00:10:00+00:00", "signal_type": "short_entry", "entry_signal": True, "trade_ok": False, "htf_filter_enabled": True, "htf_direction_aligned": False},
    ]
    htf_strict_logs = [
        {"timestamp": "2024-01-01 00:05:00+00:00", "signal_type": "long_entry", "entry_signal": True, "trade_ok": False, "htf_filter_enabled": True, "htf_direction_aligned": False},
        {"timestamp": "2024-01-01 00:10:00+00:00", "signal_type": "short_entry", "entry_signal": True, "trade_ok": True, "htf_filter_enabled": True, "htf_direction_aligned": True},
    ]

    summary_rows = [
        {"condition": "htf_off"},
        {"condition": "htf_permissive"},
        {"condition": "htf_strict"},
    ]
    candidate_sets = {
        "htf_off": _extract_entry_set(htf_off_logs),
        "htf_permissive": _extract_entry_set(htf_permissive_logs),
        "htf_strict": _extract_entry_set(htf_strict_logs),
    }
    accepted_sets = {
        "htf_off": _extract_accepted_entry_set(htf_off_logs),
        "htf_permissive": _extract_accepted_entry_set(htf_permissive_logs),
        "htf_strict": _extract_accepted_entry_set(htf_strict_logs),
    }
    rejected_sets = {
        "htf_off": _extract_htf_rejected_entry_set(htf_off_logs),
        "htf_permissive": _extract_htf_rejected_entry_set(htf_permissive_logs),
        "htf_strict": _extract_htf_rejected_entry_set(htf_strict_logs),
    }

    _add_entry_set_diff_summary(summary_rows, candidate_sets)
    _add_accepted_entry_set_diff_summary(summary_rows, accepted_sets)
    _add_htf_rejected_entry_set_summary(summary_rows, rejected_sets)
    by_name = {r["condition"]: r for r in summary_rows}

    assert by_name["htf_off"]["entry_set_count"] == 2
    assert by_name["htf_permissive"]["entry_set_count"] == 2
    assert by_name["htf_strict"]["entry_set_count"] == 2
    assert by_name["htf_permissive"]["entry_set_removed_vs_htf_off_count"] == 0
    assert by_name["htf_strict"]["entry_set_removed_vs_htf_off_count"] == 0

    assert by_name["htf_off"]["accepted_entry_set_count"] == 2
    assert by_name["htf_permissive"]["accepted_entry_set_count"] == 1
    assert by_name["htf_strict"]["accepted_entry_set_count"] == 1
    assert by_name["htf_permissive"]["accepted_entry_set_removed_vs_htf_off_count"] == 1
    assert by_name["htf_strict"]["accepted_entry_set_removed_vs_htf_off_count"] == 1
    assert by_name["htf_permissive"]["accepted_entry_set_intersection_count"] == 1
    assert by_name["htf_strict"]["accepted_entry_set_intersection_count"] == 1

    assert by_name["htf_off"]["htf_rejected_entry_set_count"] == 0
    assert by_name["htf_permissive"]["htf_rejected_entry_set_count"] == 1
    assert by_name["htf_strict"]["htf_rejected_entry_set_count"] == 1
    assert by_name["htf_permissive"]["htf_rejected_entry_set_vs_htf_off_added_count"] == 1
    assert by_name["htf_strict"]["htf_rejected_entry_set_vs_htf_off_added_count"] == 1
