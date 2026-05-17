#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from src.persistence.csv_log_reader import CsvLogReader
from src.persistence.csv_schema_validator import CsvSchemaValidator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze backtest decision_logs for entry/no-entry diagnostics.")
    parser.add_argument("--decision-logs", required=True, help="Path to decision_logs.csv")
    parser.add_argument("--trade-logs", required=False, default="", help="Optional path to trade_logs.csv")
    parser.add_argument("--output-dir", required=True, help="Directory to save analysis outputs")
    return parser.parse_args()


def _as_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _as_int(value: Any) -> int | None:
    try:
        return int(float(str(value).strip()))
    except Exception:
        return None


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text != "" and text.lower() != "none"


def write_analysis_csv(path: Path, metrics: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        for k, v in metrics.items():
            writer.writerow({"metric": k, "value": v})


def main() -> int:
    args = parse_args()
    decision_logs_path = Path(args.decision_logs)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    decision_read = CsvLogReader.read(str(decision_logs_path))
    if not decision_read.success:
        raise RuntimeError(decision_read.persistence_reason)
    rows = decision_read.data

    decision_log_count = len(rows)
    schema_result = CsvSchemaValidator.validate_records("decision_logs", rows)
    columns = list(rows[0].keys()) if rows else []
    fail_stage_counts = Counter(str(r.get("fail_stage", "")).strip() for r in rows)

    entry_signal_true = 0
    entry_signal_false = 0
    trade_ok_true = 0
    trade_ok_false = 0
    structure_candidate_true = 0
    structure_candidate_false = 0
    temporal_candidate_true_count = 0
    temporal_candidate_false_count = 0
    direction_aligned_true = 0
    direction_aligned_false = 0
    pattern_allowed_true = 0
    pattern_allowed_false = 0
    recent_third_timestamp_non_empty_count = 0
    temporal_true_and_recent_non_empty_count = 0
    temporal_false_but_recent_non_empty_count = 0
    structure_source_counts = Counter()
    temporal_lag_distribution = Counter()
    no_entry_reasons = Counter()

    for r in rows:
        structure_source_counts[str(r.get("structure_source", "")).strip()] += 1

        entry_signal = _as_bool(r.get("entry_signal"))
        if entry_signal is True:
            entry_signal_true += 1
        elif entry_signal is False:
            entry_signal_false += 1

        trade_ok = _as_bool(r.get("trade_ok"))
        if trade_ok is True:
            trade_ok_true += 1
        elif trade_ok is False:
            trade_ok_false += 1

        structure_candidate = _as_bool(r.get("structure_candidate"))
        if structure_candidate is True:
            structure_candidate_true += 1
        elif structure_candidate is False:
            structure_candidate_false += 1

        temporal_candidate = _as_bool(r.get("temporal_candidate"))
        if temporal_candidate is True:
            temporal_candidate_true_count += 1
        elif temporal_candidate is False:
            temporal_candidate_false_count += 1

        direction_aligned = _as_bool(r.get("direction_aligned"))
        if direction_aligned is True:
            direction_aligned_true += 1
        elif direction_aligned is False:
            direction_aligned_false += 1

        pattern_allowed = _as_bool(r.get("pattern_allowed"))
        if pattern_allowed is True:
            pattern_allowed_true += 1
        elif pattern_allowed is False:
            pattern_allowed_false += 1

        recent_non_empty = _non_empty(r.get("recent_third_timestamp"))
        if recent_non_empty:
            recent_third_timestamp_non_empty_count += 1
        if temporal_candidate is True and recent_non_empty:
            temporal_true_and_recent_non_empty_count += 1
        if temporal_candidate is False and recent_non_empty:
            temporal_false_but_recent_non_empty_count += 1

        lag = _as_int(r.get("temporal_lag_bars"))
        if lag is not None:
            temporal_lag_distribution[str(lag)] += 1

        reason = str(r.get("decision_reason", "")).strip()
        if trade_ok is not True and reason:
            no_entry_reasons[reason] += 1

    detector_chain_temporal_count = int(structure_source_counts.get("detector_chain_temporal", 0))
    signal_fail_count = int(fail_stage_counts.get("signal", 0))
    risk_filter_fail_count = int(fail_stage_counts.get("risk_filter", 0))
    dedup_count = int(fail_stage_counts.get("dedup", 0))

    trade_count = None
    trade_ok_true_matches_trade_count = None
    if args.trade_logs:
        trade_read = CsvLogReader.read(str(Path(args.trade_logs)))
        if trade_read.success:
            trade_rows = trade_read.data
            trade_count = len(trade_rows)
            trade_ok_true_matches_trade_count = trade_count == trade_ok_true
            consistency_result = CsvSchemaValidator.validate_backtest_log_consistency(
                trade_logs=trade_rows,
                decision_logs=rows,
            )
        else:
            consistency_result = None
    else:
        consistency_result = None

    expected_columns = [
        "log_time",
        "bar_index",
        "timestamp",
        "close",
        "htf_bias",
        "wave_phase",
        "wave_direction",
        "breakout_flag",
        "breakout_direction",
        "structure_candidate",
        "structure_source",
        "temporal_candidate",
        "recent_third_timestamp",
        "recent_third_direction",
        "temporal_lag_bars",
        "temporal_lookback_bars",
        "direction_aligned",
        "pattern_allowed",
        "entry_signal",
        "trade_ok",
        "fail_stage",
        "decision_reason",
    ]
    missing_columns = [c for c in expected_columns if c not in columns]

    metrics: dict[str, Any] = {
        "decision_log_count": decision_log_count,
        "decision_log_columns": columns,
        "missing_expected_columns": missing_columns,
        "fail_stage_counts": dict(fail_stage_counts),
        "entry_signal_true_count": entry_signal_true,
        "entry_signal_false_count": entry_signal_false,
        "trade_ok_true_count": trade_ok_true,
        "trade_ok_false_count": trade_ok_false,
        "structure_candidate_true_count": structure_candidate_true,
        "structure_candidate_false_count": structure_candidate_false,
        "structure_source_counts": dict(structure_source_counts),
        "temporal_candidate_true_count": temporal_candidate_true_count,
        "temporal_candidate_false_count": temporal_candidate_false_count,
        "detector_chain_temporal_count": detector_chain_temporal_count,
        "direction_aligned_true_count": direction_aligned_true,
        "direction_aligned_false_count": direction_aligned_false,
        "pattern_allowed_true_count": pattern_allowed_true,
        "pattern_allowed_false_count": pattern_allowed_false,
        "recent_third_timestamp_non_empty_count": recent_third_timestamp_non_empty_count,
        "temporal_true_and_recent_non_empty_count": temporal_true_and_recent_non_empty_count,
        "temporal_false_but_recent_non_empty_count": temporal_false_but_recent_non_empty_count,
        "temporal_lag_bars_distribution": dict(temporal_lag_distribution),
        "signal_fail_count": signal_fail_count,
        "risk_filter_fail_count": risk_filter_fail_count,
        "dedup_count": dedup_count,
        "top_no_entry_decision_reasons": dict(no_entry_reasons.most_common(10)),
        "trade_count_from_trade_logs": trade_count,
        "trade_ok_true_matches_trade_count": trade_ok_true_matches_trade_count,
        "schema_valid": schema_result.valid,
        "schema_validation_reason": schema_result.validation_reason,
        "schema_warnings": schema_result.warnings,
        "consistency_valid": None if consistency_result is None else consistency_result.valid,
        "consistency_reason": "" if consistency_result is None else consistency_result.consistency_reason,
        "consistency_warnings": [] if consistency_result is None else consistency_result.warnings,
    }

    analysis_csv = output_dir / "decision_log_analysis.csv"
    analysis_md = output_dir / "decision_log_analysis.md"
    write_analysis_csv(analysis_csv, metrics)

    lines = [
        "# Decision Log Analysis",
        "",
        "## 注意書き",
        "- この結果は初期BT/構造検証用であり、収益性評価ではない。",
        "- spread=0.2 pips fallback 前提。",
        "- 手数料・スリッページ・スワップ未反映。",
        "",
        "## 集計",
        f"- decision_log_count: {decision_log_count}",
        f"- decision_log_columns: {columns}",
        f"- missing_expected_columns: {missing_columns}",
        f"- fail_stage_counts: {dict(fail_stage_counts)}",
        f"- entry_signal_true_count: {entry_signal_true}",
        f"- entry_signal_false_count: {entry_signal_false}",
        f"- trade_ok_true_count: {trade_ok_true}",
        f"- trade_ok_false_count: {trade_ok_false}",
        f"- structure_candidate_true_count: {structure_candidate_true}",
        f"- structure_candidate_false_count: {structure_candidate_false}",
        f"- structure_source_counts: {dict(structure_source_counts)}",
        f"- temporal_candidate_true_count: {temporal_candidate_true_count}",
        f"- temporal_candidate_false_count: {temporal_candidate_false_count}",
        f"- detector_chain_temporal_count: {detector_chain_temporal_count}",
        f"- direction_aligned_true_count: {direction_aligned_true}",
        f"- direction_aligned_false_count: {direction_aligned_false}",
        f"- pattern_allowed_true_count: {pattern_allowed_true}",
        f"- pattern_allowed_false_count: {pattern_allowed_false}",
        f"- recent_third_timestamp_non_empty_count: {recent_third_timestamp_non_empty_count}",
        f"- temporal_true_and_recent_non_empty_count: {temporal_true_and_recent_non_empty_count}",
        f"- temporal_false_but_recent_non_empty_count: {temporal_false_but_recent_non_empty_count}",
        f"- temporal_lag_bars_distribution: {dict(temporal_lag_distribution)}",
        f"- signal_fail_count: {signal_fail_count}",
        f"- risk_filter_fail_count: {risk_filter_fail_count}",
        f"- dedup_count: {dedup_count}",
        f"- top_no_entry_decision_reasons: {dict(no_entry_reasons.most_common(10))}",
        f"- trade_count_from_trade_logs: {trade_count}",
        f"- trade_ok_true_matches_trade_count: {trade_ok_true_matches_trade_count}",
        f"- schema_valid: {schema_result.valid}",
        f"- schema_validation_reason: {schema_result.validation_reason}",
        f"- schema_warnings: {schema_result.warnings}",
        f"- consistency_valid: {None if consistency_result is None else consistency_result.valid}",
        f"- consistency_reason: {'' if consistency_result is None else consistency_result.consistency_reason}",
        f"- consistency_warnings: {[] if consistency_result is None else consistency_result.warnings}",
        "",
    ]
    analysis_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[done] decision_logs={decision_logs_path}")
    print(f"[done] analysis_csv={analysis_csv}")
    print(f"[done] analysis_md={analysis_md}")
    print(f"[summary] decision_log_count={decision_log_count}, trade_ok_true_count={trade_ok_true}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
