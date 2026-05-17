from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from scripts.analyze_sr_v2_diagnostic_trades import build_group_summary
from scripts.analyze_sr_v2_diagnostic_trades import load_and_join
from scripts.analyze_sr_v2_diagnostic_trades import run_analysis


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _decision_fields() -> list[str]:
    return [
        "timestamp",
        "sr_v2_enabled",
        "sr_policy",
        "sr_window_bars",
        "nearest_resistance",
        "nearest_support",
        "nearest_resistance_distance_pips",
        "nearest_support_distance_pips",
        "sr_proximity_flag",
        "sr_block_side",
        "sr_reason",
        "sr_data_valid_flag",
        "sr_counterfactual_group",
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
                "sr_v2_enabled": "True",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": "48",
                "nearest_resistance": "154.2",
                "nearest_support": "153.7",
                "nearest_resistance_distance_pips": "6.0",
                "nearest_support_distance_pips": "44.0",
                "sr_proximity_flag": "True",
                "sr_block_side": "resistance",
                "sr_reason": "diagnostic_only:no_entry_filter",
                "sr_data_valid_flag": "True",
                "sr_counterfactual_group": "sr_long_near_resistance",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "1.2"}])
    joined, unmatched = load_and_join(d, t)
    assert unmatched == 0
    assert joined.iloc[0]["sr_block_side"] == "resistance"


def test_join_handles_timezone_format_differences(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00Z",
                "sr_v2_enabled": "True",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": "48",
                "nearest_resistance": "154.2",
                "nearest_support": "153.7",
                "nearest_resistance_distance_pips": "6.0",
                "nearest_support_distance_pips": "44.0",
                "sr_proximity_flag": "False",
                "sr_block_side": "none",
                "sr_reason": "diagnostic_only:no_entry_filter",
                "sr_data_valid_flag": "True",
                "sr_counterfactual_group": "sr_long_not_near_resistance",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "-0.3"}])
    joined, unmatched = load_and_join(d, t)
    assert unmatched == 0
    assert bool(joined.iloc[0]["sr_proximity_flag"]) is False


def test_sr_columns_attached_to_trade_analysis(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00+00:00",
                "sr_v2_enabled": "True",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": "48",
                "nearest_resistance": "154.2",
                "nearest_support": "153.7",
                "nearest_resistance_distance_pips": "6.0",
                "nearest_support_distance_pips": "44.0",
                "sr_proximity_flag": "True",
                "sr_block_side": "resistance",
                "sr_reason": "diagnostic_only:no_entry_filter",
                "sr_data_valid_flag": "True",
                "sr_counterfactual_group": "sr_long_near_resistance",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "0.5"}])
    out = tmp_path / "out"
    trade_csv, _, _, _ = run_analysis(d, t, out)
    row = pd.read_csv(trade_csv).iloc[0]
    assert row["sr_policy"] == "diagnostic_only"
    assert str(row["sr_block_side"]) == "resistance"


def test_group_summary_metrics_are_correct() -> None:
    df = pd.DataFrame(
        [
            {
                "pnl": 1.0,
                "sr_proximity_flag": True,
                "sr_block_side": "resistance",
                "sr_data_valid_flag": True,
                "sr_counterfactual_group": "sr_long_near_resistance",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": 48,
            },
            {
                "pnl": -0.5,
                "sr_proximity_flag": True,
                "sr_block_side": "resistance",
                "sr_data_valid_flag": True,
                "sr_counterfactual_group": "sr_long_near_resistance",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": 48,
            },
        ]
    )
    out = build_group_summary(df)
    row = out[(out["group_name"] == "sr_proximity_flag") & (out["group_value"] == "true")].iloc[0]
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
                "sr_v2_enabled": "True",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": "48",
                "nearest_resistance": "154.2",
                "nearest_support": "153.7",
                "nearest_resistance_distance_pips": "6.0",
                "nearest_support_distance_pips": "44.0",
                "sr_proximity_flag": "False",
                "sr_block_side": "none",
                "sr_reason": "diagnostic_only:no_entry_filter",
                "sr_data_valid_flag": "True",
                "sr_counterfactual_group": "sr_long_not_near_resistance",
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


def test_outputs_are_generated_and_markdown_has_disclaimer(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00+00:00",
                "sr_v2_enabled": "True",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": "48",
                "nearest_resistance": "154.2",
                "nearest_support": "153.7",
                "nearest_resistance_distance_pips": "6.0",
                "nearest_support_distance_pips": "44.0",
                "sr_proximity_flag": "False",
                "sr_block_side": "none",
                "sr_reason": "diagnostic_only:no_entry_filter",
                "sr_data_valid_flag": "True",
                "sr_counterfactual_group": "sr_long_not_near_resistance",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "0.1"}])
    trade_csv, group_csv, group_md, _ = run_analysis(d, t, out_dir)
    assert trade_csv.exists()
    assert group_csv.exists()
    assert group_md.exists()
    md_text = group_md.read_text(encoding="utf-8")
    assert "SR v2はentryを止めていない" in md_text


def test_sr_proximity_and_block_side_grouping_values_are_correct() -> None:
    df = pd.DataFrame(
        [
            {
                "pnl": 1.0,
                "sr_proximity_flag": True,
                "sr_block_side": "resistance",
                "sr_data_valid_flag": True,
                "sr_counterfactual_group": "sr_long_near_resistance",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": 48,
            },
            {
                "pnl": -0.2,
                "sr_proximity_flag": False,
                "sr_block_side": "none",
                "sr_data_valid_flag": True,
                "sr_counterfactual_group": "sr_long_not_near_resistance",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": 48,
            },
            {
                "pnl": 0.4,
                "sr_proximity_flag": True,
                "sr_block_side": "support",
                "sr_data_valid_flag": True,
                "sr_counterfactual_group": "sr_short_near_support",
                "sr_policy": "diagnostic_only",
                "sr_window_bars": 48,
            },
        ]
    )
    out = build_group_summary(df)
    row_true = out[(out["group_name"] == "sr_proximity_flag") & (out["group_value"] == "true")].iloc[0]
    assert int(row_true["trade_count"]) == 2
    assert float(row_true["total_pnl"]) == pytest.approx(1.4)

    row_res = out[(out["group_name"] == "sr_block_side") & (out["group_value"] == "resistance")].iloc[0]
    row_sup = out[(out["group_name"] == "sr_block_side") & (out["group_value"] == "support")].iloc[0]
    row_none = out[(out["group_name"] == "sr_block_side") & (out["group_value"] == "none")].iloc[0]
    assert int(row_res["trade_count"]) == 1
    assert int(row_sup["trade_count"]) == 1
    assert int(row_none["trade_count"]) == 1
