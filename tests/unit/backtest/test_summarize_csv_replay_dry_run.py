from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

from scripts.summarize_csv_replay_dry_run import main
from scripts.summarize_csv_replay_dry_run import _build_reason_category_metrics
from scripts.summarize_csv_replay_dry_run import parse_args
from scripts.summarize_csv_replay_dry_run import summarize


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_minimal_inputs(base_dir: Path, summary_row: dict[str, object], warning_rows: list[dict[str, object]]) -> None:
    _write_csv(base_dir / "near_live_summary.csv", [summary_row])
    _write_csv(base_dir / "near_live_validation_warnings.csv", warning_rows)


def _write_decision_logs(base_dir: Path, rows: list[dict[str, object]]) -> None:
    _write_csv(base_dir / "near_live_decision_logs.csv", rows)


def _pipeline_summary_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "r_pipeline",
        "mode": "csv_replay_pipeline",
        "replay_bar_count": 10,
        "decision_log_count": 10,
        "warning_count": 0,
        "duplicate_bar_count": 0,
        "out_of_order_count": 0,
        "data_gap_count": 0,
        "expected_weekend_gap_count": 0,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
        "pipeline_adapter_called_count": 10,
        "pipeline_adapter_error_count": 0,
        "pipeline_adapter_skipped_count": 0,
        "entry_signal_true_count": 0,
        "trade_ok_true_count": 0,
        "paper_order_candidate_count": 0,
        "real_order_sent_count": 0,
        "no_real_order_integrity_violation_count": 0,
    }
    row.update(overrides)
    return row


def test_parse_args() -> None:
    old = sys.argv
    try:
        sys.argv = [
            "summarize_csv_replay_dry_run.py",
            "--input-dir",
            "in",
            "--output-dir",
            "out",
        ]
        args = parse_args()
    finally:
        sys.argv = old
    assert args.input_dir == "in"
    assert args.output_dir == "out"


