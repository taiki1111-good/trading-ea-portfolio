#!/usr/bin/env python
from __future__ import annotations

import argparse
import bisect
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

VISUAL_REFERENCE_NOTE = "H1/H4 are visual references only; current backtest decision used M5-derived pipeline window."


@dataclass
class PriceBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    spread: float
    volume: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot multi-timeframe backtest entry charts (H4/H1/M5).")
    parser.add_argument("--price-csv", required=True, help="Path to M5 OHLC CSV")
    parser.add_argument("--trade-logs", required=True, help="Path to trade_logs.csv")
    parser.add_argument("--output-dir", required=True, help="Directory to save chart PNG files and index CSV")
    parser.add_argument("--before-bars", type=int, default=40, help="M5 bars before entry_time")
    parser.add_argument("--after-bars", type=int, default=20, help="M5 bars after entry_time")
    parser.add_argument("--max-charts", type=int, default=30, help="Maximum number of charts to generate")
    parser.add_argument("--trade-index", type=int, default=None, help="Optional single trade index (0-based)")
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
        return float(value)
    except Exception:
        return None


def load_price_bars(path: Path) -> tuple[list[PriceBar], dict[datetime, int]]:
    bars: list[PriceBar] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = parse_iso(row.get("timestamp"))
            o = to_float(row.get("open"))
            h = to_float(row.get("high"))
            l = to_float(row.get("low"))
            c = to_float(row.get("close"))
            spread = to_float(row.get("spread"))
            volume = to_float(row.get("volume"))
            if None in {ts, o, h, l, c, spread, volume}:
                continue
            bars.append(PriceBar(ts, o, h, l, c, spread, volume))
    bars.sort(key=lambda x: x.timestamp)
    index_map = {bar.timestamp: i for i, bar in enumerate(bars)}
    return bars, index_map


def load_trade_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [{k: str(v) for k, v in row.items()} for row in reader]


def floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def floor_to_h4(dt: datetime) -> datetime:
    h = (dt.hour // 4) * 4
    return dt.replace(hour=h, minute=0, second=0, microsecond=0)


def resample_bars(m5_bars: list[PriceBar], timeframe: str) -> list[PriceBar]:
    if timeframe not in {"H1", "H4"}:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    if timeframe == "H1":
        bucket_fn = floor_to_hour
    else:
        bucket_fn = floor_to_h4

    bucket_bars: dict[datetime, list[PriceBar]] = {}
    for bar in m5_bars:
        key = bucket_fn(bar.timestamp)
        bucket_bars.setdefault(key, []).append(bar)

    result: list[PriceBar] = []
    for key in sorted(bucket_bars.keys()):
        rows = bucket_bars[key]
        result.append(
            PriceBar(
                timestamp=key,
                open=rows[0].open,
                high=max(r.high for r in rows),
                low=min(r.low for r in rows),
                close=rows[-1].close,
                volume=sum(r.volume for r in rows),
                spread=rows[-1].spread,
            )
        )
    return result


def draw_candles(ax: Any, bars: list[PriceBar]) -> None:
    width = 0.6
    for i, bar in enumerate(bars):
        is_up = bar.close >= bar.open
        color = "#2ca02c" if is_up else "#d62728"
        ax.vlines(i, bar.low, bar.high, color=color, linewidth=1.0)
        body_low = min(bar.open, bar.close)
        body_h = abs(bar.close - bar.open) or 1e-6
        rect = plt.Rectangle((i - width / 2.0, body_low), width, body_h, facecolor=color, edgecolor=color, alpha=0.8)
        ax.add_patch(rect)


def idx_at_or_before(ts_list: list[datetime], target: datetime | None) -> int | None:
    if target is None or not ts_list:
        return None
    pos = bisect.bisect_right(ts_list, target) - 1
    if pos < 0:
        return None
    return pos


def draw_markers(
    ax: Any,
    panel_bars: list[PriceBar],
    trade: dict[str, str],
    signal_type: str,
    show_sl_tp: bool,
) -> None:
    ts_list = [b.timestamp for b in panel_bars]
    entry_t = parse_iso(trade.get("entry_time"))
    exit_t = parse_iso(trade.get("exit_time"))
    recent_t = parse_iso(trade.get("recent_third_timestamp"))

    entry_i = idx_at_or_before(ts_list, entry_t)
    exit_i = idx_at_or_before(ts_list, exit_t)
    recent_i = idx_at_or_before(ts_list, recent_t)

    entry_color = "#1f77b4" if signal_type == "long_entry" else "#ff7f0e"
    marker = "^" if signal_type == "long_entry" else "v"

    if entry_i is not None:
        entry_p = to_float(trade.get("fill_price")) or to_float(trade.get("execution_price")) or panel_bars[entry_i].close
        ax.scatter([entry_i], [entry_p], marker=marker, s=70, color=entry_color, label=signal_type, zorder=5)
        ax.axvline(entry_i, color=entry_color, linestyle="--", linewidth=1.0, label="entry_time")

    if exit_i is not None:
        exit_p = panel_bars[exit_i].close
        ax.scatter([exit_i], [exit_p], marker="x", s=70, color="#111111", label="exit", zorder=5)
        ax.axvline(exit_i, color="#111111", linestyle=":", linewidth=1.0, label="exit_time")

    if recent_i is not None:
        ax.axvline(recent_i, color="#9467bd", linestyle="-.", linewidth=1.0, label="recent_third_timestamp")

    if show_sl_tp:
        sl = to_float(trade.get("stop_loss"))
        tp = to_float(trade.get("take_profit"))
        if sl is not None:
            ax.axhline(sl, color="#d62728", linestyle="--", linewidth=1.0, label="stop_loss")
        if tp is not None:
            ax.axhline(tp, color="#2ca02c", linestyle="--", linewidth=1.0, label="take_profit")


def dedup_legend(ax: Any) -> None:
    handles, labels = ax.get_legend_handles_labels()
    seen: set[str] = set()
    uniq_h = []
    uniq_l = []
    for h, l in zip(handles, labels):
        if l in seen:
            continue
        seen.add(l)
        uniq_h.append(h)
        uniq_l.append(l)
    if uniq_h:
        ax.legend(uniq_h, uniq_l, loc="best", fontsize=7)


def panel_window(all_bars: list[PriceBar], start_t: datetime, end_t: datetime) -> list[PriceBar]:
    return [b for b in all_bars if start_t <= b.timestamp <= end_t]


def set_xticks(ax: Any, bars: list[PriceBar], fmt: str) -> None:
    if not bars:
        return
    step = max(1, len(bars) // 6)
    ticks = list(range(0, len(bars), step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([bars[i].timestamp.strftime(fmt) for i in ticks], rotation=30, ha="right", fontsize=7)


def make_main_title(trade: dict[str, str]) -> str:
    return (
        f"{VISUAL_REFERENCE_NOTE}\n"
        f"signal_type={trade.get('signal_type','')} | entry_time={trade.get('entry_time','')} | "
        f"exit_reason={trade.get('exit_reason','')} | pnl={trade.get('pnl','')} | "
        f"temporal_lag_bars={trade.get('temporal_lag_bars','')} | structure_source={trade.get('structure_source','')}"
    )


def main() -> int:
    args = parse_args()
    price_csv = Path(args.price_csv)
    trade_logs = Path(args.trade_logs)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    m5_bars, m5_index = load_price_bars(price_csv)
    if not m5_bars:
        raise RuntimeError(f"No valid M5 bars found: {price_csv}")

    h1_bars = resample_bars(m5_bars, "H1")
    h4_bars = resample_bars(m5_bars, "H4")

    trades = load_trade_rows(trade_logs)
    if args.trade_index is not None:
        if args.trade_index < 0 or args.trade_index >= len(trades):
            raise IndexError(f"trade-index out of range: {args.trade_index}")
        target_indices = [args.trade_index]
    else:
        target_indices = list(range(min(len(trades), max(0, args.max_charts))))

    chart_rows: list[dict[str, Any]] = []
    chart_count = 0

    for trade_idx in target_indices:
        trade = trades[trade_idx]
        entry_t = parse_iso(trade.get("entry_time"))
        if entry_t is None or entry_t not in m5_index:
            continue

        entry_i = m5_index[entry_t]
        start_i = max(0, entry_i - max(0, args.before_bars))
        end_i = min(len(m5_bars) - 1, entry_i + max(0, args.after_bars))
        m5_window = m5_bars[start_i : end_i + 1]
        if not m5_window:
            continue

        start_t = m5_window[0].timestamp
        end_t = m5_window[-1].timestamp
        h1_window = panel_window(h1_bars, floor_to_hour(start_t), floor_to_hour(end_t))
        h4_window = panel_window(h4_bars, floor_to_h4(start_t), floor_to_h4(end_t))

        if not h1_window:
            h1_window = [b for b in h1_bars if b.timestamp <= floor_to_hour(end_t)][-max(1, (args.before_bars + args.after_bars) // 12):]
        if not h4_window:
            h4_window = [b for b in h4_bars if b.timestamp <= floor_to_h4(end_t)][-max(1, (args.before_bars + args.after_bars) // 48 + 1):]

        fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=False)

        panels = [
            (axes[0], h4_window, "H4 reference panel", False, "%m-%d %H:%M"),
            (axes[1], h1_window, "H1 reference panel", False, "%m-%d %H:%M"),
            (axes[2], m5_window, "M5 execution panel", True, "%m-%d %H:%M"),
        ]

        for ax, bars, panel_title, show_sl_tp, tick_fmt in panels:
            if not bars:
                ax.text(0.5, 0.5, "No bars in range", transform=ax.transAxes, ha="center", va="center")
                ax.set_title(panel_title)
                continue
            draw_candles(ax, bars)
            draw_markers(ax, bars, trade, trade.get("signal_type", ""), show_sl_tp)
            ax.set_title(panel_title, fontsize=10)
            ax.set_ylabel("Price")
            ax.grid(alpha=0.2)
            set_xticks(ax, bars, tick_fmt)
            dedup_legend(ax)

        axes[2].set_xlabel("Time")
        fig.suptitle(make_main_title(trade), fontsize=10, y=0.99)
        fig.tight_layout(rect=[0, 0, 1, 0.95])

        chart_count += 1
        chart_file = f"mtf_chart_{chart_count:04d}.png"
        fig.savefig(output_dir / chart_file, dpi=150)
        plt.close(fig)

        chart_rows.append(
            {
                "chart_file": chart_file,
                "trade_index": trade_idx,
                "signal_type": trade.get("signal_type", ""),
                "entry_time": trade.get("entry_time", ""),
                "exit_time": trade.get("exit_time", ""),
                "recent_third_timestamp": trade.get("recent_third_timestamp", ""),
                "temporal_lag_bars": trade.get("temporal_lag_bars", ""),
                "exit_reason": trade.get("exit_reason", ""),
                "pnl": trade.get("pnl", ""),
                "structure_source": trade.get("structure_source", ""),
                "note_visual_reference_only": VISUAL_REFERENCE_NOTE,
            }
        )

        if args.trade_index is None and chart_count >= max(0, args.max_charts):
            break

    idx_path = output_dir / "mtf_chart_index.csv"
    fields = [
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
        "note_visual_reference_only",
    ]
    with idx_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in chart_rows:
            writer.writerow(row)

    print(f"[done] output_dir={output_dir}")
    print(f"[done] chart_count={chart_count}")
    print(f"[done] index_csv={idx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
