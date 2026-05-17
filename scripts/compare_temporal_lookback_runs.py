#!/usr/bin/env python
from __future__ import annotations

import argparse
import ast
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare temporal lookback backtest runs.")
    parser.add_argument(
        "--run-dir",
        action="append",
        required=True,
        help="Run directory path. Can be provided multiple times.",
    )
    parser.add_argument("--output-dir", required=True, help="Output directory for comparison files.")
    return parser.parse_args()


def _parse_iso(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _parse_lookback_from_notes(notes: str) -> int | None:
    marker = "third_candidate_lookback_bars="
    for part in str(notes).split(";"):
        item = part.strip()
        if item.startswith(marker):
            try:
                return int(item.split("=", 1)[1].strip())
            except Exception:
                return None
    return None


def _parse_max_entries_from_notes(notes: str) -> str:
    marker = "max_entries_per_recent_third_candidate="
    for part in str(notes).split(";"):
        item = part.strip()
        if item.startswith(marker):
            return item.split("=", 1)[1].strip()
    return ""


def _read_backtest_summary(summary_csv: Path) -> dict[str, str]:
    with summary_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"empty summary csv: {summary_csv}")
    return {k: str(v) for k, v in rows[0].items()}


def _read_trade_logs(trade_logs_csv: Path) -> list[dict[str, str]]:
    with trade_logs_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [{k: str(v) for k, v in row.items()} for row in reader]


