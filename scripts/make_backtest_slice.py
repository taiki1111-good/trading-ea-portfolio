#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Output schema required by PriceDataLoader.
OUTPUT_COLUMNS = ["timestamp", "open", "high", "low", "close", "spread", "volume"]

# Candidate source column names (case-insensitive).
COLUMN_ALIASES: Dict[str, List[str]] = {
    "timestamp": ["timestamp", "time", "datetime", "date", "utc_time"],
    "open": ["open", "o"],
    "high": ["high", "h"],
    "low": ["low", "l"],
    "close": ["close", "c", "price"],
    "spread": ["spread", "spread_pips"],
    "volume": ["volume", "tick_volume", "vol"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a short backtest CSV slice from a large raw CSV. "
            "This is for structure checks / initial backtest checks, not profitability evaluation."
        )
    )
    parser.add_argument("--input-csv", required=True, help="Path to input CSV (e.g. data/raw/...).")
    parser.add_argument("--output-csv", required=True, help="Path to output slice CSV.")
    parser.add_argument("--start", required=True, help="UTC start (inclusive), e.g. 2024-01-01 or 2024-01-01T00:00:00Z")
    parser.add_argument("--end", required=True, help="UTC end (inclusive), e.g. 2024-01-07 or 2024-01-07T23:59:59Z")
    parser.add_argument(
        "--spread-fallback",
        type=float,
        default=0.2,
        help=(
            "Fallback spread in pips when spread column/value is missing. "
            "Default: 0.2 (allowed for structure/initial backtest only, not for operation-like runs)."
        ),
    )
    parser.add_argument(
        "--volume-fallback",
        type=float,
        default=0.0,
        help="Fallback volume when volume column/value is missing. Default: 0",
    )
    parser.add_argument("--preview-rows", type=int, default=5, help="How many head rows to print for preview.")
    return parser.parse_args()


def _normalize_name(value: str) -> str:
    return value.strip().lower()


def _parse_timestamp(value: str) -> datetime:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("timestamp is empty")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        if raw.isdigit():
            return datetime.fromtimestamp(int(raw), tz=timezone.utc)
        raise ValueError(f"unable to parse timestamp: {value}")

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _pick_columns(fieldnames: Iterable[str]) -> Dict[str, Optional[str]]:
    source = list(fieldnames)
    lowered = {_normalize_name(name): name for name in source}
    resolved: Dict[str, Optional[str]] = {}

    for target, aliases in COLUMN_ALIASES.items():
        resolved_name: Optional[str] = None
        for alias in aliases:
            if alias in lowered:
                resolved_name = lowered[alias]
                break
        resolved[target] = resolved_name

    return resolved


def _parse_bound(value: str, *, end_of_day: bool) -> datetime:
    if "T" in value:
        return _parse_timestamp(value)
    suffix = "T23:59:59Z" if end_of_day else "T00:00:00Z"
    return _parse_timestamp(value + suffix)


def main() -> int:
    args = parse_args()

    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)

    if not input_path.exists():
        raise FileNotFoundError(f"input_csv does not exist: {input_path}")

    start_dt = _parse_bound(args.start, end_of_day=False)
    end_dt = _parse_bound(args.end, end_of_day=True)
    if start_dt > end_dt:
        raise ValueError("start must be <= end")

    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("input CSV has no header")

        print("[info] input columns:", reader.fieldnames)

        resolved = _pick_columns(reader.fieldnames)
        missing_required = [
            key for key in ["timestamp", "open", "high", "low", "close"] if resolved[key] is None
        ]
        if missing_required:
            raise ValueError(
                "missing required source columns for output mapping: "
                f"{missing_required}. input columns={reader.fieldnames}"
            )

        if resolved["spread"] is None:
            print(
                "[warn] spread column is missing. Using fallback spread "
                f"{args.spread_fallback} pips for initial structure/backtest checks only."
            )
        if resolved["volume"] is None:
            print(f"[warn] volume column is missing. Using fallback volume {args.volume_fallback}.")

        print("[info] resolved column mapping:", resolved)

        preview_rows: List[dict] = []
        sliced_rows: List[dict] = []

        for raw in reader:
            if len(preview_rows) < args.preview_rows:
                preview_rows.append(raw)

            ts = _parse_timestamp(raw[resolved["timestamp"]])
            if ts < start_dt or ts > end_dt:
                continue

            spread_value: Optional[float]
            if resolved["spread"] is None:
                spread_value = args.spread_fallback
            else:
                spread_raw = (raw.get(resolved["spread"], "") or "").strip()
                spread_value = float(spread_raw) if spread_raw else args.spread_fallback

            if resolved["volume"] is None:
                volume_value = args.volume_fallback
            else:
                volume_raw = (raw.get(resolved["volume"], "") or "").strip()
                volume_value = float(volume_raw) if volume_raw else args.volume_fallback

            out = {
                "timestamp": _to_iso_z(ts),
                "open": float(raw[resolved["open"]]),
                "high": float(raw[resolved["high"]]),
                "low": float(raw[resolved["low"]]),
                "close": float(raw[resolved["close"]]),
                "spread": spread_value,
                "volume": volume_value,
            }
            sliced_rows.append(out)

    print("[info] input head rows:")
    for i, row in enumerate(preview_rows, start=1):
        print(f"  row{i}: {row}")

    if not sliced_rows:
        raise ValueError("no rows found in requested [start, end] range")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(sliced_rows)

    print(
        f"[done] wrote {len(sliced_rows)} rows to {output_path} "
        f"(range: {_to_iso_z(start_dt)} .. {_to_iso_z(end_dt)})"
    )
    print("[done] output columns:", OUTPUT_COLUMNS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
