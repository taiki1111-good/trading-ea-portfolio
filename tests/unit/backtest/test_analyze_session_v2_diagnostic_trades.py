from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from scripts.analyze_session_v2_diagnostic_trades import build_group_summary
from scripts.analyze_session_v2_diagnostic_trades import load_and_join
from scripts.analyze_session_v2_diagnostic_trades import run_analysis


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _decision_fields() -> list[str]:
    return [
        "timestamp",
        "session_v2_enabled",
        "session_policy",
        "hour_utc",
        "day_of_week",
        "session_label",
        "is_tokyo_session",
        "is_london_session",
        "is_new_york_session",
        "is_london_ny_overlap",
        "is_low_liquidity_hour",
        "session_risk_flag",
        "session_reason",
        "session_data_valid_flag",
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
                "session_v2_enabled": "True",
                "session_policy": "diagnostic_only",
                "hour_utc": "0",
                "day_of_week": "friday",
                "session_label": "tokyo",
                "is_tokyo_session": "True",
                "is_london_session": "False",
                "is_new_york_session": "False",
                "is_london_ny_overlap": "False",
                "is_low_liquidity_hour": "False",
                "session_risk_flag": "False",
                "session_reason": "diagnostic_only:no_entry_filter",
                "session_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "1.2"}])
    joined, unmatched = load_and_join(d, t)
    assert unmatched == 0
    assert joined.iloc[0]["session_label"] == "tokyo"


def test_join_handles_timezone_format_differences(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T13:00:00Z",
                "session_v2_enabled": "True",
                "session_policy": "diagnostic_only",
                "hour_utc": "13",
                "day_of_week": "friday",
                "session_label": "london_ny_overlap",
                "is_tokyo_session": "False",
                "is_london_session": "True",
                "is_new_york_session": "True",
                "is_london_ny_overlap": "True",
                "is_low_liquidity_hour": "False",
                "session_risk_flag": "False",
                "session_reason": "diagnostic_only:no_entry_filter",
                "session_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T13:00:00+00:00", "direction": "long", "pnl": "-0.3"}])
    joined, unmatched = load_and_join(d, t)
    assert unmatched == 0
    assert joined.iloc[0]["session_label"] == "london_ny_overlap"


def test_session_columns_attached_to_trade_analysis(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    out = tmp_path / "out"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T22:00:00+00:00",
                "session_v2_enabled": "True",
                "session_policy": "diagnostic_only",
                "hour_utc": "22",
                "day_of_week": "friday",
                "session_label": "low_liquidity",
                "is_tokyo_session": "False",
                "is_london_session": "False",
                "is_new_york_session": "False",
                "is_london_ny_overlap": "False",
                "is_low_liquidity_hour": "True",
                "session_risk_flag": "True",
                "session_reason": "diagnostic_only:no_entry_filter",
                "session_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T22:00:00+00:00", "direction": "short", "pnl": "0.5"}])
    trade_csv, _, _, _ = run_analysis(d, t, out)
    row = pd.read_csv(trade_csv).iloc[0]
    assert row["session_policy"] == "diagnostic_only"
    assert row["session_label"] == "low_liquidity"
    assert bool(row["session_risk_flag"]) is True


