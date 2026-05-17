#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from src.risk_filter.reason_catalog import normalize_reason_categories


PERIOD_SUMMARY_FIELDS = [
    "run_id",
    "mode",
    "replay_bar_count",
    "decision_log_count",
    "warning_count",
    "duplicate_bar_count",
    "out_of_order_count",
    "data_gap_count",
    "expected_weekend_gap_count",
    "ordinary_missing_bar_gap_count",
    "unknown_gap_count",
    "placeholder_integrity_checked",
    "placeholder_integrity_ok",
    "placeholder_violation_count",
    "entry_signal_true_count",
    "exit_signal_true_count",
    "trade_ok_true_count",
    "paper_order_action_non_none_count",
    "paper_position_state_non_flat_count",
    "log_completeness_ok",
    "data_quality_status",
    "dry_run_health_status",
    "status_reason",
    "pipeline_adapter_error_count",
    "pipeline_adapter_called_count",
    "pipeline_adapter_skipped_count",
    "paper_order_candidate_count",
    "real_order_sent_count",
    "no_real_order_integrity_violation_count",
    "risk_reason_category_counts",
    "filter_reason_category_counts",
    "risk_reason_primary_category_counts",
    "filter_reason_primary_category_counts",
    "risk_reason_unknown_count",
    "filter_reason_unknown_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize CSV replay dry-run outputs for validation framework.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required input file not found: {path}")


def _to_int(row: dict[str, str], key: str) -> int:
    raw = row.get(key, "")
    if raw is None or raw == "":
        return 0
    return int(raw)


def _to_bool_str(v: bool) -> str:
    return "True" if v else "False"


def _normalize_text(v: str) -> str:
    s = (v or "").strip()
    return s if s else "(blank)"


def _bool_text(v: str) -> str:
    s = (v or "").strip().lower()
    if s in {"true", "1", "yes"}:
        return "true"
    if s in {"false", "0", "no"}:
        return "false"
    return "(blank)"


def _is_true(v: str) -> bool:
    return (v or "").strip().lower() in {"true", "1", "yes"}


def _is_none_text(v: str) -> bool:
    return (v or "").strip().lower() == "none"


def _is_flat_text(v: str) -> bool:
    return (v or "").strip().lower() == "flat"


def _primary_category(categories: list[str]) -> str:
    return categories[0] if categories else "unknown"


