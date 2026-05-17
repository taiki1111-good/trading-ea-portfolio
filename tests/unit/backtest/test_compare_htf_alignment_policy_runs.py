from __future__ import annotations

import csv
from pathlib import Path

from scripts.compare_htf_alignment_policy_runs import compare_pair
from scripts.compare_htf_alignment_policy_runs import neutral_counts


def test_neutral_passed_count_with_permissive_neutral_aligned_true() -> None:
    rows = [
        {
            "htf_filter_enabled": "True",
            "htf_bias": "neutral",
            "htf_neutral_policy": "permissive",
            "htf_direction_aligned": "True",
            "entry_signal": "True",
            "trade_ok": "True",
        }
    ]
    passed, rejected = neutral_counts(rows)
    assert passed == 1
    assert rejected == 0


def test_neutral_rejected_count_with_strict_neutral_aligned_false() -> None:
    rows = [
        {
            "htf_filter_enabled": "True",
            "htf_bias": "neutral",
            "htf_neutral_policy": "strict",
            "htf_direction_aligned": "False",
            "entry_signal": "False",
            "trade_ok": "False",
            "fail_stage": "direction_alignment",
            "decision_reason": "blocked_by_htf",
            "htf_filter_reason": "neutral strict rejected",
        }
    ]
    passed, rejected = neutral_counts(rows)
    assert passed == 0
    assert rejected == 1


def test_non_neutral_rows_are_not_counted() -> None:
    rows = [
        {
            "htf_filter_enabled": "True",
            "htf_bias": "up",
            "htf_neutral_policy": "permissive",
            "htf_direction_aligned": "True",
            "entry_signal": "True",
            "trade_ok": "True",
        },
        {
            "htf_filter_enabled": "True",
            "htf_bias": "down",
            "htf_neutral_policy": "strict",
            "htf_direction_aligned": "False",
            "fail_stage": "direction_alignment",
            "decision_reason": "blocked_by_htf",
            "htf_filter_reason": "rejected",
        },
    ]
    passed, rejected = neutral_counts(rows)
    assert passed == 0
    assert rejected == 0


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def test_compare_pair_entry_set_diff_and_shifted_5min_not_broken(tmp_path: Path) -> None:
    base = tmp_path / "base"
    comp = tmp_path / "comp"
    base.mkdir()
    comp.mkdir()

    _write_csv(
        base / "backtest_summary.csv",
        ["run_id"],
        [{"run_id": "base_run"}],
    )
    _write_csv(
        comp / "backtest_summary.csv",
        ["run_id"],
        [{"run_id": "comp_run"}],
    )

    trade_fields = ["direction", "entry_time", "pnl"]
    _write_csv(
        base / "trade_logs.csv",
        trade_fields,
        [
            {"direction": "long", "entry_time": "2024-04-01T00:05:00+00:00", "pnl": "1.0"},
            {"direction": "short", "entry_time": "2024-04-01T00:20:00+00:00", "pnl": "-0.5"},
        ],
    )
    _write_csv(
        comp / "trade_logs.csv",
        trade_fields,
        [
            {"direction": "long", "entry_time": "2024-04-01T00:00:00+00:00", "pnl": "1.1"},
            {"direction": "short", "entry_time": "2024-04-01T00:20:00+00:00", "pnl": "-0.4"},
        ],
    )

    decision_fields = [
        "htf_filter_enabled",
        "htf_bias",
        "htf_neutral_policy",
        "htf_direction_aligned",
        "entry_signal",
        "trade_ok",
        "fail_stage",
        "decision_reason",
        "htf_filter_reason",
    ]
    _write_csv(
        comp / "decision_logs.csv",
        decision_fields,
        [
            {
                "htf_filter_enabled": "True",
                "htf_bias": "neutral",
                "htf_neutral_policy": "permissive",
                "htf_direction_aligned": "True",
                "entry_signal": "True",
                "trade_ok": "True",
                "fail_stage": "",
                "decision_reason": "",
                "htf_filter_reason": "",
            }
        ],
    )

    row = compare_pair(base, comp)
    assert row["base_trade_count"] == 2
    assert row["compare_trade_count"] == 2
    assert row["common_count"] == 1
    assert row["compare_only_count"] == 1
    assert row["base_only_count"] == 1
    assert row["shifted_5min_count"] == 1
    assert row["neutral_passed_count"] == 1
