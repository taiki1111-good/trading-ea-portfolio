#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


REQUIRED_M5_COLUMNS = {"timestamp", "open", "high", "low", "close"}


@dataclass
class HaltTrigger:
    halt_start_time: datetime
    halt_end_time: datetime
    halt_reason: str
    halt_source: str
    trigger_time: datetime
    trigger_value_pips: float | None
    atr_ratio: float | None
    range_ratio: float | None
    cooldown_minutes: int


@dataclass
class HaltWindow:
    halt_start_time: datetime
    halt_end_time: datetime
    halt_reason: str
    halt_source: str
    trigger_time: datetime
    trigger_value_pips: float | None
    atr_ratio: float | None
    range_ratio: float | None
    cooldown_minutes: int


@dataclass
class EntryCandidate:
    entry_time: datetime
    signal_type: str
    trade_id: str
    pnl: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose Halt/Risk filters on M5 slice (counterfactual).")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--decision-logs", required=True)
    parser.add_argument("--trade-logs", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--shock-m5-pips", type=float, required=True)
    parser.add_argument("--shock-m15-pips", type=float, required=True)
    parser.add_argument("--atr-window", type=int, required=True)
    parser.add_argument("--atr-median-window", type=int, required=True)
    parser.add_argument("--atr-ratio-threshold", type=float, required=True)
    parser.add_argument("--range-ratio-threshold", type=float, required=True)
    parser.add_argument("--cooldown-minutes-after-shock", type=int, required=True)
    parser.add_argument("--cooldown-minutes-after-volatility-spike", type=int, required=True)
    parser.add_argument("--instrument", default="USDJPY")
    parser.add_argument("--pip-size", type=float, default=0.01)
    parser.add_argument("--enable-price-shock", action="store_true", default=None)
    parser.add_argument("--enable-volatility-spike", action="store_true", default=None)
    return parser.parse_args()


def parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def to_float(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _rolling_mean(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    q: list[float] = []
    rolling_sum = 0.0
    for v in values:
        q.append(v)
        rolling_sum += v
        if len(q) > window:
            rolling_sum -= q.pop(0)
        if len(q) == window:
            out.append(rolling_sum / window)
        else:
            out.append(None)
    return out


def _rolling_median(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    q: list[float] = []
    for v in values:
        q.append(v)
        if len(q) > window:
            q.pop(0)
        if len(q) == window:
            s = sorted(q)
            n = len(s)
            if n % 2 == 1:
                out.append(s[n // 2])
            else:
                out.append((s[n // 2 - 1] + s[n // 2]) / 2.0)
        else:
            out.append(None)
    return out


def load_m5_slice(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"input-csv not found: {path}")

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_M5_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"input-csv missing required columns: {sorted(missing)}")

        for i, row in enumerate(reader, start=2):
            ts = parse_iso(row.get("timestamp"))
            o = to_float(row.get("open"))
            h = to_float(row.get("high"))
            l = to_float(row.get("low"))
            c = to_float(row.get("close"))
            if ts is None or o is None or h is None or l is None or c is None:
                raise ValueError(f"invalid OHLC/timestamp at line {i}")
            if h < l:
                raise ValueError(f"invalid bar high<low at line {i}")
            rows.append(
                {
                    "timestamp": ts,
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "spread": to_float(row.get("spread")),
                    "volume": to_float(row.get("volume")),
                }
            )

    rows.sort(key=lambda r: r["timestamp"])
    for i in range(1, len(rows)):
        if rows[i]["timestamp"] <= rows[i - 1]["timestamp"]:
            raise ValueError("input-csv timestamp must be strictly increasing (no duplicates)")
    return rows


def detect_price_shock_triggers(
    bars: list[dict[str, Any]],
    pip_size: float,
    shock_m5_pips: float,
    shock_m15_pips: float,
    cooldown_minutes_after_shock: int,
) -> list[HaltTrigger]:
    triggers: list[HaltTrigger] = []

    for bar in bars:
        range_pips = (bar["high"] - bar["low"]) / pip_size
        if range_pips >= shock_m5_pips:
            ts = bar["timestamp"]
            triggers.append(
                HaltTrigger(
                    halt_start_time=ts,
                    halt_end_time=ts + timedelta(minutes=cooldown_minutes_after_shock),
                    halt_reason="price_shock_halt",
                    halt_source="m5_range",
                    trigger_time=ts,
                    trigger_value_pips=range_pips,
                    atr_ratio=None,
                    range_ratio=None,
                    cooldown_minutes=cooldown_minutes_after_shock,
                )
            )

    for i in range(2, len(bars)):
        window = bars[i - 2 : i + 1]
        rolling_high = max(b["high"] for b in window)
        rolling_low = min(b["low"] for b in window)
        range_pips = (rolling_high - rolling_low) / pip_size
        if range_pips >= shock_m15_pips:
            ts = bars[i]["timestamp"]
            triggers.append(
                HaltTrigger(
                    halt_start_time=ts,
                    halt_end_time=ts + timedelta(minutes=cooldown_minutes_after_shock),
                    halt_reason="price_shock_halt",
                    halt_source="m15_equivalent_rolling3",
                    trigger_time=ts,
                    trigger_value_pips=range_pips,
                    atr_ratio=None,
                    range_ratio=None,
                    cooldown_minutes=cooldown_minutes_after_shock,
                )
            )

    return triggers


def detect_volatility_spike_triggers(
    bars: list[dict[str, Any]],
    pip_size: float,
    atr_window: int,
    atr_median_window: int,
    atr_ratio_threshold: float,
    range_ratio_threshold: float,
    cooldown_minutes_after_volatility_spike: int,
) -> list[HaltTrigger]:
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    closes = [b["close"] for b in bars]

    true_ranges: list[float] = []
    range_pips_series: list[float] = []
    for i, bar in enumerate(bars):
        if i == 0:
            tr = bar["high"] - bar["low"]
        else:
            prev_close = closes[i - 1]
            tr = max(
                bar["high"] - bar["low"],
                abs(bar["high"] - prev_close),
                abs(bar["low"] - prev_close),
            )
        true_ranges.append(tr)
        range_pips_series.append((highs[i] - lows[i]) / pip_size)

    atr = _rolling_mean(true_ranges, atr_window)
    atr_median = _rolling_median([x if x is not None else 0.0 for x in atr], atr_median_window)
    range_median = _rolling_median(range_pips_series, atr_median_window)

    triggers: list[HaltTrigger] = []
    for i, bar in enumerate(bars):
        atr_value = atr[i]
        atr_med = atr_median[i]
        range_med = range_median[i]

        atr_ratio: float | None = None
        range_ratio: float | None = None

        atr_trigger = False
        if atr_value is not None and atr_med is not None and atr_med > 0:
            atr_ratio = atr_value / atr_med
            atr_trigger = atr_ratio > atr_ratio_threshold

        range_trigger = False
        if range_med is not None and range_med > 0:
            range_ratio = range_pips_series[i] / range_med
            range_trigger = range_ratio > range_ratio_threshold

        if atr_trigger or range_trigger:
            ts = bar["timestamp"]
            trigger_value = range_pips_series[i]
            triggers.append(
                HaltTrigger(
                    halt_start_time=ts,
                    halt_end_time=ts + timedelta(minutes=cooldown_minutes_after_volatility_spike),
                    halt_reason="volatility_spike_halt",
                    halt_source="atr_ratio_or_range_ratio",
                    trigger_time=ts,
                    trigger_value_pips=trigger_value,
                    atr_ratio=atr_ratio,
                    range_ratio=range_ratio,
                    cooldown_minutes=cooldown_minutes_after_volatility_spike,
                )
            )

    return triggers


def merge_halt_windows(triggers: list[HaltTrigger]) -> list[HaltWindow]:
    if not triggers:
        return []

    sorted_triggers = sorted(triggers, key=lambda t: t.halt_start_time)
    merged: list[HaltWindow] = []

    for t in sorted_triggers:
        if not merged:
            merged.append(
                HaltWindow(
                    halt_start_time=t.halt_start_time,
                    halt_end_time=t.halt_end_time,
                    halt_reason=t.halt_reason,
                    halt_source=t.halt_source,
                    trigger_time=t.trigger_time,
                    trigger_value_pips=t.trigger_value_pips,
                    atr_ratio=t.atr_ratio,
                    range_ratio=t.range_ratio,
                    cooldown_minutes=t.cooldown_minutes,
                )
            )
            continue

        prev = merged[-1]
        if t.halt_start_time <= prev.halt_end_time:
            prev.halt_end_time = max(prev.halt_end_time, t.halt_end_time)
            reasons = sorted(set(prev.halt_reason.split("|")) | {t.halt_reason})
            sources = sorted(set(prev.halt_source.split("|")) | {t.halt_source})
            prev.halt_reason = "|".join(reasons)
            prev.halt_source = "|".join(sources)
            prev.cooldown_minutes = max(prev.cooldown_minutes, t.cooldown_minutes)
            if t.trigger_time < prev.trigger_time:
                prev.trigger_time = t.trigger_time
            if prev.trigger_value_pips is None:
                prev.trigger_value_pips = t.trigger_value_pips
            elif t.trigger_value_pips is not None:
                prev.trigger_value_pips = max(prev.trigger_value_pips, t.trigger_value_pips)
            if prev.atr_ratio is None:
                prev.atr_ratio = t.atr_ratio
            elif t.atr_ratio is not None:
                prev.atr_ratio = max(prev.atr_ratio, t.atr_ratio)
            if prev.range_ratio is None:
                prev.range_ratio = t.range_ratio
            elif t.range_ratio is not None:
                prev.range_ratio = max(prev.range_ratio, t.range_ratio)
        else:
            merged.append(
                HaltWindow(
                    halt_start_time=t.halt_start_time,
                    halt_end_time=t.halt_end_time,
                    halt_reason=t.halt_reason,
                    halt_source=t.halt_source,
                    trigger_time=t.trigger_time,
                    trigger_value_pips=t.trigger_value_pips,
                    atr_ratio=t.atr_ratio,
                    range_ratio=t.range_ratio,
                    cooldown_minutes=t.cooldown_minutes,
                )
            )

    return merged


def _is_true(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "t", "yes", "y"}


def _load_trade_entries(path: Path) -> list[EntryCandidate]:
    if not path.exists():
        return []

    rows: list[EntryCandidate] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"entry_time", "signal_type"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"trade_logs missing required columns: {sorted(missing)}")

        for row in reader:
            entry_time = parse_iso(row.get("entry_time"))
            signal_type = str(row.get("signal_type") or "").strip()
            if entry_time is None or not signal_type:
                continue
            trade_id = str(row.get("trade_id") or "").strip()
            pnl = to_float(row.get("pnl"))
            rows.append(EntryCandidate(entry_time, signal_type, trade_id, pnl))
    return rows


def _load_decision_entries(path: Path, strict: bool = False) -> tuple[list[EntryCandidate], list[str]]:
    warnings: list[str] = []
    if not path.exists():
        warnings.append(f"decision_logs not found, skipped: {path}")
        return [], warnings

    rows: list[EntryCandidate] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"entry_time", "signal_type"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            if strict:
                raise ValueError(f"decision_logs missing required columns: {sorted(missing)}")
            warnings.append(
                f"decision_logs missing required columns and skipped: {sorted(missing)}"
            )
            return [], warnings

        for row in reader:
            entry_time = parse_iso(row.get("entry_time"))
            signal_type = str(row.get("signal_type") or "").strip()
            if entry_time is None or not signal_type:
                continue
            if not (_is_true(row.get("entry_signal")) or _is_true(row.get("trade_ok"))):
                continue
            trade_id = str(row.get("trade_id") or "").strip()
            rows.append(EntryCandidate(entry_time, signal_type, trade_id, None))
    return rows, warnings


def load_entry_candidates(
    trade_logs_path: Path, decision_logs_path: Path
) -> tuple[list[EntryCandidate], list[str]]:
    warnings: list[str] = []
    trade_entries = _load_trade_entries(trade_logs_path)
    decision_strict = len(trade_entries) == 0
    decision_entries, decision_warnings = _load_decision_entries(
        decision_logs_path, strict=decision_strict
    )
    warnings.extend(decision_warnings)

    dedup: dict[str, EntryCandidate] = {}
    ordered: list[EntryCandidate] = []

    for src in (trade_entries, decision_entries):
        for e in src:
            key = f"trade_id:{e.trade_id}" if e.trade_id else f"time_signal:{e.entry_time.isoformat()}|{e.signal_type}"
            if key in dedup:
                existing = dedup[key]
                if existing.pnl is None and e.pnl is not None:
                    existing.pnl = e.pnl
                continue
            dedup[key] = EntryCandidate(e.entry_time, e.signal_type, e.trade_id, e.pnl)
            ordered.append(dedup[key])

    ordered.sort(key=lambda x: x.entry_time)
    if len(trade_entries) == 0 and len(decision_entries) == 0:
        raise ValueError("no entry candidates found from trade_logs and decision_logs")
    return ordered, warnings


def _entry_in_window(entry_time: datetime, window: HaltWindow) -> bool:
    return window.halt_start_time <= entry_time <= window.halt_end_time


def build_halted_entry_candidates(
    entries: list[EntryCandidate], windows: list[HaltWindow], pip_size: float
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for e in entries:
        matched = [w for w in windows if _entry_in_window(e.entry_time, w)]
        if not matched:
            continue
        reasons = sorted({r for w in matched for r in w.halt_reason.split("|")})
        start = min(w.halt_start_time for w in matched)
        end = max(w.halt_end_time for w in matched)
        rows.append(
            {
                "entry_time": e.entry_time,
                "signal_type": e.signal_type,
                "trade_id": e.trade_id,
                "pnl": e.pnl,
                "counterfactual_pips": (e.pnl / pip_size) if e.pnl is not None else None,
                "halt_reason": "|".join(reasons),
                "halt_start_time": start,
                "halt_end_time": end,
                "would_be_halted": True,
                "counterfactual_pnl": e.pnl,
            }
        )
    return rows


def summarize(
    halt_windows: list[HaltWindow], halted_entries: list[dict[str, Any]], pip_size: float
) -> dict[str, Any]:
    total_halt_minutes = 0.0
    for w in halt_windows:
        total_halt_minutes += (w.halt_end_time - w.halt_start_time).total_seconds() / 60.0

    reason_counter: Counter[str] = Counter()
    for w in halt_windows:
        for r in w.halt_reason.split("|"):
            reason_counter[r] += 1

    avoided_loss_pips = 0.0
    missed_profit_pips = 0.0
    for row in halted_entries:
        pnl = row.get("counterfactual_pnl")
        if pnl is None:
            continue
        pnl_pips = float(pnl) / pip_size
        if pnl_pips < 0:
            avoided_loss_pips += abs(pnl_pips)
        elif pnl_pips > 0:
            missed_profit_pips += pnl_pips

    net_effect = avoided_loss_pips - missed_profit_pips
    halted_count = len(halted_entries)

    return {
        "halt_window_count": len(halt_windows),
        "total_halt_minutes": total_halt_minutes,
        "halted_entry_count": halted_count,
        "halt_reason_counts": "|".join(f"{k}:{v}" for k, v in sorted(reason_counter.items())),
        "avoided_loss_pips": avoided_loss_pips,
        "missed_profit_pips": missed_profit_pips,
        "net_counterfactual_effect_pips": net_effect,
        "trade_count_reduction": halted_count,
    }


def _fmt_dt(value: datetime) -> str:
    return value.isoformat()


def _fmt_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def write_halt_windows_csv(path: Path, windows: list[HaltWindow]) -> None:
    fields = [
        "halt_start_time",
        "halt_end_time",
        "halt_reason",
        "halt_source",
        "trigger_time",
        "trigger_value_pips",
        "atr_ratio",
        "range_ratio",
        "cooldown_minutes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for w in windows:
            writer.writerow(
                {
                    "halt_start_time": _fmt_dt(w.halt_start_time),
                    "halt_end_time": _fmt_dt(w.halt_end_time),
                    "halt_reason": w.halt_reason,
                    "halt_source": w.halt_source,
                    "trigger_time": _fmt_dt(w.trigger_time),
                    "trigger_value_pips": _fmt_float(w.trigger_value_pips),
                    "atr_ratio": _fmt_float(w.atr_ratio),
                    "range_ratio": _fmt_float(w.range_ratio),
                    "cooldown_minutes": w.cooldown_minutes,
                }
            )


def write_halted_entries_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "entry_time",
        "signal_type",
        "trade_id",
        "pnl",
        "counterfactual_pips",
        "halt_reason",
        "halt_start_time",
        "halt_end_time",
        "would_be_halted",
        "counterfactual_pnl",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "entry_time": _fmt_dt(row["entry_time"]),
                    "signal_type": row["signal_type"],
                    "trade_id": row["trade_id"],
                    "pnl": "" if row["pnl"] is None else f"{row['pnl']:.6f}",
                    "counterfactual_pips": ""
                    if row["counterfactual_pips"] is None
                    else f"{row['counterfactual_pips']:.6f}",
                    "halt_reason": row["halt_reason"],
                    "halt_start_time": _fmt_dt(row["halt_start_time"]),
                    "halt_end_time": _fmt_dt(row["halt_end_time"]),
                    "would_be_halted": str(bool(row["would_be_halted"])).lower(),
                    "counterfactual_pnl": "" if row["counterfactual_pnl"] is None else f"{row['counterfactual_pnl']:.6f}",
                }
            )


def write_summary_csv(path: Path, summary: dict[str, Any]) -> None:
    fields = [
        "enabled_filters",
        "halt_window_count",
        "total_halt_minutes",
        "halted_entry_count",
        "halt_reason_counts",
        "avoided_loss_pips",
        "missed_profit_pips",
        "net_counterfactual_effect_pips",
        "trade_count_reduction",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow(summary)


def write_summary_md(path: Path, summary: dict[str, Any], args: argparse.Namespace, warnings: list[str]) -> None:
    lines = [
        "# Halt Diagnostic Summary",
        "",
        "## Inputs",
        f"- instrument: {args.instrument}",
        f"- pip_size: {args.pip_size}",
        f"- input_csv: {args.input_csv}",
        f"- decision_logs: {args.decision_logs}",
        f"- trade_logs: {args.trade_logs}",
        f"- enabled_filters: {summary['enabled_filters']}",
        "",
        "## Metrics",
        f"- halt_window_count: {summary['halt_window_count']}",
        f"- total_halt_minutes: {summary['total_halt_minutes']}",
        f"- halted_entry_count: {summary['halted_entry_count']}",
        f"- halt_reason_counts: {summary['halt_reason_counts']}",
        f"- avoided_loss_pips: {summary['avoided_loss_pips']}",
        f"- missed_profit_pips: {summary['missed_profit_pips']}",
        f"- net_counterfactual_effect_pips: {summary['net_counterfactual_effect_pips']}",
        f"- trade_count_reduction: {summary['trade_count_reduction']}",
        "- avoided/missed/net は counterfactual_pnl を pip_size で換算した pips 単位。",
        "",
        "## Warnings",
    ]
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
        "## 注意",
        "- 構造診断であり収益性確認ではない。",
        "- 閾値は初期仮説であり本採用値ではない。",
        "- 本体halt統合ではない。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_diagnostic(args: argparse.Namespace) -> dict[str, Any]:
    if args.pip_size <= 0:
        raise ValueError("pip-size must be > 0")
    if args.atr_window <= 0 or args.atr_median_window <= 0:
        raise ValueError("atr-window and atr-median-window must be > 0")

    enable_price_shock = bool(args.enable_price_shock) if args.enable_price_shock is not None else False
    enable_volatility_spike = bool(args.enable_volatility_spike) if args.enable_volatility_spike is not None else False
    if args.enable_price_shock is None and args.enable_volatility_spike is None:
        enable_price_shock = True
        enable_volatility_spike = True

    enabled_filter_names: list[str] = []
    if enable_price_shock:
        enabled_filter_names.append("price_shock_halt")
    if enable_volatility_spike:
        enabled_filter_names.append("volatility_spike_halt")
    if not enabled_filter_names:
        enabled_filter_names = ["price_shock_halt", "volatility_spike_halt"]
        enable_price_shock = True
        enable_volatility_spike = True

    enabled_filters = "|".join(enabled_filter_names)

    bars = load_m5_slice(Path(args.input_csv))
    shock: list[HaltTrigger] = []
    spike: list[HaltTrigger] = []
    if enable_price_shock:
        shock = detect_price_shock_triggers(
            bars=bars,
            pip_size=args.pip_size,
            shock_m5_pips=args.shock_m5_pips,
            shock_m15_pips=args.shock_m15_pips,
            cooldown_minutes_after_shock=args.cooldown_minutes_after_shock,
        )
    if enable_volatility_spike:
        spike = detect_volatility_spike_triggers(
            bars=bars,
            pip_size=args.pip_size,
            atr_window=args.atr_window,
            atr_median_window=args.atr_median_window,
            atr_ratio_threshold=args.atr_ratio_threshold,
            range_ratio_threshold=args.range_ratio_threshold,
            cooldown_minutes_after_volatility_spike=args.cooldown_minutes_after_volatility_spike,
        )
    windows = merge_halt_windows(shock + spike)

    entries, warnings = load_entry_candidates(Path(args.trade_logs), Path(args.decision_logs))
    halted_entries = build_halted_entry_candidates(entries, windows, args.pip_size)
    summary = summarize(windows, halted_entries, args.pip_size)
    summary["enabled_filters"] = enabled_filters

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    halt_windows_csv = output_dir / "halt_windows.csv"
    halted_entries_csv = output_dir / "halted_entry_candidates.csv"
    summary_csv = output_dir / "halt_diagnostic_summary.csv"
    summary_md = output_dir / "halt_diagnostic_summary.md"

    write_halt_windows_csv(halt_windows_csv, windows)
    write_halted_entries_csv(halted_entries_csv, halted_entries)
    write_summary_csv(summary_csv, summary)
    write_summary_md(summary_md, summary, args, warnings)

    return {
        "halt_windows_csv": str(halt_windows_csv),
        "halted_entries_csv": str(halted_entries_csv),
        "summary_csv": str(summary_csv),
        "summary_md": str(summary_md),
        "summary": summary,
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    result = run_diagnostic(args)
    print(f"[done] halt_windows_csv={result['halt_windows_csv']}")
    print(f"[done] halted_entries_csv={result['halted_entries_csv']}")
    print(f"[done] summary_csv={result['summary_csv']}")
    print(f"[done] summary_md={result['summary_md']}")
    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"[warning] {warning}")
    print(f"[summary] enabled_filters={result['summary']['enabled_filters']}")
    print(f"[summary] {result['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
