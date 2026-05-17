#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from src.risk_filter.lot_sizing_calculator import LotSizingCalculator
from src.risk_filter.lot_sizing_calculator import LotSizingV1Config


ROW_FIELDS = [
    "row_index",
    "fixed_lot",
    "account_balance",
    "risk_per_trade",
    "stop_loss_distance_pips",
    "pip_value_per_lot",
    "risk_based_raw_lot",
    "risk_based_rounded_lot",
    "risk_based_effective_lot",
    "risk_based_lot_sizing_reason",
    "risk_based_clamped_flag",
    "risk_lot_valid_flag",
    "lot_size_diff",
    "lot_size_ratio",
]

SUMMARY_FIELDS = [
    "row_count",
    "valid_risk_lot_count",
    "invalid_risk_lot_count",
    "clamped_count",
    "below_min_count",
    "invalid_input_count",
    "average_lot_size_diff",
    "average_lot_size_ratio",
    "max_lot_size_diff",
    "min_lot_size_diff",
    "risk_based_lot_reason_counts",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline Lot Sizing v1 shadow comparison tool.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fixed-lot", required=True, type=float)
    parser.add_argument("--account-balance", required=True, type=float)
    parser.add_argument("--risk-per-trade", required=True, type=float)
    parser.add_argument("--pip-value-per-lot", required=True, type=float)
    parser.add_argument("--lot-step", required=True, type=float)
    parser.add_argument("--min-lot", required=True, type=float)
    parser.add_argument("--max-lot", required=True, type=float)
    parser.add_argument("--rounding-mode", required=True)
    parser.add_argument("--stop-loss-distance-pips", required=False, type=float, default=None)
    return parser.parse_args()


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _to_float_or_none(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _format_float(v: float | None) -> str:
    if v is None:
        return ""
    return str(v)


def _get_stop_loss_distance_pips(row: dict[str, str], fallback: float | None) -> float:
    from_row = _to_float_or_none(row.get("stop_loss_distance_pips"))
    if from_row is not None:
        return from_row
    if fallback is not None:
        return float(fallback)
    raise ValueError("stop_loss_distance_pips is required via CSV column or --stop-loss-distance-pips")


def compare_shadow(
    *,
    input_csv: Path,
    output_dir: Path,
    fixed_lot: float,
    account_balance: float,
    risk_per_trade: float,
    pip_value_per_lot: float,
    lot_step: float,
    min_lot: float,
    max_lot: float,
    rounding_mode: str,
    stop_loss_distance_pips_fallback: float | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _read_csv_rows(input_csv)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    clamped_count = 0
    valid_count = 0
    below_min_count = 0
    invalid_input_count = 0
    diffs: list[float] = []
    ratios: list[float] = []

    for i, row in enumerate(rows):
        sl_distance = _get_stop_loss_distance_pips(row, stop_loss_distance_pips_fallback)
        result = LotSizingCalculator.calculate(
            LotSizingV1Config(
                account_balance=account_balance,
                risk_per_trade=risk_per_trade,
                stop_loss_distance_pips=sl_distance,
                pip_value_per_lot=pip_value_per_lot,
                lot_step=lot_step,
                min_lot=min_lot,
                max_lot=max_lot,
                rounding_mode=rounding_mode,
            )
        )
        reason_counts[result.size_reason] += 1
        if result.clamped_flag:
            clamped_count += 1
        if result.size_reason == "invalid_lot_sizing_input: below_min_lot":
            below_min_count += 1
        if result.size_reason.startswith("invalid_lot_sizing_input:"):
            invalid_input_count += 1

        valid = result.lot is not None
        lot_size_diff: float | None = None
        lot_size_ratio: float | None = None
        if valid:
            valid_count += 1
            if fixed_lot > 0:
                lot_size_diff = result.lot - fixed_lot
                lot_size_ratio = result.lot / fixed_lot
                diffs.append(lot_size_diff)
                ratios.append(lot_size_ratio)

        out_rows.append(
            {
                "row_index": i,
                "fixed_lot": fixed_lot,
                "account_balance": account_balance,
                "risk_per_trade": risk_per_trade,
                "stop_loss_distance_pips": sl_distance,
                "pip_value_per_lot": pip_value_per_lot,
                "risk_based_raw_lot": _format_float(result.raw_lot),
                "risk_based_rounded_lot": _format_float(result.rounded_lot),
                "risk_based_effective_lot": _format_float(result.lot),
                "risk_based_lot_sizing_reason": result.size_reason,
                "risk_based_clamped_flag": str(result.clamped_flag),
                "risk_lot_valid_flag": str(valid),
                "lot_size_diff": _format_float(lot_size_diff),
                "lot_size_ratio": _format_float(lot_size_ratio),
            }
        )

    summary: dict[str, Any] = {
        "row_count": len(rows),
        "valid_risk_lot_count": valid_count,
        "invalid_risk_lot_count": len(rows) - valid_count,
        "clamped_count": clamped_count,
        "below_min_count": below_min_count,
        "invalid_input_count": invalid_input_count,
        "average_lot_size_diff": (sum(diffs) / len(diffs)) if diffs else "",
        "average_lot_size_ratio": (sum(ratios) / len(ratios)) if ratios else "",
        "max_lot_size_diff": max(diffs) if diffs else "",
        "min_lot_size_diff": min(diffs) if diffs else "",
        "risk_based_lot_reason_counts": dict(reason_counts),
    }

    _write_csv(output_dir / "lot_sizing_shadow_rows.csv", ROW_FIELDS, out_rows)
    _write_csv(output_dir / "lot_sizing_shadow_summary.csv", SUMMARY_FIELDS, [summary])
    _write_summary_md(output_dir / "lot_sizing_shadow_summary.md", summary)
    return out_rows, summary


def _write_summary_md(path: Path, summary: dict[str, Any]) -> None:
    lines = ["# lot_sizing_shadow_summary", ""]
    for k in SUMMARY_FIELDS:
        lines.append(f"- {k}: {summary.get(k, '')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    compare_shadow(
        input_csv=Path(args.input_csv),
        output_dir=Path(args.output_dir),
        fixed_lot=args.fixed_lot,
        account_balance=args.account_balance,
        risk_per_trade=args.risk_per_trade,
        pip_value_per_lot=args.pip_value_per_lot,
        lot_step=args.lot_step,
        min_lot=args.min_lot,
        max_lot=args.max_lot,
        rounding_mode=args.rounding_mode,
        stop_loss_distance_pips_fallback=args.stop_loss_distance_pips,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