def _bool_from_text(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _counter_repr(counter: Counter[str]) -> str:
    return str(dict(counter))


def _compute_run_metrics(run_dir: Path) -> dict[str, Any]:
    summary = _read_backtest_summary(run_dir / "backtest_summary.csv")
    trade_logs = _read_trade_logs(run_dir / "trade_logs.csv")

    run_id = summary.get("run_id", run_dir.name)
    lookback_bars = _parse_lookback_from_notes(summary.get("notes", ""))
    max_entries_setting = _parse_max_entries_from_notes(summary.get("notes", ""))
    total_pnl = _to_float(summary.get("total_pnl", "")) or 0.0
    average_pnl = _to_float(summary.get("average_pnl", "")) or 0.0

    signal_type_counts = Counter(row.get("signal_type", "") for row in trade_logs)
    exit_reason_counts = Counter(row.get("exit_reason", "") for row in trade_logs)
    structure_source_counts = Counter(row.get("structure_source", "") for row in trade_logs)
    long_count = int(signal_type_counts.get("long_entry", 0))
    short_count = int(signal_type_counts.get("short_entry", 0))

    fallback_used_count = sum(1 for row in trade_logs if _bool_from_text(row.get("fallback_used", "")))
    trade_count = len(trade_logs)
    fallback_used_rate = (fallback_used_count / trade_count * 100.0) if trade_count else 0.0

    pnls = [_to_float(row.get("pnl", "")) for row in trade_logs]
    pnl_values = [v for v in pnls if v is not None]
    wins = sum(1 for v in pnl_values if v > 0)
    win_rate = (wins / len(pnl_values) * 100.0) if pnl_values else 0.0

    entry_times = [_parse_iso(row.get("entry_time", "")) for row in trade_logs]
    entry_times = [t for t in entry_times if t is not None]
    entry_time_min = min(entry_times).isoformat() if entry_times else ""
    entry_time_max = max(entry_times).isoformat() if entry_times else ""

    day_counts: Counter[str] = Counter()
    hour_counts: Counter[str] = Counter()
    for row in trade_logs:
        dt = _parse_iso(row.get("entry_time", ""))
        if dt is None:
            continue
        day_counts[dt.date().isoformat()] += 1
        hour_counts[f"{dt.hour:02d}"] += 1

    temporal_reason_count = 0
    for row in trade_logs:
        reason = row.get("entry_reason", "")
        signal_reason = row.get("signal_reason", "")
        if "temporal third_wave_break" in reason or "temporal third_wave_break" in signal_reason:
            temporal_reason_count += 1

    recent_third_counts = Counter(
        row.get("recent_third_timestamp", "").strip()
        for row in trade_logs
        if row.get("recent_third_timestamp", "").strip()
    )
    duplicate_recent_third_candidate_count = sum(1 for _, c in recent_third_counts.items() if c > 1)
    max_entries_per_recent_third_candidate = max(recent_third_counts.values()) if recent_third_counts else 0

    lag_values = []
    for row in trade_logs:
        value = row.get("temporal_lag_bars", "").strip()
        if not value:
            continue
        try:
            lag_values.append(int(float(value)))
        except Exception:
            continue
    average_temporal_lag_bars = (sum(lag_values) / len(lag_values)) if lag_values else None
    max_temporal_lag_bars = max(lag_values) if lag_values else None
    temporal_lag_bars_distribution = Counter(str(v) for v in lag_values)

    return {
        "run_id": run_id,
        "lookback_bars": lookback_bars if lookback_bars is not None else "",
        "max_entries_per_recent_third_candidate_setting": max_entries_setting,
        "trade_count": trade_count,
        "signal_type_counts": _counter_repr(signal_type_counts),
        "exit_reason_counts": _counter_repr(exit_reason_counts),
        "structure_source_counts": _counter_repr(structure_source_counts),
        "fallback_used_rate_percent": fallback_used_rate,
        "total_pnl": total_pnl,
        "average_pnl": average_pnl,
        "win_rate_percent": win_rate,
        "long_count": long_count,
        "short_count": short_count,
        "entry_time_min": entry_time_min,
        "entry_time_max": entry_time_max,
        "daily_trade_counts": _counter_repr(day_counts),
        "hourly_trade_counts": _counter_repr(hour_counts),
        "temporal_reason_count": temporal_reason_count,
        "duplicate_recent_third_candidate_count": duplicate_recent_third_candidate_count,
        "max_entries_per_recent_third_candidate": max_entries_per_recent_third_candidate,
        "average_temporal_lag_bars": average_temporal_lag_bars,
        "max_temporal_lag_bars": max_temporal_lag_bars,
        "temporal_lag_bars_distribution": _counter_repr(temporal_lag_bars_distribution),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "run_id",
        "lookback_bars",
        "max_entries_per_recent_third_candidate_setting",
        "trade_count",
        "long_count",
        "short_count",
        "win_rate_percent",
        "total_pnl",
        "average_pnl",
        "fallback_used_rate_percent",
        "signal_type_counts",
        "exit_reason_counts",
        "structure_source_counts",
        "entry_time_min",
        "entry_time_max",
        "daily_trade_counts",
        "hourly_trade_counts",
        "temporal_reason_count",
        "duplicate_recent_third_candidate_count",
        "max_entries_per_recent_third_candidate",
        "average_temporal_lag_bars",
        "max_temporal_lag_bars",
        "temporal_lag_bars_distribution",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Temporal Lookback Comparison",
        "",
        "## 注意書き",
        "- これは収益性評価ではない",
        "- spread=0.2 pips fallback 前提",
        "- 手数料・スリッページ・スワップ未反映",
        "- lookback は構造接続仕様の比較であり、最適化確定ではない",
        "- 期間は1週間のみ",
        "",
        "## Runs",
    ]
    for row in rows:
        lines.extend(
            [
                f"- run_id: {row['run_id']}",
                f"  - lookback_bars: {row['lookback_bars']}",
                f"  - trade_count: {row['trade_count']}",
                f"  - max_entries_per_recent_third_candidate_setting: {row['max_entries_per_recent_third_candidate_setting']}",
                f"  - long_count: {row['long_count']}",
                f"  - short_count: {row['short_count']}",
                f"  - win_rate_percent: {row['win_rate_percent']}",
                f"  - total_pnl: {row['total_pnl']}",
                f"  - average_pnl: {row['average_pnl']}",
                f"  - fallback_used_rate_percent: {row['fallback_used_rate_percent']}",
                f"  - signal_type_counts: {row['signal_type_counts']}",
                f"  - exit_reason_counts: {row['exit_reason_counts']}",
                f"  - structure_source_counts: {row['structure_source_counts']}",
                f"  - entry_time_min: {row['entry_time_min']}",
                f"  - entry_time_max: {row['entry_time_max']}",
                f"  - daily_trade_counts: {row['daily_trade_counts']}",
                f"  - hourly_trade_counts: {row['hourly_trade_counts']}",
                f"  - temporal_reason_count: {row['temporal_reason_count']}",
                f"  - duplicate_recent_third_candidate_count: {row['duplicate_recent_third_candidate_count']}",
                f"  - max_entries_per_recent_third_candidate: {row['max_entries_per_recent_third_candidate']}",
                f"  - average_temporal_lag_bars: {row['average_temporal_lag_bars']}",
                f"  - max_temporal_lag_bars: {row['max_temporal_lag_bars']}",
                f"  - temporal_lag_bars_distribution: {row['temporal_lag_bars_distribution']}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = [Path(p) for p in args.run_dir]
    rows = [_compute_run_metrics(run_dir) for run_dir in run_dirs]

    def sort_key(item: dict[str, Any]) -> int:
        value = item.get("lookback_bars", "")
        try:
            return int(value)
        except Exception:
            return 10**9

    rows = sorted(rows, key=sort_key)

    out_csv = output_dir / "temporal_lookback_comparison.csv"
    out_md = output_dir / "temporal_lookback_comparison.md"
    _write_csv(out_csv, rows)
    _write_md(out_md, rows)

    print(f"[done] comparison_csv={out_csv}")
    print(f"[done] comparison_md={out_md}")
    print(f"[summary] runs={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
