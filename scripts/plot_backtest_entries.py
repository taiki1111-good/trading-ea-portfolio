#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass
class PriceBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot backtest entry timing charts from M5 price CSV and trade_logs.csv."
    )
    parser.add_argument("--price-csv", required=True, help="Path to M5 OHLC CSV")
    parser.add_argument("--trade-logs", required=True, help="Path to trade_logs.csv")
    parser.add_argument("--output-dir", required=True, help="Directory to save chart PNG files and chart_index.csv")
    parser.add_argument("--before-bars", type=int, default=40, help="Bars before entry_time")
    parser.add_argument("--after-bars", type=int, default=20, help="Bars after entry_time")
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
            if ts is None or o is None or h is None or l is None or c is None:
                continue
            bars.append(PriceBar(timestamp=ts, open=o, high=h, low=l, close=c))

    bars.sort(key=lambda x: x.timestamp)
    index_map = {bar.timestamp: i for i, bar in enumerate(bars)}
    return bars, index_map


def load_trade_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [{k: str(v) for k, v in row.items()} for row in reader]


def draw_candles(ax: Any, bars: list[PriceBar]) -> None:
    width = 0.6
    for i, bar in enumerate(bars):
        is_up = bar.close >= bar.open
        color = "#2ca02c" if is_up else "#d62728"
        ax.vlines(i, bar.low, bar.high, color=color, linewidth=1.0)
        body_low = min(bar.open, bar.close)
        body_h = abs(bar.close - bar.open)
        if body_h == 0:
            body_h = 1e-6
        rect = plt.Rectangle((i - width / 2.0, body_low), width, body_h, facecolor=color, edgecolor=color, alpha=0.8)
        ax.add_patch(rect)


def draw_trade_markers(
    ax: Any,
    window_bars: list[PriceBar],
    trade: dict[str, str],
    signal_type: str,
) -> None:
    def x_from_time(key: str) -> float | None:
        t = parse_iso(trade.get(key))
        if t is None:
            return None
        for i, bar in enumerate(window_bars):
            if bar.timestamp == t:
                return float(i)
        return None

    entry_x = x_from_time("entry_time")
    exit_x = x_from_time("exit_time")
    recent_x = x_from_time("recent_third_timestamp")

    entry_price = to_float(trade.get("fill_price"))
    if entry_price is None:
        entry_price = to_float(trade.get("execution_price"))

    exit_price = None
    if exit_x is not None and 0 <= int(exit_x) < len(window_bars):
        exit_price = window_bars[int(exit_x)].close

    marker = "^" if signal_type == "long_entry" else "v"
    entry_color = "#1f77b4" if signal_type == "long_entry" else "#ff7f0e"

    if entry_x is not None and entry_price is not None:
        ax.scatter([entry_x], [entry_price], marker=marker, s=80, color=entry_color, label=f"{signal_type}", zorder=5)
        ax.axvline(entry_x, color=entry_color, linestyle="--", linewidth=1.2, alpha=0.8, label="entry_time")

    if exit_x is not None:
        y = exit_price if exit_price is not None else window_bars[int(exit_x)].close
        ax.scatter([exit_x], [y], marker="x", s=80, color="#111111", label="exit", zorder=5)
        ax.axvline(exit_x, color="#111111", linestyle=":", linewidth=1.0, alpha=0.8, label="exit_time")

    if recent_x is not None:
        ax.axvline(recent_x, color="#9467bd", linestyle="-.", linewidth=1.0, alpha=0.8, label="recent_third_timestamp")

    sl = to_float(trade.get("stop_loss"))
    tp = to_float(trade.get("take_profit"))
    if sl is not None:
        ax.axhline(sl, color="#d62728", linestyle="--", linewidth=1.0, alpha=0.8, label="stop_loss")
    if tp is not None:
        ax.axhline(tp, color="#2ca02c", linestyle="--", linewidth=1.0, alpha=0.8, label="take_profit")


