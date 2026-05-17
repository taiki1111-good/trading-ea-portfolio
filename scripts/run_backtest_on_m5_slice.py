#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.backtest.backtest_runner import BacktestRunner
from src.backtest.pipeline_adapter import PipelineAdapter, PipelineAdapterConfig
from src.backtest.types import BacktestConfig
from src.data.price_loader import PriceDataLoader
from src.persistence.csv_log_reader import CsvLogReader
from src.persistence.csv_log_writer import CsvLogWriter
from src.persistence.csv_schema_validator import CsvSchemaValidator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal backtest on generated M5 slice CSV.")
    parser.add_argument("--input-csv", required=True, help="M5 PriceDataLoader-compatible input CSV path.")
    parser.add_argument("--run-id", required=True, help="Backtest run id.")
    parser.add_argument("--output-dir", required=True, help="Output directory for logs and summaries.")
    parser.add_argument("--max-holding-bars", type=int, required=True, help="Backtest max holding bars.")
    parser.add_argument(
        "--allow-invalid-logs",
        action="store_true",
        help="Do not fail run even when schema/consistency validation is invalid.",
    )
    fb_group = parser.add_mutually_exclusive_group()
    fb_group.add_argument(
        "--allow-heuristic-fallback",
        action="store_true",
        help="Enable heuristic fallback in PipelineAdapter (default behavior).",
    )
    fb_group.add_argument(
        "--disable-heuristic-fallback",
        action="store_true",
        help="Disable heuristic fallback in PipelineAdapter and use detector-chain only.",
    )
    parser.add_argument(
        "--third-candidate-lookback-bars",
        type=int,
        default=5,
        help="Lookback bars for temporal third candidate to connect with breakout.",
    )
    parser.add_argument(
        "--disable-temporal-third-break",
        action="store_true",
        help="Disable temporal third_wave_break connection in detector chain.",
    )
    parser.add_argument(
        "--max-entries-per-recent-third-candidate",
        type=int,
        default=None,
        help="Limit entries per identical recent_third_timestamp (None means unlimited).",
    )
    return parser.parse_args()