def test_group_summary_metrics_are_correct() -> None:
    df = pd.DataFrame(
        [
            {
                "pnl": 1.0,
                "session_label": "tokyo",
                "hour_utc": 0,
                "day_of_week": "friday",
                "session_risk_flag": False,
                "is_low_liquidity_hour": False,
                "is_tokyo_session": True,
                "is_london_session": False,
                "is_new_york_session": False,
                "is_london_ny_overlap": False,
                "session_policy": "diagnostic_only",
            },
            {
                "pnl": -0.5,
                "session_label": "tokyo",
                "hour_utc": 0,
                "day_of_week": "friday",
                "session_risk_flag": False,
                "is_low_liquidity_hour": False,
                "is_tokyo_session": True,
                "is_london_session": False,
                "is_new_york_session": False,
                "is_london_ny_overlap": False,
                "session_policy": "diagnostic_only",
            },
        ]
    )
    out, invalid_hour_count = build_group_summary(df)
    assert invalid_hour_count == 0
    row = out[(out["group_name"] == "session_label") & (out["group_value"] == "tokyo")].iloc[0]
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
                "session_v2_enabled": "True",
                "session_policy": "diagnostic_only",
                "hour_utc": "0",
                "day_of_week": "friday",
                "session_label": "tokyo",
                "is_tokyo_session": "True",
                "is_london_session": "False",
                "is_new_york_session": "False",
                "is_london_ny_overlap": "False",
                "is_low_liquidity_hour": "False",
                "session_risk_flag": "False",
                "session_reason": "diagnostic_only:no_entry_filter",
                "session_data_valid_flag": "True",
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
    assert "unmatched trades" in md.read_text(encoding="utf-8")


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
                "timestamp": "2024-11-01T13:00:00+00:00",
                "session_v2_enabled": "True",
                "session_policy": "diagnostic_only",
                "hour_utc": "13",
                "day_of_week": "friday",
                "session_label": "london_ny_overlap",
                "is_tokyo_session": "False",
                "is_london_session": "True",
                "is_new_york_session": "True",
                "is_london_ny_overlap": "True",
                "is_low_liquidity_hour": "False",
                "session_risk_flag": "False",
                "session_reason": "diagnostic_only:no_entry_filter",
                "session_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T13:00:00+00:00", "direction": "long", "pnl": "0.1"}])
    trade_csv, group_csv, group_md, _ = run_analysis(d, t, out_dir)
    assert trade_csv.exists()
    assert group_csv.exists()
    assert group_md.exists()
    md_text = group_md.read_text(encoding="utf-8")
    assert "Session v2はentryを止めていない" in md_text
    assert "DST厳密補正なし" in md_text


def test_groupings_session_hour_day_risk_are_correct() -> None:
    df = pd.DataFrame(
        [
            {
                "pnl": 1.0,
                "session_label": "tokyo",
                "hour_utc": 0,
                "day_of_week": "monday",
                "session_risk_flag": False,
                "is_low_liquidity_hour": False,
                "is_tokyo_session": True,
                "is_london_session": False,
                "is_new_york_session": False,
                "is_london_ny_overlap": False,
                "session_policy": "diagnostic_only",
            },
            {
                "pnl": -0.2,
                "session_label": "low_liquidity",
                "hour_utc": 22,
                "day_of_week": "monday",
                "session_risk_flag": True,
                "is_low_liquidity_hour": True,
                "is_tokyo_session": False,
                "is_london_session": False,
                "is_new_york_session": False,
                "is_london_ny_overlap": False,
                "session_policy": "diagnostic_only",
            },
        ]
    )
    out, invalid_hour_count = build_group_summary(df)
    assert invalid_hour_count == 0
    row_session = out[(out["group_name"] == "session_label") & (out["group_value"] == "tokyo")].iloc[0]
    row_hour = out[(out["group_name"] == "hour_utc") & (out["group_value"] == "22")].iloc[0]
    row_day = out[(out["group_name"] == "day_of_week") & (out["group_value"] == "monday")].iloc[0]
    row_risk = out[(out["group_name"] == "session_risk_flag") & (out["group_value"] == "true")].iloc[0]
    assert int(row_session["trade_count"]) == 1
    assert int(row_hour["trade_count"]) == 1
    assert int(row_day["trade_count"]) == 2
    assert int(row_risk["trade_count"]) == 1


def test_hour_utc_group_values_are_numeric_only_when_valid() -> None:
    df = pd.DataFrame(
        [
            {
                "pnl": 0.1,
                "session_label": "tokyo",
                "hour_utc": 0,
                "day_of_week": "monday",
                "session_risk_flag": False,
                "is_low_liquidity_hour": False,
                "is_tokyo_session": True,
                "is_london_session": False,
                "is_new_york_session": False,
                "is_london_ny_overlap": False,
                "session_policy": "diagnostic_only",
            },
            {
                "pnl": 0.2,
                "session_label": "london",
                "hour_utc": 23,
                "day_of_week": "tuesday",
                "session_risk_flag": False,
                "is_low_liquidity_hour": False,
                "is_tokyo_session": False,
                "is_london_session": True,
                "is_new_york_session": False,
                "is_london_ny_overlap": False,
                "session_policy": "diagnostic_only",
            },
        ]
    )
    out, invalid_hour_count = build_group_summary(df)
    assert invalid_hour_count == 0
    hour_values = set(out.loc[out["group_name"] == "hour_utc", "group_value"].tolist())
    assert hour_values == {"0", "23"}