def _normalize_reason_for_category(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return s if s else ""


def _build_reason_category_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    risk_reason_category_counts: Counter[str] = Counter()
    filter_reason_category_counts: Counter[str] = Counter()
    risk_reason_primary_category_counts: Counter[str] = Counter()
    filter_reason_primary_category_counts: Counter[str] = Counter()
    risk_reason_unknown_count = 0
    filter_reason_unknown_count = 0

    has_risk_reason_col = bool(rows) and ("risk_reason" in rows[0])
    has_filter_reason_col = bool(rows) and ("filter_reason" in rows[0])

    if has_risk_reason_col:
        for r in rows:
            risk_categories = normalize_reason_categories(_normalize_reason_for_category(r.get("risk_reason", "")))
            risk_primary = _primary_category(risk_categories)
            if risk_primary == "unknown":
                risk_reason_unknown_count += 1
            risk_reason_primary_category_counts[risk_primary] += 1
            risk_reason_category_counts.update(risk_categories)

    if has_filter_reason_col:
        for r in rows:
            filter_categories = normalize_reason_categories(_normalize_reason_for_category(r.get("filter_reason", "")))
            filter_primary = _primary_category(filter_categories)
            if filter_primary == "unknown":
                filter_reason_unknown_count += 1
            filter_reason_primary_category_counts[filter_primary] += 1
            filter_reason_category_counts.update(filter_categories)

    return {
        "risk_reason_category_counts": dict(risk_reason_category_counts),
        "filter_reason_category_counts": dict(filter_reason_category_counts),
        "risk_reason_primary_category_counts": dict(risk_reason_primary_category_counts),
        "filter_reason_primary_category_counts": dict(filter_reason_primary_category_counts),
        "risk_reason_unknown_count": risk_reason_unknown_count,
        "filter_reason_unknown_count": filter_reason_unknown_count,
    }


def _count_by(rows: list[dict[str, str]], key: str, value_normalizer: Any = _normalize_text) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    for row in rows:
        value = value_normalizer(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    result = []
    for value in sorted(counts):
        result.append({"summary_type": key, "value": value, "count": str(counts[value])})
    return result


def _build_status(
    replay_bar_count: int,
    decision_log_count: int,
    warning_count: int,
    duplicate_bar_count: int,
    out_of_order_count: int,
    ordinary_missing_bar_gap_count: int,
    unknown_gap_count: int,
    placeholder_integrity_checked: bool,
    placeholder_integrity_ok: bool,
    warning_rows: list[dict[str, str]],
) -> tuple[str, str, str]:
    log_completeness_ok = decision_log_count == replay_bar_count
    if not log_completeness_ok:
        return "no_go_candidate", "no_go_candidate", "decision_log_count_mismatch"

    if placeholder_integrity_checked and (not placeholder_integrity_ok):
        return "no_go_candidate", "no_go_candidate", "placeholder_integrity_violation"

    has_investigate_signal = (
        duplicate_bar_count > 0
        or out_of_order_count > 0
        or ordinary_missing_bar_gap_count > 0
        or unknown_gap_count > 0
    )
    if has_investigate_signal:
        return "investigate", "investigate", "data_quality_investigation_required"

    if warning_count > 0:
        warning_types = {_normalize_text(r.get("warning_type", "")) for r in warning_rows}
        gap_classes = {_normalize_text(r.get("gap_class", "")) for r in warning_rows}
        weekend_only = warning_types == {"data_gap"} and gap_classes == {"expected_weekend_gap"}
        if weekend_only:
            return "warn", "warn", "expected_weekend_gap_only"
        return "investigate", "investigate", "unclassified_warning_pattern"

    return "pass", "clean", "no_warnings_and_log_complete"


def _is_pipeline_mode(summary_row: dict[str, str]) -> bool:
    mode = (summary_row.get("mode", "") or "").strip().lower()
    pipeline_mode = (summary_row.get("pipeline_mode", "") or "").strip().lower()
    return mode == "csv_replay_pipeline" or pipeline_mode == "pipeline"


def _build_pipeline_health_status(
    replay_bar_count: int,
    decision_log_count: int,
    real_order_sent_count: int,
    no_real_order_integrity_violation_count: int,
    pipeline_adapter_error_count: int,
    ordinary_missing_bar_gap_count: int,
    unknown_gap_count: int,
    duplicate_bar_count: int,
    out_of_order_count: int,
) -> tuple[str, str]:
    if (
        real_order_sent_count > 0
        or no_real_order_integrity_violation_count > 0
        or decision_log_count != replay_bar_count
    ):
        if real_order_sent_count > 0:
            return "fail", "real_order_sent_detected"
        if no_real_order_integrity_violation_count > 0:
            return "fail", "no_real_order_integrity_violation_detected"
        return "fail", "decision_log_count_mismatch"

    if (
        pipeline_adapter_error_count > 0
        or ordinary_missing_bar_gap_count > 0
        or unknown_gap_count > 0
        or duplicate_bar_count > 0
        or out_of_order_count > 0
    ):
        if pipeline_adapter_error_count > 0:
            return "warn", "pipeline_adapter_error_detected"
        if ordinary_missing_bar_gap_count > 0:
            return "warn", "ordinary_missing_bar_gap_detected"
        if unknown_gap_count > 0:
            return "warn", "unknown_gap_detected"
        if duplicate_bar_count > 0:
            return "warn", "duplicate_bar_detected"
        return "warn", "out_of_order_detected"

    return "pass", "pipeline_health_ok"


def summarize(input_dir: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    summary_path = input_dir / "near_live_summary.csv"
    warnings_path = input_dir / "near_live_validation_warnings.csv"
    _require_file(summary_path)
    _require_file(warnings_path)

    summary_rows = _read_csv_rows(summary_path)
    if not summary_rows:
        raise ValueError(f"near_live_summary.csv has no rows: {summary_path}")
    summary_row = summary_rows[0]
    warning_rows = _read_csv_rows(warnings_path)
    decision_logs_path = input_dir / "near_live_decision_logs.csv"
    decision_rows: list[dict[str, str]] = []
    if decision_logs_path.exists():
        decision_rows = _read_csv_rows(decision_logs_path)
    reason_category_metrics = _build_reason_category_metrics(decision_rows)

    run_id = summary_row.get("run_id", "")
    mode = summary_row.get("mode", "csv_replay")
    is_pipeline_mode = _is_pipeline_mode(summary_row)
    replay_bar_count = _to_int(summary_row, "replay_bar_count")
    decision_log_count = _to_int(summary_row, "decision_log_count")
    warning_count = _to_int(summary_row, "warning_count")
    duplicate_bar_count = _to_int(summary_row, "duplicate_bar_count")
    out_of_order_count = _to_int(summary_row, "out_of_order_count")
    data_gap_count = _to_int(summary_row, "data_gap_count")
    expected_weekend_gap_count = _to_int(summary_row, "expected_weekend_gap_count")
    ordinary_missing_bar_gap_count = _to_int(summary_row, "ordinary_missing_bar_gap_count")
    unknown_gap_count = _to_int(summary_row, "unknown_gap_count")
    pipeline_adapter_error_count = _to_int(summary_row, "pipeline_adapter_error_count")
    pipeline_adapter_called_count = _to_int(summary_row, "pipeline_adapter_called_count")
    pipeline_adapter_skipped_count = _to_int(summary_row, "pipeline_adapter_skipped_count")
    paper_order_candidate_count = _to_int(summary_row, "paper_order_candidate_count")
    real_order_sent_count = _to_int(summary_row, "real_order_sent_count")
    no_real_order_integrity_violation_count = _to_int(summary_row, "no_real_order_integrity_violation_count")
    placeholder_integrity_checked = decision_logs_path.exists()

    entry_signal_true_count = 0
    exit_signal_true_count = 0
    trade_ok_true_count = 0
    paper_order_action_non_none_count = 0
    paper_position_state_non_flat_count = 0
    placeholder_violation_count = 0

    if placeholder_integrity_checked:
        for row in decision_rows:
            entry_signal_is_true = _is_true(row.get("entry_signal", ""))
            exit_signal_is_true = _is_true(row.get("exit_signal", ""))
            trade_ok_is_true = _is_true(row.get("trade_ok", ""))
            paper_order_action_is_non_none = not _is_none_text(row.get("paper_order_action", ""))
            paper_position_state_is_non_flat = not _is_flat_text(row.get("paper_position_state", ""))

            if entry_signal_is_true:
                entry_signal_true_count += 1
            if exit_signal_is_true:
                exit_signal_true_count += 1
            if trade_ok_is_true:
                trade_ok_true_count += 1
            if paper_order_action_is_non_none:
                paper_order_action_non_none_count += 1
            if paper_position_state_is_non_flat:
                paper_position_state_non_flat_count += 1

            if (
                entry_signal_is_true
                or exit_signal_is_true
                or trade_ok_is_true
                or paper_order_action_is_non_none
                or paper_position_state_is_non_flat
            ):
                placeholder_violation_count += 1

    placeholder_integrity_ok = placeholder_violation_count == 0 if placeholder_integrity_checked else False
    placeholder_integrity_ok_text = _to_bool_str(placeholder_integrity_ok) if placeholder_integrity_checked else "not_checked"

    if is_pipeline_mode:
        dry_run_health_status, status_reason = _build_pipeline_health_status(
            replay_bar_count=replay_bar_count,
            decision_log_count=decision_log_count,
            real_order_sent_count=real_order_sent_count,
            no_real_order_integrity_violation_count=no_real_order_integrity_violation_count,
            pipeline_adapter_error_count=pipeline_adapter_error_count,
            ordinary_missing_bar_gap_count=ordinary_missing_bar_gap_count,
            unknown_gap_count=unknown_gap_count,
            duplicate_bar_count=duplicate_bar_count,
            out_of_order_count=out_of_order_count,
        )
        data_quality_status = dry_run_health_status
    else:
        dry_run_health_status, data_quality_status, status_reason = _build_status(
            replay_bar_count=replay_bar_count,
            decision_log_count=decision_log_count,
            warning_count=warning_count,
            duplicate_bar_count=duplicate_bar_count,
            out_of_order_count=out_of_order_count,
            ordinary_missing_bar_gap_count=ordinary_missing_bar_gap_count,
            unknown_gap_count=unknown_gap_count,
            placeholder_integrity_checked=placeholder_integrity_checked,
            placeholder_integrity_ok=placeholder_integrity_ok,
            warning_rows=warning_rows,
        )
    period_summary = {
        "run_id": run_id,
        "mode": mode,
        "replay_bar_count": str(replay_bar_count),
        "decision_log_count": str(decision_log_count),
        "warning_count": str(warning_count),
        "duplicate_bar_count": str(duplicate_bar_count),
        "out_of_order_count": str(out_of_order_count),
        "data_gap_count": str(data_gap_count),
        "expected_weekend_gap_count": str(expected_weekend_gap_count),
        "ordinary_missing_bar_gap_count": str(ordinary_missing_bar_gap_count),
        "unknown_gap_count": str(unknown_gap_count),
        "placeholder_integrity_checked": _to_bool_str(placeholder_integrity_checked),
        "placeholder_integrity_ok": placeholder_integrity_ok_text,
        "placeholder_violation_count": str(placeholder_violation_count),
        "entry_signal_true_count": str(entry_signal_true_count),
        "exit_signal_true_count": str(exit_signal_true_count),
        "trade_ok_true_count": str(trade_ok_true_count),
        "paper_order_action_non_none_count": str(paper_order_action_non_none_count),
        "paper_position_state_non_flat_count": str(paper_position_state_non_flat_count),
        "log_completeness_ok": _to_bool_str(decision_log_count == replay_bar_count),
        "data_quality_status": data_quality_status,
        "dry_run_health_status": dry_run_health_status,
        "status_reason": status_reason,
        "pipeline_adapter_error_count": str(pipeline_adapter_error_count),
        "pipeline_adapter_called_count": str(pipeline_adapter_called_count),
        "pipeline_adapter_skipped_count": str(pipeline_adapter_skipped_count),
        "paper_order_candidate_count": str(paper_order_candidate_count),
        "real_order_sent_count": str(real_order_sent_count),
        "no_real_order_integrity_violation_count": str(no_real_order_integrity_violation_count),
        "risk_reason_category_counts": str(reason_category_metrics["risk_reason_category_counts"]),
        "filter_reason_category_counts": str(reason_category_metrics["filter_reason_category_counts"]),
        "risk_reason_primary_category_counts": str(reason_category_metrics["risk_reason_primary_category_counts"]),
        "filter_reason_primary_category_counts": str(reason_category_metrics["filter_reason_primary_category_counts"]),
        "risk_reason_unknown_count": str(reason_category_metrics["risk_reason_unknown_count"]),
        "filter_reason_unknown_count": str(reason_category_metrics["filter_reason_unknown_count"]),
    }

    warning_summary_rows: list[dict[str, str]] = []
    warning_summary_rows.extend(_count_by(warning_rows, "warning_type", _normalize_text))
    warning_summary_rows.extend(_count_by(warning_rows, "gap_class", _normalize_text))
    warning_summary_rows.extend(_count_by(warning_rows, "expected_gap_flag", _bool_text))
    warning_summary_rows.extend(_count_by(warning_rows, "gap_requires_investigation", _bool_text))
    return period_summary, warning_summary_rows


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(output_dir: Path, period_summary: dict[str, str], warning_summary: list[dict[str, str]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "dry_run_period_summary.csv", [period_summary], PERIOD_SUMMARY_FIELDS)
    _write_csv(
        output_dir / "dry_run_warning_summary.csv",
        warning_summary,
        ["summary_type", "value", "count"],
    )

    md_lines = [
        "# dry-run period summary",
        "",
        "- 収益性確認ではない",
        "- OANDA/API接続なし",
        "- 実注文・デモ注文なし",
        "- 二次summary（near_live_summary.csv を読み取る検証用summary）",
        "- dry-run安全性とログ整合性の確認であり、passは収益性や実運用品質を意味しない",
        "- warn は調査候補であり、必ずしも即failではない",
        "- expected_weekend_gap 単独は原則 pass を許容する",
        "- health意味: pass=主要整合OK / warn=調査候補あり / fail=実注文送信または整合性破綻",
        f"- run_id: {period_summary['run_id']}",
        f"- mode: {period_summary['mode']}",
        f"- replay_bar_count: {period_summary['replay_bar_count']}",
        f"- decision_log_count: {period_summary['decision_log_count']}",
        f"- log_completeness_ok: {period_summary['log_completeness_ok']}",
        f"- real_order_sent_count: {period_summary['real_order_sent_count']}",
        f"- no_real_order_integrity_violation_count: {period_summary['no_real_order_integrity_violation_count']}",
        f"- risk_reason_category_counts: {period_summary['risk_reason_category_counts']}",
        f"- filter_reason_category_counts: {period_summary['filter_reason_category_counts']}",
        f"- risk_reason_primary_category_counts: {period_summary['risk_reason_primary_category_counts']}",
        f"- filter_reason_primary_category_counts: {period_summary['filter_reason_primary_category_counts']}",
        f"- risk_reason_unknown_count: {period_summary['risk_reason_unknown_count']}",
        f"- filter_reason_unknown_count: {period_summary['filter_reason_unknown_count']}",
        f"- pipeline_adapter_error_count: {period_summary['pipeline_adapter_error_count']}",
        f"- warning_count: {period_summary['warning_count']}",
        f"- expected_weekend_gap_count: {period_summary['expected_weekend_gap_count']}",
        f"- ordinary_missing_bar_gap_count: {period_summary['ordinary_missing_bar_gap_count']}",
        f"- unknown_gap_count: {period_summary['unknown_gap_count']}",
        f"- dry_run_health_status: {period_summary['dry_run_health_status']}",
        f"- status_reason: {period_summary['status_reason']}",
    ]
    (output_dir / "dry_run_period_summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    period_summary, warning_summary = summarize(input_dir)
    write_outputs(output_dir, period_summary, warning_summary)
    print(f"[summary] run_id={period_summary['run_id']}")
    print(f"[summary] dry_run_health_status={period_summary['dry_run_health_status']}")
    print(f"[summary] output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