def to_iso_or_empty(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _to_csv_value(value: Any) -> str:
    if isinstance(value, list):
        return " | ".join(str(v) for v in value)
    if value is None:
        return ""
    return str(value)


def evaluate_log_validation(trade_logs: list[dict[str, Any]], decision_logs: list[dict[str, Any]]) -> dict[str, Any]:
    trade_schema = CsvSchemaValidator.validate_records("trade_logs", trade_logs)
    decision_schema = CsvSchemaValidator.validate_records("decision_logs", decision_logs)
    consistency = CsvSchemaValidator.validate_backtest_log_consistency(trade_logs=trade_logs, decision_logs=decision_logs)

    schema_warnings = list(trade_schema.warnings) + list(decision_schema.warnings)

    return {
        "trade_logs_schema_valid": trade_schema.valid,
        "decision_logs_schema_valid": decision_schema.valid,
        "log_consistency_valid": consistency.valid,
        "trade_schema_validation_reason": trade_schema.validation_reason,
        "decision_schema_validation_reason": decision_schema.validation_reason,
        "consistency_reason": consistency.consistency_reason,
        "schema_warnings": schema_warnings,
        "consistency_warnings": consistency.warnings,
    }


def write_summary_csv(path: Path, summary: dict[str, Any]) -> None:
    columns = [
        "run_id",
        "input_csv",
        "bar_count",
        "start_time",
        "end_time",
        "trade_count",
        "total_pnl",
        "average_pnl",
        "trade_log_path",
        "trade_log_write_success",
        "trade_log_schema_valid",
        "decision_logs_schema_valid",
        "log_consistency_valid",
        "schema_validation_reason",
        "consistency_reason",
        "summary_reason",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerow(summary)


def write_summary_md(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Backtest Summary",
        "",
        f"- run_id: {summary['run_id']}",
        f"- input_csv: {summary['input_csv']}",
        f"- bar_count: {summary['bar_count']}",
        f"- start_time: {summary['start_time']}",
        f"- end_time: {summary['end_time']}",
        f"- trade_count: {summary['trade_count']}",
        f"- total_pnl: {summary['total_pnl']}",
        f"- average_pnl: {summary['average_pnl']}",
        f"- trade_log_path: {summary['trade_log_path']}",
        f"- trade_log_write_success: {summary['trade_log_write_success']}",
        f"- trade_log_schema_valid: {summary['trade_log_schema_valid']}",
        f"- decision_logs_schema_valid: {summary['decision_logs_schema_valid']}",
        f"- log_consistency_valid: {summary['log_consistency_valid']}",
        f"- schema_validation_reason: {summary['schema_validation_reason']}",
        f"- consistency_reason: {summary['consistency_reason']}",
        f"- summary_reason: {summary['summary_reason']}",
        f"- notes: {summary['notes']}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_log_validation_summary_csv(path: Path, validation: dict[str, Any]) -> None:
    rows = [{"metric": k, "value": _to_csv_value(v)} for k, v in validation.items()]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)


def write_log_validation_summary_md(path: Path, validation: dict[str, Any]) -> None:
    lines = [
        "# Log Validation Summary",
        "",
        f"- trade_logs_schema_valid: {validation['trade_logs_schema_valid']}",
        f"- decision_logs_schema_valid: {validation['decision_logs_schema_valid']}",
        f"- log_consistency_valid: {validation['log_consistency_valid']}",
        f"- trade_schema_validation_reason: {validation['trade_schema_validation_reason']}",
        f"- decision_schema_validation_reason: {validation['decision_schema_validation_reason']}",
        f"- consistency_reason: {validation['consistency_reason']}",
        f"- schema_warnings: {validation['schema_warnings']}",
        f"- consistency_warnings: {validation['consistency_warnings']}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_empty_trade_log_csv(path: Path) -> None:
    columns = [
        "log_time",
        "entry_time",
        "exit_time",
        "signal_type",
        "order_result",
        "lot",
        "fill_price",
        "execution_price",
        "stop_loss",
        "take_profit",
        "pnl",
        "realized_pnl",
        "exit_reason",
        "entry_reason",
        "signal_reason",
        "risk_reason",
        "filter_reason",
        "fallback_used",
        "structure_source",
        "recent_third_timestamp",
        "recent_third_direction",
        "temporal_lag_bars",
        "temporal_lookback_bars",
        "breakout_direction",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()


def write_records_csv(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        path.write_text("", encoding="utf-8")
        return
    columns = list(records[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in records:
            writer.writerow(row)


def main() -> int:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_csv.exists():
        raise FileNotFoundError(f"input CSV not found: {input_csv}")

    price_frame = PriceDataLoader.load_from_csv(str(input_csv), timeframe="M5")
    config = BacktestConfig(run_id=args.run_id, max_holding_bars=args.max_holding_bars)
    allow_fallback = not args.disable_heuristic_fallback
    allow_temporal = not args.disable_temporal_third_break
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=allow_fallback,
            third_candidate_lookback_bars=args.third_candidate_lookback_bars,
            allow_temporal_third_break=allow_temporal,
            max_entries_per_recent_third_candidate=args.max_entries_per_recent_third_candidate,
        )
    )
    result = BacktestRunner.run(price_frame=price_frame, config=config, entry_event_provider=adapter)

    summary = result.summary
    if summary is None:
        raise RuntimeError("Backtest finished without summary.")

    trade_log_path = output_dir / "trade_logs.csv"
    decision_log_path = output_dir / "decision_logs.csv"
    trade_log_write_success = False
    trade_log_schema_valid = ""
    schema_reason = ""
    notes = [
        "This run uses spread=0.2 pips fallback data for initial structure/backtest checks, not operation-like validation.",
        f"allow_heuristic_fallback={allow_fallback}",
        f"allow_temporal_third_break={allow_temporal}",
        f"third_candidate_lookback_bars={args.third_candidate_lookback_bars}",
        f"max_entries_per_recent_third_candidate={args.max_entries_per_recent_third_candidate}",
    ]

    if result.trade_logs:
        write_result = CsvLogWriter.write(str(trade_log_path), result.trade_logs, append=False)
        trade_log_write_success = bool(write_result.success)
        if write_result.success:
            read_result = CsvLogReader.read(str(trade_log_path))
            if read_result.success:
                schema_result = CsvSchemaValidator.validate_records("trade_logs", read_result.data)
                trade_log_schema_valid = str(schema_result.valid)
                schema_reason = schema_result.validation_reason
            else:
                trade_log_schema_valid = "False"
                schema_reason = read_result.persistence_reason
        else:
            trade_log_schema_valid = "False"
            schema_reason = write_result.persistence_reason
    else:
        write_empty_trade_log_csv(trade_log_path)
        notes.append("No trade logs generated (trade_count=0). Current conditions produced no qualifying entries.")
        if not allow_fallback:
            notes.append("detector_chain 由来の entry はこの期間では発火なし")

    if schema_reason:
        notes.append(f"trade_log_schema_reason={schema_reason}")
    if result.decision_logs:
        write_records_csv(decision_log_path, result.decision_logs)
    else:
        decision_log_path.write_text("", encoding="utf-8")

    validation = evaluate_log_validation(result.trade_logs, result.decision_logs)
    validation_valid = (
        validation["trade_logs_schema_valid"] and validation["decision_logs_schema_valid"] and validation["log_consistency_valid"]
    )
    if not validation_valid and not args.allow_invalid_logs:
        notes.append("log validation failed; rerun with --allow-invalid-logs to keep artifacts without error exit")

    validation_md = output_dir / "log_validation_summary.md"
    validation_csv = output_dir / "log_validation_summary.csv"
    write_log_validation_summary_md(validation_md, validation)
    write_log_validation_summary_csv(validation_csv, validation)

    summary_record = {
        "run_id": args.run_id,
        "input_csv": str(input_csv),
        "bar_count": summary.bar_count,
        "start_time": to_iso_or_empty(summary.start_time),
        "end_time": to_iso_or_empty(summary.end_time),
        "trade_count": summary.trade_count,
        "total_pnl": summary.total_pnl,
        "average_pnl": "" if summary.average_pnl is None else summary.average_pnl,
        "trade_log_path": str(trade_log_path) if result.trade_logs else "",
        "trade_log_write_success": trade_log_write_success,
        "trade_log_schema_valid": validation["trade_logs_schema_valid"],
        "decision_logs_schema_valid": validation["decision_logs_schema_valid"],
        "log_consistency_valid": validation["log_consistency_valid"],
        "schema_validation_reason": (
            f"trade={validation['trade_schema_validation_reason']} ; decision={validation['decision_schema_validation_reason']}"
        ),
        "consistency_reason": validation["consistency_reason"],
        "summary_reason": summary.summary_reason,
        "notes": " ; ".join(notes),
    }

    write_summary_csv(output_dir / "backtest_summary.csv", summary_record)
    write_summary_md(output_dir / "backtest_summary.md", summary_record)

    evaluator_path = output_dir / "evaluator_result.txt"
    evaluator_path.write_text(json.dumps(result.evaluator_result or {}, default=str, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[summary]")
    print(f"run_id={args.run_id}")
    print(f"bar_count={summary.bar_count}")
    print(f"start_time={to_iso_or_empty(summary.start_time)}")
    print(f"end_time={to_iso_or_empty(summary.end_time)}")
    print(f"trade_count={summary.trade_count}")
    print(f"total_pnl={summary.total_pnl}")
    print(f"average_pnl={summary.average_pnl}")
    print(f"trade_log_path={trade_log_path if result.trade_logs else '(none)'}")
    print(f"decision_log_path={decision_log_path if result.decision_logs else '(none)'}")
    print(f"trade_log_write_success={trade_log_write_success}")
    print(f"trade_logs_schema_valid={validation['trade_logs_schema_valid']}")
    print(f"decision_logs_schema_valid={validation['decision_logs_schema_valid']}")
    print(f"log_consistency_valid={validation['log_consistency_valid']}")
    print(f"schema_validation_reason=trade:{validation['trade_schema_validation_reason']} | decision:{validation['decision_schema_validation_reason']}")
    print(f"consistency_reason={validation['consistency_reason']}")
    print(f"schema_warnings={validation['schema_warnings']}")
    print(f"consistency_warnings={validation['consistency_warnings']}")
    print(f"summary_csv={output_dir / 'backtest_summary.csv'}")
    print(f"summary_md={output_dir / 'backtest_summary.md'}")
    print(f"log_validation_summary_csv={validation_csv}")
    print(f"log_validation_summary_md={validation_md}")
    print(f"evaluator_result={evaluator_path}")

    if not validation_valid and not args.allow_invalid_logs:
        raise RuntimeError("log validation failed (schema and/or consistency invalid)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