def test_summarize_warn_for_expected_weekend_only(tmp_path: Path) -> None:
    summary_row = {
        "run_id": "r_weekend",
        "mode": "csv_replay",
        "replay_bar_count": 100,
        "decision_log_count": 100,
        "warning_count": 1,
        "duplicate_bar_count": 0,
        "out_of_order_count": 0,
        "data_gap_count": 1,
        "expected_weekend_gap_count": 1,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
    }
    warning_rows = [
        {
            "timestamp": "2024-01-07T17:05:00+00:00",
            "warning_type": "data_gap",
            "severity": "warning",
            "message": "gap",
            "gap_class": "expected_weekend_gap",
            "expected_gap_flag": "True",
            "gap_duration": "2 days 00:10:00",
            "previous_timestamp": "2024-01-05T16:55:00+00:00",
            "current_timestamp": "2024-01-07T17:05:00+00:00",
            "gap_reason": "weekend_or_market_closure_candidate",
            "gap_action": "record_as_expected_gap",
            "gap_requires_investigation": "False",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    _write_decision_logs(
        tmp_path,
        [
            {
                "timestamp": "2024-01-03T00:00:00+00:00",
                "entry_signal": "False",
                "exit_signal": "False",
                "trade_ok": "False",
                "paper_order_action": "none",
                "paper_position_state": "flat",
            }
        ],
    )

    period_summary, warning_summary = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "warn"
    assert period_summary["status_reason"] == "expected_weekend_gap_only"
    assert period_summary["log_completeness_ok"] == "True"
    assert period_summary["placeholder_integrity_checked"] == "True"
    assert period_summary["placeholder_integrity_ok"] == "True"
    assert period_summary["placeholder_violation_count"] == "0"

    entries = {(r["summary_type"], r["value"]): int(r["count"]) for r in warning_summary}
    assert entries[("warning_type", "data_gap")] == 1
    assert entries[("gap_class", "expected_weekend_gap")] == 1
    assert entries[("expected_gap_flag", "true")] == 1
    assert entries[("gap_requires_investigation", "false")] == 1


def test_summarize_investigate_for_duplicate(tmp_path: Path) -> None:
    summary_row = {
        "run_id": "r_dup",
        "mode": "csv_replay",
        "replay_bar_count": 100,
        "decision_log_count": 100,
        "warning_count": 1,
        "duplicate_bar_count": 1,
        "out_of_order_count": 0,
        "data_gap_count": 0,
        "expected_weekend_gap_count": 0,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
    }
    warning_rows = [
        {
            "timestamp": "2024-01-01T00:10:00+00:00",
            "warning_type": "duplicate_timestamp",
            "severity": "warning",
            "message": "duplicate",
            "gap_class": "",
            "expected_gap_flag": "",
            "gap_duration": "",
            "previous_timestamp": "",
            "current_timestamp": "2024-01-01T00:10:00+00:00",
            "gap_reason": "",
            "gap_action": "",
            "gap_requires_investigation": "",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    _write_decision_logs(
        tmp_path,
        [
            {
                "timestamp": "2024-01-01T00:10:00+00:00",
                "entry_signal": "False",
                "exit_signal": "False",
                "trade_ok": "False",
                "paper_order_action": "none",
                "paper_position_state": "flat",
            }
        ],
    )
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "investigate"
    assert period_summary["data_quality_status"] == "investigate"


def test_summarize_no_go_for_log_mismatch(tmp_path: Path) -> None:
    summary_row = {
        "run_id": "r_ng",
        "mode": "csv_replay",
        "replay_bar_count": 100,
        "decision_log_count": 99,
        "warning_count": 0,
        "duplicate_bar_count": 0,
        "out_of_order_count": 0,
        "data_gap_count": 0,
        "expected_weekend_gap_count": 0,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
    }
    warning_rows = [
        {
            "timestamp": "",
            "warning_type": "",
            "severity": "",
            "message": "",
            "gap_class": "",
            "expected_gap_flag": "",
            "gap_duration": "",
            "previous_timestamp": "",
            "current_timestamp": "",
            "gap_reason": "",
            "gap_action": "",
            "gap_requires_investigation": "",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "no_go_candidate"
    assert period_summary["status_reason"] == "decision_log_count_mismatch"
    assert period_summary["log_completeness_ok"] == "False"


def test_main_writes_outputs(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir(parents=True, exist_ok=True)
    summary_row = {
        "run_id": "r_pass",
        "mode": "csv_replay",
        "replay_bar_count": 10,
        "decision_log_count": 10,
        "warning_count": 0,
        "duplicate_bar_count": 0,
        "out_of_order_count": 0,
        "data_gap_count": 0,
        "expected_weekend_gap_count": 0,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
    }
    warning_rows = [
        {
            "timestamp": "",
            "warning_type": "",
            "severity": "",
            "message": "",
            "gap_class": "",
            "expected_gap_flag": "",
            "gap_duration": "",
            "previous_timestamp": "",
            "current_timestamp": "",
            "gap_reason": "",
            "gap_action": "",
            "gap_requires_investigation": "",
        }
    ]
    _write_minimal_inputs(input_dir, summary_row, warning_rows)
    _write_decision_logs(
        input_dir,
        [
            {
                "timestamp": "2024-01-01T00:00:00+00:00",
                "entry_signal": "False",
                "exit_signal": "False",
                "trade_ok": "False",
                "paper_order_action": "none",
                "paper_position_state": "flat",
            }
        ],
    )

    old = sys.argv
    try:
        sys.argv = [
            "summarize_csv_replay_dry_run.py",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ]
        rc = main()
    finally:
        sys.argv = old
    assert rc == 0
    assert (output_dir / "dry_run_period_summary.csv").exists()
    assert (output_dir / "dry_run_period_summary.md").exists()
    assert (output_dir / "dry_run_warning_summary.csv").exists()


def test_missing_required_input_files_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="required input file not found"):
        summarize(tmp_path)


def test_placeholder_integrity_no_go_for_entry_signal_true(tmp_path: Path) -> None:
    summary_row = {
        "run_id": "r_entry_true",
        "mode": "csv_replay",
        "replay_bar_count": 10,
        "decision_log_count": 10,
        "warning_count": 0,
        "duplicate_bar_count": 0,
        "out_of_order_count": 0,
        "data_gap_count": 0,
        "expected_weekend_gap_count": 0,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
    }
    warning_rows = [
        {
            "timestamp": "",
            "warning_type": "",
            "severity": "",
            "message": "",
            "gap_class": "",
            "expected_gap_flag": "",
            "gap_duration": "",
            "previous_timestamp": "",
            "current_timestamp": "",
            "gap_reason": "",
            "gap_action": "",
            "gap_requires_investigation": "",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    _write_decision_logs(
        tmp_path,
        [
            {
                "timestamp": "2024-01-01T00:00:00+00:00",
                "entry_signal": "True",
                "exit_signal": "False",
                "trade_ok": "False",
                "paper_order_action": "none",
                "paper_position_state": "flat",
            }
        ],
    )

    period_summary, _ = summarize(tmp_path)
    assert period_summary["placeholder_integrity_checked"] == "True"
    assert period_summary["placeholder_integrity_ok"] == "False"
    assert period_summary["entry_signal_true_count"] == "1"
    assert int(period_summary["placeholder_violation_count"]) >= 1
    assert period_summary["dry_run_health_status"] == "no_go_candidate"
    assert period_summary["status_reason"] == "placeholder_integrity_violation"


def test_placeholder_integrity_no_go_for_paper_order_action_non_none(tmp_path: Path) -> None:
    summary_row = {
        "run_id": "r_order_action",
        "mode": "csv_replay",
        "replay_bar_count": 10,
        "decision_log_count": 10,
        "warning_count": 0,
        "duplicate_bar_count": 0,
        "out_of_order_count": 0,
        "data_gap_count": 0,
        "expected_weekend_gap_count": 0,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
    }
    warning_rows = [
        {
            "timestamp": "",
            "warning_type": "",
            "severity": "",
            "message": "",
            "gap_class": "",
            "expected_gap_flag": "",
            "gap_duration": "",
            "previous_timestamp": "",
            "current_timestamp": "",
            "gap_reason": "",
            "gap_action": "",
            "gap_requires_investigation": "",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    _write_decision_logs(
        tmp_path,
        [
            {
                "timestamp": "2024-01-01T00:00:00+00:00",
                "entry_signal": "False",
                "exit_signal": "False",
                "trade_ok": "False",
                "paper_order_action": "submit_long",
                "paper_position_state": "flat",
            }
        ],
    )

    period_summary, _ = summarize(tmp_path)
    assert period_summary["paper_order_action_non_none_count"] == "1"
    assert period_summary["dry_run_health_status"] == "no_go_candidate"
    assert period_summary["status_reason"] == "placeholder_integrity_violation"


def test_placeholder_integrity_not_checked_when_decision_logs_missing(tmp_path: Path) -> None:
    summary_row = {
        "run_id": "r_no_decision_logs",
        "mode": "csv_replay",
        "replay_bar_count": 10,
        "decision_log_count": 10,
        "warning_count": 0,
        "duplicate_bar_count": 0,
        "out_of_order_count": 0,
        "data_gap_count": 0,
        "expected_weekend_gap_count": 0,
        "ordinary_missing_bar_gap_count": 0,
        "unknown_gap_count": 0,
    }
    warning_rows = [
        {
            "timestamp": "",
            "warning_type": "",
            "severity": "",
            "message": "",
            "gap_class": "",
            "expected_gap_flag": "",
            "gap_duration": "",
            "previous_timestamp": "",
            "current_timestamp": "",
            "gap_reason": "",
            "gap_action": "",
            "gap_requires_investigation": "",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)

    period_summary, _ = summarize(tmp_path)
    assert period_summary["placeholder_integrity_checked"] == "False"
    assert period_summary["placeholder_integrity_ok"] == "not_checked"
    assert period_summary["dry_run_health_status"] == "pass"


def test_pipeline_health_pass(tmp_path: Path) -> None:
    summary_row = _pipeline_summary_row()
    warning_rows = [
        {
            "timestamp": "",
            "warning_type": "",
            "severity": "",
            "message": "",
            "gap_class": "",
            "expected_gap_flag": "",
            "gap_duration": "",
            "previous_timestamp": "",
            "current_timestamp": "",
            "gap_reason": "",
            "gap_action": "",
            "gap_requires_investigation": "",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    _write_decision_logs(
        tmp_path,
        [{"timestamp": "2024-01-01T00:00:00+00:00", "paper_order_action": "none", "paper_position_state": "flat"}],
    )
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "pass"


def test_pipeline_health_fail_on_integrity_violation_count(tmp_path: Path) -> None:
    summary_row = _pipeline_summary_row(no_real_order_integrity_violation_count=1)
    warning_rows = [
        {"timestamp": "", "warning_type": "", "severity": "", "message": "", "gap_class": "", "expected_gap_flag": "", "gap_duration": "", "previous_timestamp": "", "current_timestamp": "", "gap_reason": "", "gap_action": "", "gap_requires_investigation": ""}
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "fail"
    assert period_summary["status_reason"] == "no_real_order_integrity_violation_detected"


def test_pipeline_health_fail_on_real_order_sent(tmp_path: Path) -> None:
    summary_row = _pipeline_summary_row(real_order_sent_count=1)
    warning_rows = [
        {"timestamp": "", "warning_type": "", "severity": "", "message": "", "gap_class": "", "expected_gap_flag": "", "gap_duration": "", "previous_timestamp": "", "current_timestamp": "", "gap_reason": "", "gap_action": "", "gap_requires_investigation": ""}
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "fail"
    assert period_summary["status_reason"] == "real_order_sent_detected"


def test_pipeline_health_warn_on_pipeline_adapter_error(tmp_path: Path) -> None:
    summary_row = _pipeline_summary_row(pipeline_adapter_error_count=2)
    warning_rows = [
        {"timestamp": "", "warning_type": "", "severity": "", "message": "", "gap_class": "", "expected_gap_flag": "", "gap_duration": "", "previous_timestamp": "", "current_timestamp": "", "gap_reason": "", "gap_action": "", "gap_requires_investigation": ""}
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "warn"
    assert period_summary["status_reason"] == "pipeline_adapter_error_detected"


def test_pipeline_health_warn_on_ordinary_missing_gap(tmp_path: Path) -> None:
    summary_row = _pipeline_summary_row(ordinary_missing_bar_gap_count=1, warning_count=1, data_gap_count=1)
    warning_rows = [
        {"timestamp": "2024-01-01T00:10:00+00:00", "warning_type": "data_gap", "severity": "warning", "message": "gap", "gap_class": "ordinary_missing_bar_gap", "expected_gap_flag": "False", "gap_duration": "0:10:00", "previous_timestamp": "2024-01-01T00:00:00+00:00", "current_timestamp": "2024-01-01T00:10:00+00:00", "gap_reason": "missing_bar_candidate", "gap_action": "investigate_missing_bars", "gap_requires_investigation": "True"}
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "warn"
    assert period_summary["status_reason"] == "ordinary_missing_bar_gap_detected"


def test_pipeline_health_fail_on_decision_log_mismatch(tmp_path: Path) -> None:
    summary_row = _pipeline_summary_row(decision_log_count=9)
    warning_rows = [
        {"timestamp": "", "warning_type": "", "severity": "", "message": "", "gap_class": "", "expected_gap_flag": "", "gap_duration": "", "previous_timestamp": "", "current_timestamp": "", "gap_reason": "", "gap_action": "", "gap_requires_investigation": ""}
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "fail"
    assert period_summary["status_reason"] == "decision_log_count_mismatch"


def test_pipeline_health_pass_for_expected_weekend_gap_only(tmp_path: Path) -> None:
    summary_row = _pipeline_summary_row(
        warning_count=1,
        data_gap_count=1,
        expected_weekend_gap_count=1,
    )
    warning_rows = [
        {
            "timestamp": "2024-01-07T17:05:00+00:00",
            "warning_type": "data_gap",
            "severity": "warning",
            "message": "gap",
            "gap_class": "expected_weekend_gap",
            "expected_gap_flag": "True",
            "gap_duration": "2 days 00:10:00",
            "previous_timestamp": "2024-01-05T16:55:00+00:00",
            "current_timestamp": "2024-01-07T17:05:00+00:00",
            "gap_reason": "weekend_or_market_closure_candidate",
            "gap_action": "record_as_expected_gap",
            "gap_requires_investigation": "False",
        }
    ]
    _write_minimal_inputs(tmp_path, summary_row, warning_rows)
    period_summary, _ = summarize(tmp_path)
    assert period_summary["dry_run_health_status"] == "pass"


def test_build_reason_category_metrics_filter_and_risk_with_unknown_handling() -> None:
    rows = [
        {
            "filter_reason": "all risk filters passed",
            "risk_reason": "fixed_sl_tp | placeholder_fixed_lot",
        },
        {
            "filter_reason": "risk_contract_invalid: entry_signal_false | invalid_lot: fixed_lot=0",
            "risk_reason": None,
        },
        {
            "filter_reason": " ",
            "risk_reason": "",
        },
    ]

    metrics = _build_reason_category_metrics(rows)

    assert metrics["filter_reason_category_counts"]["all_risk_filters_passed"] == 1
    assert metrics["filter_reason_primary_category_counts"]["all_risk_filters_passed"] == 1
    assert metrics["filter_reason_category_counts"]["risk_contract_invalid"] == 1
    assert metrics["filter_reason_category_counts"]["invalid_lot"] == 1
    assert metrics["filter_reason_primary_category_counts"]["risk_contract_invalid"] == 1

    assert metrics["risk_reason_category_counts"]["fixed_sl_tp"] == 1
    assert metrics["risk_reason_category_counts"]["placeholder_fixed_lot"] == 1
    assert metrics["risk_reason_primary_category_counts"]["fixed_sl_tp"] == 1

    assert metrics["risk_reason_primary_category_counts"]["unknown"] == 2
    assert metrics["filter_reason_primary_category_counts"]["unknown"] == 1
    assert metrics["risk_reason_unknown_count"] == 2
    assert metrics["filter_reason_unknown_count"] == 1
    assert "none" not in metrics["risk_reason_category_counts"]
    assert "none" not in metrics["filter_reason_category_counts"]


def test_build_reason_category_metrics_risk_reason_missing_column_is_zero_count() -> None:
    rows = [
        {
            "filter_reason": "all risk filters passed",
        },
        {
            "filter_reason": "",
        },
    ]

    metrics = _build_reason_category_metrics(rows)

    assert metrics["risk_reason_category_counts"] == {}
    assert metrics["risk_reason_primary_category_counts"] == {}
    assert metrics["risk_reason_unknown_count"] == 0
    assert metrics["filter_reason_primary_category_counts"]["all_risk_filters_passed"] == 1
    assert metrics["filter_reason_primary_category_counts"]["unknown"] == 1
