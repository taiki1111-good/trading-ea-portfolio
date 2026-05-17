from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from scripts.build_validation_v0_2_summary import build_summary


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _write_targets(path: Path, rows: list[dict[str, str]]) -> None:
    _write_csv(
        path,
        [
            "validation_target_id",
            "period_start",
            "period_end",
            "period_type",
            "run_id",
            "run_dir",
            "module_name",
            "candidate_name",
            "policy",
            "notes",
        ],
        rows,
    )


def test_targets_csv_can_be_read_and_outputs_are_generated(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_a"
    _write_csv(
        run_dir / "backtest_summary.csv",
        ["trade_count", "total_pnl", "average_pnl", "win_rate"],
        [{"trade_count": "64", "total_pnl": "0.29", "average_pnl": "0.0045", "win_rate": "0.8"}],
    )
    targets = tmp_path / "targets.csv"
    _write_targets(
        targets,
        [
            {
                "validation_target_id": "t1",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": "r1",
                "run_dir": str(run_dir),
                "module_name": "htf_v2",
                "candidate_name": "h4_h1_context",
                "policy": "diagnostic_only",
                "notes": "",
            }
        ],
    )
    out_dir = tmp_path / "out"
    summary_csv, decision_csv, layer_csv, md = build_summary(targets, out_dir, "vrid")
    assert summary_csv.exists()
    assert decision_csv.exists()
    assert layer_csv.exists()
    assert md.exists()


def test_metrics_are_loaded_from_backtest_summary(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_a"
    _write_csv(
        run_dir / "backtest_summary.csv",
        ["trade_count", "total_pnl", "average_pnl", "win_rate"],
        [{"trade_count": "64", "total_pnl": "1.2", "average_pnl": "0.01875", "win_rate": "0.75"}],
    )
    targets = tmp_path / "targets.csv"
    _write_targets(
        targets,
        [
            {
                "validation_target_id": "t1",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": "r1",
                "run_dir": str(run_dir),
                "module_name": "session_v2",
                "candidate_name": "utc_fixed_session_label",
                "policy": "diagnostic_only",
                "notes": "",
            }
        ],
    )
    summary_csv, _, _, _ = build_summary(targets, tmp_path / "out", "vrid")
    row = pd.read_csv(summary_csv).iloc[0]
    assert float(row["trade_count"]) == 64
    assert float(row["total_pnl"]) == 1.2
    assert float(row["average_pnl"]) == 0.01875
    assert float(row["win_rate"]) == 0.75


def test_fallback_to_trade_logs_when_backtest_summary_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_b"
    _write_csv(
        run_dir / "trade_logs.csv",
        ["entry_time", "exit_time", "pnl"],
        [
            {"entry_time": "2024-11-01T00:00:00+00:00", "exit_time": "2024-11-01T00:05:00+00:00", "pnl": "1.0"},
            {"entry_time": "2024-11-01T00:10:00+00:00", "exit_time": "2024-11-01T00:15:00+00:00", "pnl": "-0.5"},
        ],
    )
    targets = tmp_path / "targets.csv"
    _write_targets(
        targets,
        [
            {
                "validation_target_id": "t1",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": "r1",
                "run_dir": str(run_dir),
                "module_name": "exit_policy",
                "candidate_name": "simple",
                "policy": "diagnostic_reference",
                "notes": "",
            }
        ],
    )
    summary_csv, decision_csv, _, md = build_summary(targets, tmp_path / "out", "vrid")
    row = pd.read_csv(summary_csv).iloc[0]
    assert float(row["trade_count"]) == 2
    assert float(row["total_pnl"]) == 0.5
    assert float(row["average_pnl"]) == 0.25
    assert float(row["win_rate"]) == 0.5
    assert "fallback to trade_logs.csv" in pd.read_csv(decision_csv).iloc[0]["warnings"]
    assert "Warnings" in md.read_text(encoding="utf-8")


def test_missing_input_files_continue_with_warning(tmp_path: Path) -> None:
    targets = tmp_path / "targets.csv"
    _write_targets(
        targets,
        [
            {
                "validation_target_id": "missing",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": "r1",
                "run_dir": str(tmp_path / "no_such_run"),
                "module_name": "risk_stop_v2",
                "candidate_name": "daily_consecutive_stop",
                "policy": "diagnostic_counterfactual",
                "notes": "",
            }
        ],
    )
    summary_csv, decision_csv, _, _ = build_summary(targets, tmp_path / "out", "vrid")
    row = pd.read_csv(summary_csv).iloc[0]
    assert row["data_quality_flag"] == "missing_source"
    assert row["decision_status"] == "insufficient_sample"
    assert "missing" in pd.read_csv(decision_csv).iloc[0]["warnings"]


def test_sample_size_flag_classification(tmp_path: Path) -> None:
    rows = []
    for i, tc in enumerate([10, 30, 60], start=1):
        run_dir = tmp_path / f"run_{i}"
        _write_csv(run_dir / "backtest_summary.csv", ["trade_count", "total_pnl", "average_pnl", "win_rate"], [{"trade_count": str(tc), "total_pnl": "0", "average_pnl": "0", "win_rate": "0"}])
        rows.append(
            {
                "validation_target_id": f"t{i}",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": f"r{i}",
                "run_dir": str(run_dir),
                "module_name": "exit_policy",
                "candidate_name": "simple",
                "policy": "diagnostic_reference",
                "notes": "",
            }
        )
    targets = tmp_path / "targets.csv"
    _write_targets(targets, rows)
    summary_csv, _, _, _ = build_summary(targets, tmp_path / "out", "vrid")
    df = pd.read_csv(summary_csv)
    assert df.loc[df["validation_target_id"] == "t1", "sample_size_flag"].iloc[0] == "low"
    assert df.loc[df["validation_target_id"] == "t2", "sample_size_flag"].iloc[0] == "medium"
    assert df.loc[df["validation_target_id"] == "t3", "sample_size_flag"].iloc[0] == "normal"


def test_htf_sr_session_are_keep_as_explanation_layer(tmp_path: Path) -> None:
    rows = []
    for i, mod in enumerate(["htf_v2", "sr_v2", "session_v2"], start=1):
        run_dir = tmp_path / f"run_{mod}"
        _write_csv(run_dir / "backtest_summary.csv", ["trade_count", "total_pnl", "average_pnl", "win_rate"], [{"trade_count": "64", "total_pnl": "0.1", "average_pnl": "0.001", "win_rate": "0.7"}])
        rows.append(
            {
                "validation_target_id": f"t{i}",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": f"r{i}",
                "run_dir": str(run_dir),
                "module_name": mod,
                "candidate_name": "x",
                "policy": "diagnostic_only",
                "notes": "",
            }
        )
    targets = tmp_path / "targets.csv"
    _write_targets(targets, rows)
    summary_csv, _, _, _ = build_summary(targets, tmp_path / "out", "vrid")
    df = pd.read_csv(summary_csv)
    assert set(df["decision_status"].tolist()) == {"keep_as_explanation_layer"}


def test_risk_stop_negative_net_becomes_pause_no_go(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_risk"
    _write_csv(run_dir / "backtest_summary.csv", ["trade_count", "total_pnl", "average_pnl", "win_rate"], [{"trade_count": "64", "total_pnl": "0.1", "average_pnl": "0.001", "win_rate": "0.7"}])
    _write_csv(
        run_dir / "risk_stop_v2_analysis" / "risk_stop_v2_summary.csv",
        ["net_counterfactual_effect_pips", "avoided_loss_pips", "missed_profit_pips", "stopped_trade_count", "trigger_count"],
        [{"net_counterfactual_effect_pips": "-0.5", "avoided_loss_pips": "0", "missed_profit_pips": "0.5", "stopped_trade_count": "2", "trigger_count": "1"}],
    )
    targets = tmp_path / "targets.csv"
    _write_targets(
        targets,
        [
            {
                "validation_target_id": "t1",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": "r1",
                "run_dir": str(run_dir),
                "module_name": "risk_stop_v2",
                "candidate_name": "daily_consecutive_stop",
                "policy": "diagnostic_counterfactual",
                "notes": "",
            }
        ],
    )
    summary_csv, _, _, _ = build_summary(targets, tmp_path / "out", "vrid")
    row = pd.read_csv(summary_csv).iloc[0]
    assert row["decision_status"] == "pause_no_go"


def test_exit_policy_without_cost_adjusted_is_needs_cost_adjusted_check(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_exit"
    _write_csv(run_dir / "backtest_summary.csv", ["trade_count", "total_pnl", "average_pnl", "win_rate"], [{"trade_count": "64", "total_pnl": "0.1", "average_pnl": "0.001", "win_rate": "0.7"}])
    targets = tmp_path / "targets.csv"
    _write_targets(
        targets,
        [
            {
                "validation_target_id": "t1",
                "period_start": "2024-11-01",
                "period_end": "2024-12-01",
                "period_type": "representative_month",
                "run_id": "r1",
                "run_dir": str(run_dir),
                "module_name": "exit_policy",
                "candidate_name": "simple_trailing_after_1R",
                "policy": "diagnostic_reference",
                "notes": "",
            }
        ],
    )
    summary_csv, _, _, _ = build_summary(targets, tmp_path / "out", "vrid")
    row = pd.read_csv(summary_csv).iloc[0]
    assert row["decision_status"] == "needs_cost_adjusted_check"
