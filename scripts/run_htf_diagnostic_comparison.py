#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.run_csv_replay_pipeline_dry_run import load_and_prepare_input
from scripts.run_csv_replay_pipeline_dry_run import run_csv_replay_pipeline_dry_run
from scripts.run_csv_replay_pipeline_dry_run import write_outputs
from src.backtest.pipeline_adapter import PipelineAdapter
from src.backtest.pipeline_adapter import PipelineAdapterConfig


SUMMARY_FIELDS = [
    "condition",
    "replay_bar_count",
    "decision_log_count",
    "entry_signal_true_count",
    "trade_ok_true_count",
    "htf_filter_enabled",
    "htf_timeframe_policy",
    "htf_neutral_policy",
    "htf_direction_aligned_count",
    "htf_against_entry_count",
    "neutral_passed_count",
    "neutral_rejected_count",
    "htf_filter_rejected_count",
    "htf_filter_rejected_by_reason",
    "real_order_sent_count",
    "no_real_order_integrity_violation_count",
    "entry_set_count",
    "entry_set_only_in_htf_off_count",
    "entry_set_only_in_condition_count",
    "entry_set_intersection_count",
    "entry_set_removed_vs_htf_off_count",
    "entry_set_added_vs_htf_off_count",
    "accepted_entry_set_count",
    "accepted_entry_set_only_in_htf_off_count",
    "accepted_entry_set_only_in_condition_count",
    "accepted_entry_set_intersection_count",
    "accepted_entry_set_removed_vs_htf_off_count",
    "accepted_entry_set_added_vs_htf_off_count",
    "htf_rejected_entry_set_count",
    "htf_rejected_entry_set_vs_htf_off_added_count",
    "htf_rejected_entry_set_vs_htf_off_intersection_count",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run HTF diagnostic comparison (off/permissive/strict).")
    p.add_argument("--input-csv", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--warmup-start", required=True)
    p.add_argument("--replay-start", required=True)
    p.add_argument("--replay-end", required=True)
    p.add_argument("--expected-timeframe-minutes", type=int, default=5)
    return p.parse_args()


def _parse_utc_timestamp(raw: str) -> pd.Timestamp:
    return pd.to_datetime(raw, utc=True)


def _is_true(v: Any) -> bool:
    return str(v or "").strip().lower() in {"true", "1", "yes"}


def _is_neutral(v: Any) -> bool:
    return str(v or "").strip().lower() == "neutral"


def _to_text(v: Any) -> str:
    return str(v or "").strip()


def _entry_set_key(row: dict[str, Any]) -> tuple[str, str] | None:
    timestamp = ""
    for col in ("timestamp", "log_time"):
        value = _to_text(row.get(col, ""))
        if value:
            timestamp = value
            break
    signal_type = _to_text(row.get("signal_type", ""))
    if not timestamp:
        return None
    return (timestamp, signal_type)


def _extract_entry_set(decision_logs: list[dict[str, Any]]) -> set[tuple[str, str]]:
    # v0 candidate entry set: entry_signal == True
    keys: set[tuple[str, str]] = set()
    for row in decision_logs:
        if not _is_true(row.get("entry_signal", "")):
            continue
        key = _entry_set_key(row)
        if key is not None:
            keys.add(key)
    return keys


def _add_entry_set_diff_summary(
    summary_rows: list[dict[str, Any]],
    entry_sets_by_condition: dict[str, set[tuple[str, str]]],
) -> None:
    htf_off_set = entry_sets_by_condition.get("htf_off", set())
    for row in summary_rows:
        condition = _to_text(row.get("condition", ""))
        condition_set = entry_sets_by_condition.get(condition, set())
        removed_vs_off = htf_off_set - condition_set
        added_vs_off = condition_set - htf_off_set
        intersection = htf_off_set & condition_set
        row["entry_set_count"] = len(condition_set)
        row["entry_set_only_in_htf_off_count"] = len(removed_vs_off)
        row["entry_set_only_in_condition_count"] = len(added_vs_off)
        row["entry_set_intersection_count"] = len(intersection)
        row["entry_set_removed_vs_htf_off_count"] = len(removed_vs_off)
        row["entry_set_added_vs_htf_off_count"] = len(added_vs_off)


def _is_htf_filter_rejected(row: dict[str, Any]) -> bool:
    if "htf_filter_rejected" in row:
        return _is_true(row.get("htf_filter_rejected", ""))
    return _is_true(row.get("htf_filter_enabled", "")) and (not _is_true(row.get("htf_direction_aligned", "")))


def _extract_accepted_entry_set(decision_logs: list[dict[str, Any]]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in decision_logs:
        if (not _is_true(row.get("entry_signal", ""))) or (not _is_true(row.get("trade_ok", ""))):
            continue
        key = _entry_set_key(row)
        if key is not None:
            keys.add(key)
    return keys


def _extract_htf_rejected_entry_set(decision_logs: list[dict[str, Any]]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in decision_logs:
        if (not _is_true(row.get("entry_signal", ""))) or (not _is_htf_filter_rejected(row)):
            continue
        key = _entry_set_key(row)
        if key is not None:
            keys.add(key)
    return keys


def _add_accepted_entry_set_diff_summary(
    summary_rows: list[dict[str, Any]],
    accepted_entry_sets_by_condition: dict[str, set[tuple[str, str]]],
) -> None:
    htf_off_set = accepted_entry_sets_by_condition.get("htf_off", set())
    for row in summary_rows:
        condition = _to_text(row.get("condition", ""))
        condition_set = accepted_entry_sets_by_condition.get(condition, set())
        removed_vs_off = htf_off_set - condition_set
        added_vs_off = condition_set - htf_off_set
        intersection = htf_off_set & condition_set
        row["accepted_entry_set_count"] = len(condition_set)
        row["accepted_entry_set_only_in_htf_off_count"] = len(removed_vs_off)
        row["accepted_entry_set_only_in_condition_count"] = len(added_vs_off)
        row["accepted_entry_set_intersection_count"] = len(intersection)
        row["accepted_entry_set_removed_vs_htf_off_count"] = len(removed_vs_off)
        row["accepted_entry_set_added_vs_htf_off_count"] = len(added_vs_off)


def _add_htf_rejected_entry_set_summary(
    summary_rows: list[dict[str, Any]],
    htf_rejected_entry_sets_by_condition: dict[str, set[tuple[str, str]]],
) -> None:
    htf_off_set = htf_rejected_entry_sets_by_condition.get("htf_off", set())
    for row in summary_rows:
        condition = _to_text(row.get("condition", ""))
        condition_set = htf_rejected_entry_sets_by_condition.get(condition, set())
        row["htf_rejected_entry_set_count"] = len(condition_set)
        row["htf_rejected_entry_set_vs_htf_off_added_count"] = len(condition_set - htf_off_set)
        row["htf_rejected_entry_set_vs_htf_off_intersection_count"] = len(condition_set & htf_off_set)


def summarize_condition(
    *,
    condition: str,
    result_summary: dict[str, Any],
    decision_logs: list[dict[str, Any]],
    htf_filter_enabled: bool,
    htf_timeframe_policy: str,
    htf_neutral_policy: str,
) -> dict[str, Any]:
    aligned_count = 0
    against_count = 0
    neutral_passed_count = 0
    neutral_rejected_count = 0
    rejected_count = 0
    rejected_reasons: Counter[str] = Counter()

    for row in decision_logs:
        aligned = _is_true(row.get("htf_direction_aligned", ""))
        htf_enabled_row = _is_true(row.get("htf_filter_enabled", ""))
        htf_bias_neutral = _is_neutral(row.get("htf_bias", ""))
        htf_trend_neutral = _is_neutral(row.get("htf_trend_dir", ""))
        htf_reason = _to_text(row.get("htf_filter_reason", ""))

        if aligned:
            aligned_count += 1
        else:
            # v0 conservative definition
            against_count += 1

        if (htf_bias_neutral or htf_trend_neutral) and aligned:
            neutral_passed_count += 1
        if (htf_bias_neutral or htf_trend_neutral) and (not aligned):
            neutral_rejected_count += 1

        if htf_enabled_row and (not aligned):
            rejected_count += 1
            rejected_reasons[htf_reason] += 1

    return {
        "condition": condition,
        "replay_bar_count": result_summary.get("replay_bar_count", 0),
        "decision_log_count": result_summary.get("decision_log_count", 0),
        "entry_signal_true_count": result_summary.get("entry_signal_true_count", 0),
        "trade_ok_true_count": result_summary.get("trade_ok_true_count", 0),
        "htf_filter_enabled": htf_filter_enabled,
        "htf_timeframe_policy": htf_timeframe_policy,
        "htf_neutral_policy": htf_neutral_policy,
        "htf_direction_aligned_count": aligned_count,
        "htf_against_entry_count": against_count,
        "neutral_passed_count": neutral_passed_count,
        "neutral_rejected_count": neutral_rejected_count,
        "htf_filter_rejected_count": rejected_count,
        "htf_filter_rejected_by_reason": dict(rejected_reasons),
        "real_order_sent_count": result_summary.get("real_order_sent_count", 0),
        "no_real_order_integrity_violation_count": result_summary.get("no_real_order_integrity_violation_count", 0),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_summary_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# htf diagnostic comparison summary",
        "",
        "- structure diagnostics only (not profitability confirmation)",
        "- HTF OFF / permissive / strict comparison on near_live logs",
        "- PnL metrics are out of scope in this runner",
        "",
    ]
    for row in rows:
        lines.append(
            f"- condition={row['condition']} replay_bar_count={row['replay_bar_count']} "
            f"decision_log_count={row['decision_log_count']} entry_signal_true_count={row['entry_signal_true_count']} "
            f"trade_ok_true_count={row['trade_ok_true_count']} htf_direction_aligned_count={row['htf_direction_aligned_count']} "
            f"htf_against_entry_count={row['htf_against_entry_count']} neutral_passed_count={row['neutral_passed_count']} "
            f"neutral_rejected_count={row['neutral_rejected_count']} htf_filter_rejected_count={row['htf_filter_rejected_count']} "
            f"real_order_sent_count={row['real_order_sent_count']} no_real_order_integrity_violation_count={row['no_real_order_integrity_violation_count']} "
            f"entry_set_count={row.get('entry_set_count', 0)} entry_set_removed_vs_htf_off_count={row.get('entry_set_removed_vs_htf_off_count', 0)} "
            f"entry_set_added_vs_htf_off_count={row.get('entry_set_added_vs_htf_off_count', 0)} "
            f"entry_set_intersection_count={row.get('entry_set_intersection_count', 0)} "
            f"accepted_entry_set_count={row.get('accepted_entry_set_count', 0)} "
            f"accepted_entry_set_removed_vs_htf_off_count={row.get('accepted_entry_set_removed_vs_htf_off_count', 0)} "
            f"accepted_entry_set_added_vs_htf_off_count={row.get('accepted_entry_set_added_vs_htf_off_count', 0)} "
            f"accepted_entry_set_intersection_count={row.get('accepted_entry_set_intersection_count', 0)} "
            f"htf_rejected_entry_set_count={row.get('htf_rejected_entry_set_count', 0)} "
            f"htf_rejected_entry_set_vs_htf_off_added_count={row.get('htf_rejected_entry_set_vs_htf_off_added_count', 0)} "
            f"htf_rejected_entry_set_vs_htf_off_intersection_count={row.get('htf_rejected_entry_set_vs_htf_off_intersection_count', 0)}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_htf_diagnostic_comparison(
    *,
    input_csv: Path,
    output_dir: Path,
    run_id: str,
    warmup_start: pd.Timestamp,
    replay_start: pd.Timestamp,
    replay_end: pd.Timestamp,
    expected_timeframe_minutes: int,
) -> list[dict[str, Any]]:
    df, duplicate_timestamps, out_of_order_timestamps = load_and_prepare_input(input_csv)

    conditions = [
        ("htf_off", False, "H1_only", "permissive"),
        ("htf_permissive", True, "H1_only", "permissive"),
        ("htf_strict", True, "H1_only", "strict"),
    ]

    summary_rows: list[dict[str, Any]] = []
    entry_sets_by_condition: dict[str, set[tuple[str, str]]] = {}
    accepted_entry_sets_by_condition: dict[str, set[tuple[str, str]]] = {}
    htf_rejected_entry_sets_by_condition: dict[str, set[tuple[str, str]]] = {}
    output_dir.mkdir(parents=True, exist_ok=True)

    for condition_name, htf_enabled, timeframe_policy, neutral_policy in conditions:
        condition_dir = output_dir / condition_name
        adapter = PipelineAdapter(
            PipelineAdapterConfig(
                htf_filter_enabled=htf_enabled,
                htf_timeframe_policy=timeframe_policy,
                htf_neutral_policy=neutral_policy,
            )
        )
        result = run_csv_replay_pipeline_dry_run(
            df=df,
            duplicate_timestamps=duplicate_timestamps,
            out_of_order_timestamps=out_of_order_timestamps,
            run_id=f"{run_id}_{condition_name}",
            warmup_start=warmup_start,
            replay_start=replay_start,
            replay_end=replay_end,
            expected_timeframe_minutes=expected_timeframe_minutes,
            adapter=adapter,
        )
        write_outputs(condition_dir, result)
        entry_sets_by_condition[condition_name] = _extract_entry_set(result.decision_logs)
        accepted_entry_sets_by_condition[condition_name] = _extract_accepted_entry_set(result.decision_logs)
        htf_rejected_entry_sets_by_condition[condition_name] = _extract_htf_rejected_entry_set(result.decision_logs)
        summary_rows.append(
            summarize_condition(
                condition=condition_name,
                result_summary=result.summary,
                decision_logs=result.decision_logs,
                htf_filter_enabled=htf_enabled,
                htf_timeframe_policy=timeframe_policy,
                htf_neutral_policy=neutral_policy,
            )
        )

    _add_entry_set_diff_summary(summary_rows, entry_sets_by_condition)
    _add_accepted_entry_set_diff_summary(summary_rows, accepted_entry_sets_by_condition)
    _add_htf_rejected_entry_set_summary(summary_rows, htf_rejected_entry_sets_by_condition)
    _write_csv(output_dir / "htf_diagnostic_comparison_summary.csv", summary_rows, SUMMARY_FIELDS)
    _write_summary_md(output_dir / "htf_diagnostic_comparison_summary.md", summary_rows)
    return summary_rows


def main() -> int:
    args = parse_args()
    warmup_start = _parse_utc_timestamp(args.warmup_start)
    replay_start = _parse_utc_timestamp(args.replay_start)
    replay_end = _parse_utc_timestamp(args.replay_end)
    if not (warmup_start <= replay_start < replay_end):
        raise ValueError("Invalid period bounds: must satisfy warmup_start <= replay_start < replay_end")

    rows = run_htf_diagnostic_comparison(
        input_csv=Path(args.input_csv),
        output_dir=Path(args.output_dir),
        run_id=args.run_id,
        warmup_start=warmup_start,
        replay_start=replay_start,
        replay_end=replay_end,
        expected_timeframe_minutes=args.expected_timeframe_minutes,
    )
    print(f"[done] compared_conditions={len(rows)}")
    print(f"[done] output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
