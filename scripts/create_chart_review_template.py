#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ISSUE_CATEGORIES = [
    "entry_ok",
    "exit_too_early",
    "htf_against_entry",
    "range_noise_breakout",
    "entry_too_late",
    "sl_tp_too_fixed",
    "unclear",
]

BASE_COLUMNS = [
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
]

REVIEW_COLUMNS = [
    "visual_entry_ok",
    "visual_exit_ok",
    "issue_category",
    "issue_note",
    "priority",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create human review template CSV from mtf_chart_index.csv for visual entry/exit review."
    )
    parser.add_argument("--chart-index", required=True, help="Path to mtf_chart_index.csv")
    parser.add_argument("--output-csv", required=True, help="Path to output review template CSV")
    return parser.parse_args()


def validate_columns(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("chart index CSV has no header")
    missing = [c for c in BASE_COLUMNS if c not in fieldnames]
    if missing:
        raise ValueError(f"chart index CSV missing required columns: {missing}")


def main() -> int:
    args = parse_args()
    chart_index_path = Path(args.chart_index)
    output_csv_path = Path(args.output_csv)

    if not chart_index_path.exists():
        raise FileNotFoundError(f"chart index CSV not found: {chart_index_path}")

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    with chart_index_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        validate_columns(reader.fieldnames)
        for src in reader:
            row = {key: src.get(key, "") for key in BASE_COLUMNS}
            row.update(
                {
                    "visual_entry_ok": "",
                    "visual_exit_ok": "",
                    "issue_category": "",
                    "issue_note": "",
                    "priority": "",
                }
            )
            rows.append(row)

    output_fields = BASE_COLUMNS + REVIEW_COLUMNS
    with output_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[done] chart_index={chart_index_path}")
    print(f"[done] output_csv={output_csv_path}")
    print(f"[done] rows={len(rows)}")
    print("[issue_category_candidates] " + ", ".join(ISSUE_CATEGORIES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
