#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.risk_filter.reason_catalog import normalize_reason_categories
from src.persistence.csv_log_reader import CsvLogReader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze existing backtest trade_logs for pipeline behavior checks.")
    parser.add_argument("--trade-logs", required=True, help="Path to existing trade_logs.csv")
    parser.add_argument("--output-dir", required=True, help="Directory to save analysis outputs")
    return parser.parse_args()


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def non_empty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def day_key_from_value(value: Any) -> str | None:
    if not non_empty(value):
        return None
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    return dt.date().isoformat()


def hour_key_from_value(value: Any) -> str | None:
    if not non_empty(value):
        return None
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    return f"{dt.hour:02d}"


def write_analysis_csv(path: Path, metrics: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        for k, v in metrics.items():
            writer.writerow({"metric": k, "value": v})


def _primary_category(categories: list[str]) -> str:
    return categories[0] if categories else "unknown"


def _normalize_reason_for_category(value: Any) -> str:
    if not non_empty(value):
        return ""
    return str(value).strip()


def _build_reason_category_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    risk_reason_category_counts: Counter[str] = Counter()
    filter_reason_category_counts: Counter[str] = Counter()
    risk_reason_primary_category_counts: Counter[str] = Counter()
    filter_reason_primary_category_counts: Counter[str] = Counter()
    risk_reason_unknown_count = 0
    filter_reason_unknown_count = 0

    for r in rows:
        risk_reason = _normalize_reason_for_category(r.get("risk_reason", ""))
        filter_reason = _normalize_reason_for_category(r.get("filter_reason", ""))
        risk_categories = normalize_reason_categories(risk_reason)
        filter_categories = normalize_reason_categories(filter_reason)

        risk_primary = _primary_category(risk_categories)
        filter_primary = _primary_category(filter_categories)

        if risk_primary == "unknown":
            risk_reason_unknown_count += 1
        if filter_primary == "unknown":
            filter_reason_unknown_count += 1

        risk_reason_primary_category_counts[risk_primary] += 1
        filter_reason_primary_category_counts[filter_primary] += 1

        risk_reason_category_counts.update(risk_categories)
        filter_reason_category_counts.update(filter_categories)

    return {
        "risk_reason_category_counts": dict(risk_reason_category_counts),
        "filter_reason_category_counts": dict(filter_reason_category_counts),
        "risk_reason_primary_category_counts": dict(risk_reason_primary_category_counts),
        "filter_reason_primary_category_counts": dict(filter_reason_primary_category_counts),
        "risk_reason_unknown_count": risk_reason_unknown_count,
        "filter_reason_unknown_count": filter_reason_unknown_count,
    }


def main() -> int:
    args = parse_args()
    trade_logs_path = Path(args.trade_logs)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    read_result = CsvLogReader.read(str(trade_logs_path))
    if not read_result.success:
        raise RuntimeError(read_result.persistence_reason)

    rows = read_result.data
    trade_count = len(rows)

    signal_type_counts = Counter(str(r.get("signal_type", "")) for r in rows)
    exit_reason_counts = Counter(str(r.get("exit_reason", "")) for r in rows)
    long_count = int(signal_type_counts.get("long_entry", 0))
    short_count = int(signal_type_counts.get("short_entry", 0))

    pnls = [to_float(r.get("pnl")) for r in rows]
    pnls = [p for p in pnls if p is not None]
    total_pnl = float(sum(pnls)) if pnls else 0.0
    average_pnl = (total_pnl / len(pnls)) if pnls else 0.0
    win_count = len([p for p in pnls if p > 0])
    loss_count = len([p for p in pnls if p < 0])
    win_rate = (win_count / len(pnls) * 100.0) if pnls else 0.0
    pnl_min = min(pnls) if pnls else None
    pnl_max = max(pnls) if pnls else None

    entry_reason_missing = len([r for r in rows if not non_empty(r.get("entry_reason"))])
    signal_reason_missing = len([r for r in rows if not non_empty(r.get("signal_reason"))])
    risk_reason_missing = len([r for r in rows if not non_empty(r.get("risk_reason"))])
    filter_reason_missing = len([r for r in rows if not non_empty(r.get("filter_reason"))])
    reason_category_metrics = _build_reason_category_metrics(rows)

    fallback_marker = "fallback heuristic structure was used"
    fallback_hits = 0
    for r in rows:
        entry_reason = str(r.get("entry_reason", ""))
        signal_reason = str(r.get("signal_reason", ""))
        if fallback_marker in entry_reason or fallback_marker in signal_reason:
            fallback_hits += 1
    fallback_rate = (fallback_hits / trade_count * 100.0) if trade_count > 0 else 0.0
    fallback_used_count = len([r for r in rows if bool(r.get("fallback_used")) is True])
    fallback_used_rate = (fallback_used_count / trade_count * 100.0) if trade_count > 0 else 0.0
    structure_source_counts = Counter(str(r.get("structure_source", "")) for r in rows)
    recent_third_timestamp_counts = Counter(
        str(r.get("recent_third_timestamp", "")).strip()
        for r in rows
        if non_empty(r.get("recent_third_timestamp"))
    )
    recent_third_timestamp_direction_counts: dict[str, dict[str, int]] = {}
    for r in rows:
        ts = str(r.get("recent_third_timestamp", "")).strip()
        if not ts:
            continue
        direction = str(r.get("recent_third_direction", "")).strip()
        if ts not in recent_third_timestamp_direction_counts:
            recent_third_timestamp_direction_counts[ts] = {"long": 0, "short": 0}
        if direction in {"long", "short"}:
            recent_third_timestamp_direction_counts[ts][direction] += 1

    lag_values_raw = [to_float(r.get("temporal_lag_bars")) for r in rows if non_empty(r.get("temporal_lag_bars"))]
    lag_values = [int(v) for v in lag_values_raw if v is not None]
    lag_distribution = Counter(str(v) for v in lag_values)
    lag_min = min(lag_values) if lag_values else None
    lag_max = max(lag_values) if lag_values else None
    lag_avg = (sum(lag_values) / len(lag_values)) if lag_values else None
    lookback_values = [to_float(r.get("temporal_lookback_bars")) for r in rows if non_empty(r.get("temporal_lookback_bars"))]
    lookback_distribution = Counter(str(int(v)) for v in lookback_values if v is not None)
    duplicate_recent_third_candidate_count = sum(1 for _, count in recent_third_timestamp_counts.items() if count > 1)
    max_entries_per_recent_third_candidate = max(recent_third_timestamp_counts.values()) if recent_third_timestamp_counts else 0

    tp_count = int(exit_reason_counts.get("take_profit", 0))
    sl_count = int(exit_reason_counts.get("stop_loss", 0))
    tp_sl_ratio = (tp_count / sl_count) if sl_count > 0 else None
    max_holding_exit_count = sum(
        int(v) for k, v in exit_reason_counts.items() if "max_holding" in str(k) or str(k) == "close"
    )

    daily_source_col = None
    for col in ["timestamp", "entry_time", "exit_time", "log_time"]:
        if rows and col in rows[0]:
            daily_source_col = col
            break
    daily_counts = Counter()
    daily_note = "timestamp列なしのため日別集計不可"
    if daily_source_col is not None:
        for r in rows:
            key = day_key_from_value(r.get(daily_source_col))
            if key is not None:
                daily_counts[key] += 1
        if daily_counts:
            daily_note = f"{daily_source_col}列を使用して日別集計"
        else:
            daily_note = f"{daily_source_col}列はあるが日別集計に使える値がない"

    time_bucket_note = "entry_time / exit_time 列なしのため時間帯別集計不可"
    entry_daily_counts = Counter()
    exit_daily_counts = Counter()
    entry_hour_counts = Counter()
    exit_hour_counts = Counter()
    has_entry_exit = rows and ("entry_time" in rows[0]) and ("exit_time" in rows[0])
    if has_entry_exit:
        for r in rows:
            ed = day_key_from_value(r.get("entry_time"))
            xd = day_key_from_value(r.get("exit_time"))
            eh = hour_key_from_value(r.get("entry_time"))
            xh = hour_key_from_value(r.get("exit_time"))
            if ed is not None:
                entry_daily_counts[ed] += 1
            if xd is not None:
                exit_daily_counts[xd] += 1
            if eh is not None:
                entry_hour_counts[eh] += 1
            if xh is not None:
                exit_hour_counts[xh] += 1
        if entry_hour_counts or exit_hour_counts:
            time_bucket_note = "entry_time / exit_time 列を使用して時間帯別集計"
        else:
            time_bucket_note = "entry_time / exit_time 列はあるが時間帯別集計に使える値がない"

    metrics: dict[str, Any] = {
        "trade_count": trade_count,
        "signal_type_counts": dict(signal_type_counts),
        "exit_reason_counts": dict(exit_reason_counts),
        "long_count": long_count,
        "short_count": short_count,
        "total_pnl": total_pnl,
        "average_pnl": average_pnl,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate_percent": win_rate,
        "pnl_min": pnl_min,
        "pnl_max": pnl_max,
        "entry_reason_missing_count": entry_reason_missing,
        "signal_reason_missing_count": signal_reason_missing,
        "risk_reason_missing_count": risk_reason_missing,
        "filter_reason_missing_count": filter_reason_missing,
        "risk_reason_category_counts": reason_category_metrics["risk_reason_category_counts"],
        "filter_reason_category_counts": reason_category_metrics["filter_reason_category_counts"],
        "risk_reason_primary_category_counts": reason_category_metrics["risk_reason_primary_category_counts"],
        "filter_reason_primary_category_counts": reason_category_metrics["filter_reason_primary_category_counts"],
        "risk_reason_unknown_count": reason_category_metrics["risk_reason_unknown_count"],
        "filter_reason_unknown_count": reason_category_metrics["filter_reason_unknown_count"],
        "fallback_usage_count": fallback_hits,
        "fallback_usage_rate_percent": fallback_rate,
        "fallback_used_count": fallback_used_count,
        "fallback_used_rate_percent": fallback_used_rate,
        "structure_source_counts": dict(structure_source_counts),
        "recent_third_timestamp_entry_counts": dict(recent_third_timestamp_counts),
        "recent_third_timestamp_long_short_counts": recent_third_timestamp_direction_counts,
        "temporal_lag_bars_distribution": dict(lag_distribution),
        "temporal_lag_bars_min": lag_min,
        "temporal_lag_bars_max": lag_max,
        "temporal_lag_bars_average": lag_avg,
        "temporal_lookback_bars_trade_counts": dict(lookback_distribution),
        "duplicate_recent_third_candidate_count": duplicate_recent_third_candidate_count,
        "max_entries_per_recent_third_candidate": max_entries_per_recent_third_candidate,
        "take_profit_count": tp_count,
        "stop_loss_count": sl_count,
        "take_profit_stop_loss_ratio": tp_sl_ratio,
        "max_holding_or_close_exit_count": max_holding_exit_count,
        "daily_count_note": daily_note,
        "daily_trade_counts": dict(daily_counts),
        "entry_exit_time_count_note": time_bucket_note,
        "entry_daily_trade_counts": dict(entry_daily_counts),
        "exit_daily_trade_counts": dict(exit_daily_counts),
        "entry_hour_trade_counts": dict(entry_hour_counts),
        "exit_hour_trade_counts": dict(exit_hour_counts),
    }

    analysis_csv = output_dir / "trade_log_analysis.csv"
    analysis_md = output_dir / "trade_log_analysis.md"
    write_analysis_csv(analysis_csv, metrics)

    lines = [
        "# Trade Log Analysis",
        "",
        "## 注意書き",
        "- この結果は初期BT/構造検証用であり、収益性評価ではない。",
        "- spread=0.2 pips fallback 前提。",
        "- 手数料・スリッページ・スワップ未反映。",
        "- fallback heuristic が使われている場合、その割合を確認する必要がある。",
        "",
        "## 集計",
        f"- trade_count: {trade_count}",
        f"- signal_type_counts: {dict(signal_type_counts)}",
        f"- exit_reason_counts: {dict(exit_reason_counts)}",
        f"- long_count: {long_count}",
        f"- short_count: {short_count}",
        f"- total_pnl: {total_pnl}",
        f"- average_pnl: {average_pnl}",
        f"- win_count: {win_count}",
        f"- loss_count: {loss_count}",
        f"- win_rate_percent: {win_rate}",
        f"- pnl_min: {pnl_min}",
        f"- pnl_max: {pnl_max}",
        f"- entry_reason_missing_count: {entry_reason_missing}",
        f"- signal_reason_missing_count: {signal_reason_missing}",
        f"- risk_reason_missing_count: {risk_reason_missing}",
        f"- filter_reason_missing_count: {filter_reason_missing}",
        f"- risk_reason_category_counts: {reason_category_metrics['risk_reason_category_counts']}",
        f"- filter_reason_category_counts: {reason_category_metrics['filter_reason_category_counts']}",
        f"- risk_reason_primary_category_counts: {reason_category_metrics['risk_reason_primary_category_counts']}",
        f"- filter_reason_primary_category_counts: {reason_category_metrics['filter_reason_primary_category_counts']}",
        f"- risk_reason_unknown_count: {reason_category_metrics['risk_reason_unknown_count']}",
        f"- filter_reason_unknown_count: {reason_category_metrics['filter_reason_unknown_count']}",
        f"- fallback_usage_count: {fallback_hits}",
        f"- fallback_usage_rate_percent: {fallback_rate}",
        f"- fallback_used_count: {fallback_used_count}",
        f"- fallback_used_rate_percent: {fallback_used_rate}",
        f"- structure_source_counts: {dict(structure_source_counts)}",
        f"- recent_third_timestamp_entry_counts: {dict(recent_third_timestamp_counts)}",
        f"- recent_third_timestamp_long_short_counts: {recent_third_timestamp_direction_counts}",
        f"- temporal_lag_bars_distribution: {dict(lag_distribution)}",
        f"- temporal_lag_bars_min: {lag_min}",
        f"- temporal_lag_bars_max: {lag_max}",
        f"- temporal_lag_bars_average: {lag_avg}",
        f"- temporal_lookback_bars_trade_counts: {dict(lookback_distribution)}",
        f"- duplicate_recent_third_candidate_count: {duplicate_recent_third_candidate_count}",
        f"- max_entries_per_recent_third_candidate: {max_entries_per_recent_third_candidate}",
        f"- take_profit_count: {tp_count}",
        f"- stop_loss_count: {sl_count}",
        f"- take_profit_stop_loss_ratio: {tp_sl_ratio}",
        f"- max_holding_or_close_exit_count: {max_holding_exit_count}",
        f"- daily_count_note: {daily_note}",
        f"- daily_trade_counts: {dict(daily_counts)}",
        f"- entry_exit_time_count_note: {time_bucket_note}",
        f"- entry_daily_trade_counts: {dict(entry_daily_counts)}",
        f"- exit_daily_trade_counts: {dict(exit_daily_counts)}",
        f"- entry_hour_trade_counts: {dict(entry_hour_counts)}",
        f"- exit_hour_trade_counts: {dict(exit_hour_counts)}",
        "",
    ]
    analysis_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[done] trade_logs={trade_logs_path}")
    print(f"[done] analysis_csv={analysis_csv}")
    print(f"[done] analysis_md={analysis_md}")
    print(f"[summary] trade_count={trade_count}, win_rate_percent={win_rate:.4f}, fallback_usage_rate_percent={fallback_rate:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
