from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from scripts.analyze_htf_v2_diagnostic_trades import build_group_summary
from scripts.analyze_htf_v2_diagnostic_trades import load_and_join
from scripts.analyze_htf_v2_diagnostic_trades import run_analysis


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _decision_fields() -> list[str]:
    return [
        "timestamp",
        "htf_v2_candidate_direction",
        "h4_bias",
        "h1_context",
        "htf_v2_aligned_only_allowed",
        "htf_v2_pullback_permissive_allowed",
        "htf_v2_context_uncertain_flag",
        "htf_v2_hard_conflict_flag",
        "htf_v2_data_valid_flag",
    ]


def test_join_by_entry_time_and_timestamp(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00+00:00",
                "htf_v2_candidate_direction": "long",
                "h4_bias": "up",
                "h1_context": "aligned_up",
                "htf_v2_aligned_only_allowed": "True",
                "htf_v2_pullback_permissive_allowed": "True",
                "htf_v2_context_uncertain_flag": "False",
                "htf_v2_hard_conflict_flag": "False",
                "htf_v2_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "1.2"}])
    joined, unmatched = load_and_join(d, t)
    assert unmatched == 0
    assert joined.iloc[0]["h4_bias"] == "up"


def test_join_handles_timezone_format_differences(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00Z",
                "htf_v2_candidate_direction": "short",
                "h4_bias": "down",
                "h1_context": "aligned_down",
                "htf_v2_aligned_only_allowed": "True",
                "htf_v2_pullback_permissive_allowed": "True",
                "htf_v2_context_uncertain_flag": "False",
                "htf_v2_hard_conflict_flag": "False",
                "htf_v2_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "short", "pnl": "-0.3"}])
    joined, unmatched = load_and_join(d, t)
    assert unmatched == 0
    assert joined.iloc[0]["htf_v2_candidate_direction"] == "short"


def test_group_summary_metrics_are_correct() -> None:
    df = pd.DataFrame(
        [
            {
                "pnl": 1.0,
                "h4_bias": "up",
                "h1_context": "aligned_up",
                "htf_v2_aligned_only_allowed": True,
                "htf_v2_pullback_permissive_allowed": True,
                "htf_v2_context_uncertain_flag": False,
                "htf_v2_hard_conflict_flag": False,
                "htf_v2_data_valid_flag": True,
                "htf_v2_candidate_direction": "long",
            },
            {
                "pnl": -0.5,
                "h4_bias": "up",
                "h1_context": "aligned_up",
                "htf_v2_aligned_only_allowed": True,
                "htf_v2_pullback_permissive_allowed": True,
                "htf_v2_context_uncertain_flag": False,
                "htf_v2_hard_conflict_flag": False,
                "htf_v2_data_valid_flag": True,
                "htf_v2_candidate_direction": "long",
            },
        ]
    )
    out = build_group_summary(df)
    row = out[(out["group_name"] == "h4_bias") & (out["group_value"] == "up")].iloc[0]
    assert int(row["trade_count"]) == 2
    assert float(row["total_pnl"]) == pytest.approx(0.5)
    assert float(row["average_pnl"]) == pytest.approx(0.25)
    assert float(row["win_rate"]) == pytest.approx(0.5)


def test_unmatched_trade_is_reported_in_markdown(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00+00:00",
                "htf_v2_candidate_direction": "long",
                "h4_bias": "up",
                "h1_context": "aligned_up",
                "htf_v2_aligned_only_allowed": "True",
                "htf_v2_pullback_permissive_allowed": "True",
                "htf_v2_context_uncertain_flag": "False",
                "htf_v2_hard_conflict_flag": "False",
                "htf_v2_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(
        t,
        ["entry_time", "direction", "pnl"],
        [
            {"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "1"},
            {"entry_time": "2024-11-01T00:05:00+00:00", "direction": "short", "pnl": "-1"},
        ],
    )
    _, _, md, unmatched = run_analysis(d, t, out_dir)
    assert unmatched == 1
    text = md.read_text(encoding="utf-8")
    assert "unmatched trades" in text


def test_missing_required_columns_raise_error(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    _write_csv(d, ["timestamp"], [{"timestamp": "2024-01-01T00:00:00+00:00"}])
    _write_csv(t, ["entry_time", "pnl"], [{"entry_time": "2024-01-01T00:00:00+00:00", "pnl": "1"}])
    with pytest.raises(ValueError, match="missing required columns"):
        load_and_join(d, t)


def test_outputs_are_generated(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00+00:00",
                "htf_v2_candidate_direction": "long",
                "h4_bias": "neutral",
                "h1_context": "range_or_neutral",
                "htf_v2_aligned_only_allowed": "False",
                "htf_v2_pullback_permissive_allowed": "False",
                "htf_v2_context_uncertain_flag": "True",
                "htf_v2_hard_conflict_flag": "False",
                "htf_v2_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "0.1"}])
    trade_csv, group_csv, group_md, _ = run_analysis(d, t, out_dir)
    assert trade_csv.exists()
    assert group_csv.exists()
    assert group_md.exists()
    md_text = group_md.read_text(encoding="utf-8")
    assert "HTF v2はentryを止めていない" in md_text