def test_bool_grouping_does_not_leak_into_hour_utc_group() -> None:
    df = pd.DataFrame(
        [
            {
                "pnl": 0.1,
                "session_label": "tokyo",
                "hour_utc": "0",
                "day_of_week": "monday",
                "session_risk_flag": "true",
                "is_low_liquidity_hour": "false",
                "is_tokyo_session": "true",
                "is_london_session": "false",
                "is_new_york_session": "false",
                "is_london_ny_overlap": "false",
                "session_policy": "diagnostic_only",
            },
            {
                "pnl": -0.1,
                "session_label": "low_liquidity",
                "hour_utc": "1",
                "day_of_week": "monday",
                "session_risk_flag": "false",
                "is_low_liquidity_hour": "true",
                "is_tokyo_session": "false",
                "is_london_session": "false",
                "is_new_york_session": "false",
                "is_london_ny_overlap": "false",
                "session_policy": "diagnostic_only",
            },
        ]
    )
    out, _ = build_group_summary(df)
    hour_values = set(out.loc[out["group_name"] == "hour_utc", "group_value"].tolist())
    assert "true" not in hour_values
    assert "false" not in hour_values


def test_invalid_hour_utc_is_warned_and_mapped_to_unknown(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T25:00:00+00:00",
                "session_v2_enabled": "True",
                "session_policy": "diagnostic_only",
                "hour_utc": "25",
                "day_of_week": "friday",
                "session_label": "unknown",
                "is_tokyo_session": "False",
                "is_london_session": "False",
                "is_new_york_session": "False",
                "is_london_ny_overlap": "False",
                "is_low_liquidity_hour": "False",
                "session_risk_flag": "False",
                "session_reason": "diagnostic_only:no_entry_filter",
                "session_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T01:00:00+00:00", "direction": "long", "pnl": "0.1"}])
    # force match with valid timestamp while keeping invalid hour_utc payload
    ddf = pd.read_csv(d)
    ddf.loc[0, "timestamp"] = "2024-11-01T01:00:00+00:00"
    ddf.to_csv(d, index=False)

    _, group_csv, group_md, _ = run_analysis(d, t, out_dir)
    gdf = pd.read_csv(group_csv)
    row = gdf[(gdf["group_name"] == "hour_utc") & (gdf["group_value"] == "unknown")]
    assert len(row) == 1
    md_text = group_md.read_text(encoding="utf-8")
    assert "invalid hour_utc values detected and mapped to unknown" in md_text


def test_markdown_and_csv_group_name_group_value_alignment(tmp_path: Path) -> None:
    d = tmp_path / "decision.csv"
    t = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(
        d,
        _decision_fields(),
        [
            {
                "timestamp": "2024-11-01T00:00:00+00:00",
                "session_v2_enabled": "True",
                "session_policy": "diagnostic_only",
                "hour_utc": "0",
                "day_of_week": "friday",
                "session_label": "tokyo",
                "is_tokyo_session": "True",
                "is_london_session": "False",
                "is_new_york_session": "False",
                "is_london_ny_overlap": "False",
                "is_low_liquidity_hour": "False",
                "session_risk_flag": "False",
                "session_reason": "diagnostic_only:no_entry_filter",
                "session_data_valid_flag": "True",
            }
        ],
    )
    _write_csv(t, ["entry_time", "direction", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "direction": "long", "pnl": "0.1"}])
    _, group_csv, group_md, _ = run_analysis(d, t, out_dir)
    gdf = pd.read_csv(group_csv)
    hour_row = gdf[(gdf["group_name"] == "hour_utc") & (gdf["group_value"] == "0")]
    assert len(hour_row) == 1
    md_text = group_md.read_text(encoding="utf-8")
    assert "| hour_utc | 0 |" in md_text
