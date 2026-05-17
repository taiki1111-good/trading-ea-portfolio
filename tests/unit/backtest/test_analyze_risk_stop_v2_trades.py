from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from scripts.analyze_risk_stop_v2_trades import load_trade_logs
from scripts.analyze_risk_stop_v2_trades import run_analysis


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _base_rows() -> list[dict[str, str]]:
    return [
        {"trade_id": "1", "entry_time": "2024-11-01T00:00:00+00:00", "exit_time": "2024-11-01T00:10:00+00:00", "pnl": "-0.10", "direction": "long"},
        {"trade_id": "2", "entry_time": "2024-11-01T00:11:00+00:00", "exit_time": "2024-11-01T00:20:00+00:00", "pnl": "-0.15", "direction": "short"},
        {"trade_id": "3", "entry_time": "2024-11-01T00:21:00+00:00", "exit_time": "2024-11-01T00:30:00+00:00", "pnl": "0.20", "direction": "long"},
        {"trade_id": "4", "entry_time": "2024-11-01T00:31:00+00:00", "exit_time": "2024-11-01T00:40:00+00:00", "pnl": "-0.05", "direction": "short"},
        {"trade_id": "5", "entry_time": "2024-11-02T00:00:00+00:00", "exit_time": "2024-11-02T00:10:00+00:00", "pnl": "-0.04", "direction": "long"},
    ]


def test_trade_logs_processed_in_exit_time_order(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    rows = list(reversed(_base_rows()))
    _write_csv(trade_logs, ["trade_id", "entry_time", "exit_time", "pnl", "direction"], rows)
    out = load_trade_logs(trade_logs, pip_size=0.01)
    assert out["trade_id"].tolist() == [1, 2, 3, 4, 5]


def test_pnl_pips_conversion_is_correct(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    _write_csv(trade_logs, ["entry_time", "exit_time", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "exit_time": "2024-11-01T00:10:00+00:00", "pnl": "0.25"}])
    out = load_trade_logs(trade_logs, pip_size=0.01)
    assert float(out.iloc[0]["pnl_pips"]) == pytest.approx(25.0)


def test_daily_loss_stop_stops_only_following_same_day_trades(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(trade_logs, ["trade_id", "entry_time", "exit_time", "pnl", "direction"], _base_rows())
    trade_csv, summary_csv, _, = run_analysis(trade_logs, out_dir, 0.01, [20], [9])
    tdf = pd.read_csv(trade_csv)
    sdf = pd.read_csv(summary_csv)

    trigger_row = tdf[tdf["trade_id"] == 2].iloc[0]
    assert float(trigger_row["daily_loss_triggered_thresholds"]) == pytest.approx(20.0)

    daily = sdf[(sdf["stop_type"] == "daily_loss_stop") & (sdf["threshold"] == 20)].iloc[0]
    assert int(daily["trigger_count"]) == 1
    assert int(daily["stopped_trade_count"]) == 2


def test_daily_loss_counterfactual_metrics_are_correct(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(trade_logs, ["trade_id", "entry_time", "exit_time", "pnl", "direction"], _base_rows())
    _, summary_csv, _ = run_analysis(trade_logs, out_dir, 0.01, [20], [9])
    row = pd.read_csv(summary_csv).query("stop_type == 'daily_loss_stop' and threshold == 20").iloc[0]
    # stopped trades are trade_id 3 (+20 pips), trade_id 4 (-5 pips)
    assert float(row["avoided_loss_pips"]) == pytest.approx(5.0)
    assert float(row["missed_profit_pips"]) == pytest.approx(20.0)
    assert float(row["net_counterfactual_effect_pips"]) == pytest.approx(-15.0)


def test_consecutive_loss_stop_targets_following_same_day_trades(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(trade_logs, ["trade_id", "entry_time", "exit_time", "pnl", "direction"], _base_rows())
    trade_csv, summary_csv, _ = run_analysis(trade_logs, out_dir, 0.01, [999], [2])
    tdf = pd.read_csv(trade_csv)
    sdf = pd.read_csv(summary_csv)
    trigger_row = tdf[tdf["trade_id"] == 2].iloc[0]
    assert float(trigger_row["consecutive_loss_triggered_thresholds"]) == pytest.approx(2.0)
    row = sdf[(sdf["stop_type"] == "consecutive_loss_stop") & (sdf["threshold"] == 2)].iloc[0]
    assert int(row["stopped_trade_count"]) == 2


def test_consecutive_loss_count_resets_by_utc_day(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(trade_logs, ["trade_id", "entry_time", "exit_time", "pnl", "direction"], _base_rows())
    trade_csv, _, _ = run_analysis(trade_logs, out_dir, 0.01, [999], [2])
    tdf = pd.read_csv(trade_csv)
    assert int(tdf[tdf["trade_id"] == 5].iloc[0]["consecutive_loss_count_after_trade"]) == 1


def test_multiple_thresholds_can_be_evaluated_together(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(trade_logs, ["trade_id", "entry_time", "exit_time", "pnl", "direction"], _base_rows())
    _, summary_csv, _ = run_analysis(trade_logs, out_dir, 0.01, [20, 30], [2, 3])
    sdf = pd.read_csv(summary_csv)
    assert len(sdf[(sdf["stop_type"] == "daily_loss_stop")]) == 2
    assert len(sdf[(sdf["stop_type"] == "consecutive_loss_stop")]) == 2


def test_missing_required_columns_raise_error(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    _write_csv(trade_logs, ["entry_time", "pnl"], [{"entry_time": "2024-11-01T00:00:00+00:00", "pnl": "1"}])
    with pytest.raises(ValueError, match="missing required columns"):
        load_trade_logs(trade_logs, pip_size=0.01)


def test_summary_markdown_is_generated(tmp_path: Path) -> None:
    trade_logs = tmp_path / "trade.csv"
    out_dir = tmp_path / "out"
    _write_csv(trade_logs, ["trade_id", "entry_time", "exit_time", "pnl", "direction"], _base_rows())
    _, _, md = run_analysis(trade_logs, out_dir, 0.01, [20], [2])
    text = md.read_text(encoding="utf-8")
    assert "収益性確認ではない" in text
    assert "Risk/Stopは本体停止ロジックではない" in text
