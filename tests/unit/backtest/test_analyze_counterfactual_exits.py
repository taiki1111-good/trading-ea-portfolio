from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.analyze_counterfactual_exits import PriceBar
from scripts.analyze_counterfactual_exits import TradeRecord
from scripts.analyze_counterfactual_exits import evaluate_trailing_rule


def _write_price_csv(path: Path) -> None:
    rows = [
        ["timestamp", "open", "high", "low", "close", "spread", "volume"],
        ["2024-01-01T00:00:00Z", "100", "101", "99", "100", "0.2", "1"],
        ["2024-01-01T00:05:00Z", "100", "102", "99", "101", "0.2", "1"],
        ["2024-01-01T00:10:00Z", "101", "103", "100", "102", "0.2", "1"],
        ["2024-01-01T00:15:00Z", "102", "104", "101", "103", "0.2", "1"],
        ["2024-01-01T00:20:00Z", "103", "105", "102", "104", "0.2", "1"],
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def _write_trade_logs(path: Path) -> None:
    fields = [
        "signal_type",
        "entry_time",
        "fill_price",
        "stop_loss",
        "take_profit",
        "exit_time",
        "exit_reason",
        "pnl",
    ]
    rows = [
        {
            "signal_type": "long_entry",
            "entry_time": "2024-01-01T00:05:00+00:00",
            "fill_price": "101",
            "stop_loss": "100",
            "take_profit": "103",
            "exit_time": "2024-01-01T00:15:00+00:00",
            "exit_reason": "take_profit",
            "pnl": "2",
        },
        {
            "signal_type": "short_entry",
            "entry_time": "2024-01-01T00:10:00+00:00",
            "fill_price": "102",
            "stop_loss": "103",
            "take_profit": "100",
            "exit_time": "2024-01-01T00:15:00+00:00",
            "exit_reason": "stop_loss",
            "pnl": "-1",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _run_script(tmp_path: Path, with_review: bool) -> Path:
    price_csv = tmp_path / "price.csv"
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    trade_logs = run_dir / "trade_logs.csv"
    output_dir = tmp_path / "out"

    _write_price_csv(price_csv)
    _write_trade_logs(trade_logs)

    if with_review:
        mtf = run_dir / "mtf_charts"
        mtf.mkdir(parents=True, exist_ok=True)
        review_csv = mtf / "chart_review_template.csv"
        with review_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "chart_file",
                    "trade_index",
                    "signal_type",
                    "entry_time",
                    "exit_time",
                    "recent_third_timestamp",
                    "temporal_lag_bars",
                    "exit_reason",
                    "pnl",
                    "structure_source",
                    "visual_entry_ok",
                    "visual_exit_ok",
                    "issue_category",
                    "issue_note",
                    "priority",
                ],
            )
            writer.writeheader()
            writer.writerow({"trade_index": "0", "issue_category": "sl_tp_too_fixed"})
            writer.writerow({"trade_index": "1", "issue_category": "entry_ok"})

    script = Path("scripts/analyze_counterfactual_exits.py").resolve()
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--price-csv",
            str(price_csv),
            "--trade-logs",
            str(trade_logs),
            "--output-dir",
            str(output_dir),
            "--max-holding-bars",
            "3",
            "--sl-multiplier-list",
            "1.5,2.0",
            "--tp-multiplier-list",
            "1.5,2.0",
            "--include-breakeven",
            "--include-trailing",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return output_dir


def test_baseline_trade_count_matches_trade_logs(tmp_path: Path) -> None:
    output_dir = _run_script(tmp_path, with_review=False)
    out_csv = output_dir / "counterfactual_exit_analysis.csv"
    rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8", newline="")))
    baseline = next(r for r in rows if r["rule_name"] == "baseline_fixed_exit")
    assert int(baseline["trade_count"]) == 2


def test_wider_sl_fixed_tp_rule_is_generated(tmp_path: Path) -> None:
    output_dir = _run_script(tmp_path, with_review=False)
    out_csv = output_dir / "counterfactual_exit_analysis.csv"
    rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8", newline="")))
    names = {r["rule_name"] for r in rows}
    assert "wider_sl_fixed_tp_slx1.5" in names
    assert "wider_sl_fixed_tp_slx2" in names


def test_invalid_price_or_trade_logs_error(tmp_path: Path) -> None:
    script = Path("scripts/analyze_counterfactual_exits.py").resolve()
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--price-csv",
            str(tmp_path / "missing_price.csv"),
            "--trade-logs",
            str(tmp_path / "missing_trade_logs.csv"),
            "--output-dir",
            str(tmp_path / "out"),
            "--max-holding-bars",
            "3",
            "--sl-multiplier-list",
            "1.5",
            "--tp-multiplier-list",
            "1.5",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "price_csv not found" in result.stderr or "trade_logs not found" in result.stderr


def test_runs_without_chart_review_csv(tmp_path: Path) -> None:
    output_dir = _run_script(tmp_path, with_review=False)
    out_md = (output_dir / "counterfactual_exit_analysis.md").read_text(encoding="utf-8")
    assert "Counterfactual Exit Analysis" in out_md


def test_issue_category_summary_present_when_review_exists(tmp_path: Path) -> None:
    output_dir = _run_script(tmp_path, with_review=True)
    out_csv = output_dir / "counterfactual_exit_analysis.csv"
    rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8", newline="")))
    baseline = next(r for r in rows if r["rule_name"] == "baseline_fixed_exit")
    issue_summary = json.loads(baseline["issue_improvement_summary"])
    assert "sl_tp_too_fixed" in issue_summary
    assert "entry_ok" in issue_summary


def test_trailing_stop_updates_only_upward_for_long() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100.0, 100.0, 100.0, 100.0),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100.0, 101.2, 100.8, 101.0),
        PriceBar(datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), 101.0, 101.6, 101.1, 101.3),
        PriceBar(datetime(2024, 1, 1, 0, 15, tzinfo=timezone.utc), 101.3, 101.35, 101.2, 101.25),
    ]
    index_map = {b.timestamp: i for i, b in enumerate(bars)}
    trade = TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 105.0, bars[2].timestamp, "take_profit", 2.0)
    result = evaluate_trailing_rule(trade, bars, index_map, 6, "simple_trailing_after_1R")
    d = result.diagnostics or {}
    assert d["trailing_direction_ok"] is True
    assert d["trailing_stop_final"] >= trade.stop_loss