def make_title(trade: dict[str, str]) -> str:
    signal_type = trade.get("signal_type", "")
    entry_time = trade.get("entry_time", "")
    exit_reason = trade.get("exit_reason", "")
    pnl = trade.get("pnl", "")
    lag = trade.get("temporal_lag_bars", "")
    source = trade.get("structure_source", "")
    return (
        f"signal_type={signal_type} | entry_time={entry_time} | exit_reason={exit_reason} | "
        f"pnl={pnl} | temporal_lag_bars={lag} | structure_source={source}"
    )


def main() -> int:
    args = parse_args()

    price_csv = Path(args.price_csv)
    trade_logs = Path(args.trade_logs)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bars, price_index = load_price_bars(price_csv)
    if not bars:
        raise RuntimeError(f"No valid price bars found: {price_csv}")

    trade_rows = load_trade_rows(trade_logs)
    if args.trade_index is not None:
        if args.trade_index < 0 or args.trade_index >= len(trade_rows):
            raise IndexError(f"trade-index out of range: {args.trade_index}")
        target_indices = [args.trade_index]
    else:
        target_indices = list(range(min(len(trade_rows), max(0, args.max_charts))))

    chart_index_rows: list[dict[str, Any]] = []
    chart_count = 0

    for idx in target_indices:
        trade = trade_rows[idx]
        entry_ts = parse_iso(trade.get("entry_time"))
        if entry_ts is None or entry_ts not in price_index:
            continue

        entry_i = price_index[entry_ts]
        start_i = max(0, entry_i - max(0, args.before_bars))
        end_i = min(len(bars) - 1, entry_i + max(0, args.after_bars))
        window = bars[start_i : end_i + 1]
        if not window:
            continue

        fig, ax = plt.subplots(figsize=(14, 7))
        draw_candles(ax, window)
        draw_trade_markers(ax, window, trade, trade.get("signal_type", ""))

        tick_step = max(1, len(window) // 8)
        xticks = list(range(0, len(window), tick_step))
        ax.set_xticks(xticks)
        ax.set_xticklabels([window[i].timestamp.strftime("%m-%d %H:%M") for i in xticks], rotation=30, ha="right")

        ax.set_title(make_title(trade), fontsize=10)
        ax.set_xlabel("M5 time")
        ax.set_ylabel("Price")
        ax.grid(alpha=0.2)

        handles, labels = ax.get_legend_handles_labels()
        seen: set[str] = set()
        uniq_handles = []
        uniq_labels = []
        for h, l in zip(handles, labels):
            if l in seen:
                continue
            seen.add(l)
            uniq_handles.append(h)
            uniq_labels.append(l)
        if uniq_handles:
            ax.legend(uniq_handles, uniq_labels, loc="best", fontsize=8)

        chart_count += 1
        chart_file = f"chart_{chart_count:04d}.png"
        chart_path = output_dir / chart_file
        fig.tight_layout()
        fig.savefig(chart_path, dpi=150)
        plt.close(fig)

        chart_index_rows.append(
            {
                "chart_file": chart_file,
                "trade_index": idx,
                "signal_type": trade.get("signal_type", ""),
                "entry_time": trade.get("entry_time", ""),
                "exit_time": trade.get("exit_time", ""),
                "recent_third_timestamp": trade.get("recent_third_timestamp", ""),
                "temporal_lag_bars": trade.get("temporal_lag_bars", ""),
                "exit_reason": trade.get("exit_reason", ""),
                "pnl": trade.get("pnl", ""),
                "structure_source": trade.get("structure_source", ""),
            }
        )

        if args.trade_index is None and chart_count >= max(0, args.max_charts):
            break

    index_path = output_dir / "chart_index.csv"
    fieldnames = [
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
    with index_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in chart_index_rows:
            writer.writerow(row)

    print(f"[done] price_csv={price_csv}")
    print(f"[done] trade_logs={trade_logs}")
    print(f"[done] output_dir={output_dir}")
    print(f"[done] chart_count={chart_count}")
    print(f"[done] chart_index={index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