def test_trailing_stop_updates_only_downward_for_short() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100.0, 100.0, 100.0, 100.0),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100.0, 99.2, 98.8, 99.0),
        PriceBar(datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), 99.0, 98.9, 98.4, 98.7),
        PriceBar(datetime(2024, 1, 1, 0, 15, tzinfo=timezone.utc), 98.7, 98.8, 98.6, 98.7),
    ]
    index_map = {b.timestamp: i for i, b in enumerate(bars)}
    trade = TradeRecord(1, "short_entry", "short", bars[0].timestamp, 100.0, 101.0, 95.0, bars[2].timestamp, "take_profit", 2.0)
    result = evaluate_trailing_rule(trade, bars, index_map, 6, "simple_trailing_after_1R")
    d = result.diagnostics or {}
    assert d["trailing_direction_ok"] is True
    assert d["trailing_stop_final"] <= trade.stop_loss


def test_trailing_does_not_exit_on_entry_bar() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100.0, 102.0, 98.0, 100.0),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100.0, 100.2, 99.8, 100.0),
    ]
    index_map = {b.timestamp: i for i, b in enumerate(bars)}
    trade = TradeRecord(2, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 103.0, bars[1].timestamp, "close", 0.0)
    result = evaluate_trailing_rule(trade, bars, index_map, 1, "simple_trailing_after_1R")
    d = result.diagnostics or {}
    assert d["entry_bar_exit"] is False


def test_trailing_never_exceeds_max_holding_bars() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100.0, 100.0, 100.0, 100.0),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100.0, 100.5, 99.5, 100.0),
        PriceBar(datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), 100.0, 100.6, 99.4, 100.1),
        PriceBar(datetime(2024, 1, 1, 0, 15, tzinfo=timezone.utc), 100.1, 100.7, 99.3, 100.2),
    ]
    index_map = {b.timestamp: i for i, b in enumerate(bars)}
    trade = TradeRecord(3, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 103.0, bars[3].timestamp, "close", 0.2)
    result = evaluate_trailing_rule(trade, bars, index_map, 2, "simple_trailing_after_1R")
    assert result.holding_bars <= 2
    assert (result.diagnostics or {})["within_max_holding_bars"] is True


def test_trailing_does_not_use_future_max_price() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100.0, 100.0, 100.0, 100.0),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100.0, 101.2, 99.8, 100.9),
        PriceBar(datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), 100.9, 101.1, 100.0, 100.2),
        PriceBar(datetime(2024, 1, 1, 0, 15, tzinfo=timezone.utc), 100.2, 104.0, 100.1, 103.5),
    ]
    index_map = {b.timestamp: i for i, b in enumerate(bars)}
    trade = TradeRecord(4, "long_entry", "long", bars[0].timestamp, 100.0, 99.0, 110.0, bars[2].timestamp, "stop_loss", -1.0)
    result = evaluate_trailing_rule(trade, bars, index_map, 2, "simple_trailing_after_1R")
    d = result.diagnostics or {}
    assert d["no_future_ref_in_best_favorable"] is True
    assert d["best_favorable_price_seen"] < 104.0


def test_baseline_matches_original_trade_logs_values(tmp_path: Path) -> None:
    output_dir = _run_script(tmp_path, with_review=False)
    details = list(csv.DictReader((output_dir / "counterfactual_exit_trade_details.csv").open("r", encoding="utf-8", newline="")))
    assert len(details) == 2
    assert details[0]["baseline_exit_reason"] == "take_profit"
    assert float(details[0]["baseline_pnl"]) == 2.0
    assert details[1]["baseline_exit_reason"] == "stop_loss"
    assert float(details[1]["baseline_pnl"]) == -1.0
