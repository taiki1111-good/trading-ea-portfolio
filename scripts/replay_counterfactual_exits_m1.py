#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any

from scripts.analyze_counterfactual_exits import ExitResult
from scripts.analyze_counterfactual_exits import TradeRecord
from scripts.analyze_counterfactual_exits import evaluate_fixed_rule
from scripts.analyze_counterfactual_exits import pnl_for
from scripts.replay_counterfactual_exits_position_aware import evaluate_trailing_variant_rule

DAT_COLUMNS = ["date", "time", "open", "high", "low", "close", "volume"]
TRAILING_RULES = {
    "simple_trailing_after_1R",
    "simple_trailing_after_1R_conservative",
    "simple_trailing_after_1R_next_bar_activation",
}
M5_REFERENCE_TOTAL_PNL = {
    "baseline_fixed_exit": -0.351,
    "simple_trailing_after_1R": 2.732,
    "simple_trailing_after_1R_conservative": 0.508,
    "simple_trailing_after_1R_next_bar_activation": -0.077,
}


@dataclass
class M1Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M1 exit replay with fixed M5 entries.")
    parser.add_argument("--m1-dat-csv", required=True)
    parser.add_argument("--trade-logs", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--rule",
        required=True,
        choices=[
            "baseline_fixed_exit",
            "simple_trailing_after_1R",
            "simple_trailing_after_1R_conservative",
            "simple_trailing_after_1R_next_bar_activation",
        ],
    )
    parser.add_argument("--max-holding-minutes", required=True, type=int)
    parser.add_argument("--spread-pips", required=True, type=float)
    parser.add_argument(
        "--entry-time-mode",
        choices=["bar_timestamp", "m5_close"],
        default="bar_timestamp",
        help="Interpretation for trade_logs entry_time.",
    )
    parser.add_argument(
        "--entry-timeframe-minutes",
        type=int,
        default=5,
        help="Timeframe minutes added when --entry-time-mode=m5_close.",
    )
    return parser.parse_args()


def _safe_iso(v: Any) -> str:
    return v.isoformat() if v is not None else ""


def _effective_entry_time(entry_time: datetime, entry_time_mode: str, entry_timeframe_minutes: int) -> datetime:
    if entry_time_mode == "m5_close":
        return entry_time + timedelta(minutes=entry_timeframe_minutes)
    return entry_time


def _parse_trade_logs_window(
    trades: list[TradeRecord],
    max_holding_minutes: int,
    entry_time_mode: str,
    entry_timeframe_minutes: int,
) -> tuple[datetime, datetime]:
    entry_min = min(_effective_entry_time(t.entry_time, entry_time_mode, entry_timeframe_minutes) for t in trades)
    end_candidates = []
    for t in trades:
        base = t.baseline_exit_time if t.baseline_exit_time is not None else t.entry_time
        end_candidates.append(base)
    latest = max(end_candidates)
    end = latest + timedelta(minutes=max_holding_minutes + entry_timeframe_minutes + 1)
    return entry_min, end


def load_m1_bars_in_range(path: Path, start: datetime, end: datetime) -> tuple[list[M1Bar], dict[datetime, int]]:
    if not path.exists():
        raise FileNotFoundError(f"m1 DAT CSV not found: {path}")

    bars: list[M1Bar] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for ln, row in enumerate(reader, start=1):
            if len(row) != 7:
                raise ValueError(f"Invalid DAT format at line {ln}: expected 7 columns, got {len(row)}")
            date_raw, time_raw, o, h, l, c, _volume = [str(x).strip() for x in row]
            try:
                ts = datetime.strptime(f"{date_raw} {time_raw}", "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
                open_p = float(o)
                high_p = float(h)
                low_p = float(l)
                close_p = float(c)
            except Exception as exc:
                raise ValueError(f"Failed to parse DAT row at line {ln}: {exc}") from exc
            if ts < start or ts > end:
                continue
            bars.append(M1Bar(ts, open_p, high_p, low_p, close_p))

    if not bars:
        raise ValueError("No M1 bars found in required trade_logs window")

    bars.sort(key=lambda x: x.timestamp)
    return bars, {b.timestamp: i for i, b in enumerate(bars)}


def _evaluate_for_rule(
    trade: TradeRecord,
    rule: str,
    bars: list[M1Bar],
    index_map: dict[datetime, int],
    max_holding_minutes: int,
) -> ExitResult:
    if rule in TRAILING_RULES:
        return evaluate_trailing_variant_rule(trade, bars, index_map, max_holding_minutes, rule)
    return evaluate_fixed_rule(
        trade,
        bars,
        index_map,
        max_holding_minutes,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        rule_name=rule,
    )


def run_m1_replay(
    trades: list[TradeRecord],
    bars: list[M1Bar],
    index_map: dict[datetime, int],
    rule: str,
    max_holding_minutes: int,
    entry_time_mode: str = "bar_timestamp",
    entry_timeframe_minutes: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = sorted(
        trades,
        key=lambda t: (_effective_entry_time(t.entry_time, entry_time_mode, entry_timeframe_minutes), t.trade_index),
    )
    open_until: datetime | None = None
    rows: list[dict[str, Any]] = []

    for t in candidates:
        effective_entry_time = _effective_entry_time(t.entry_time, entry_time_mode, entry_timeframe_minutes)
        entry_i = index_map.get(effective_entry_time)
        if entry_i is None:
            rows.append(
                {
                    "original_trade_index": t.trade_index,
                    "accepted_entry": False,
                    "skipped_reason": "entry_time_not_in_m1_data",
                    "signal_type": t.signal_type,
                    "entry_time": _safe_iso(t.entry_time),
                    "entry_effective_time": _safe_iso(effective_entry_time),
                    "original_exit_time": _safe_iso(t.baseline_exit_time),
                    "m1_exit_time": "",
                    "m1_exit_reason": "",
                    "original_pnl": t.baseline_pnl,
                    "m1_replay_pnl": "",
                    "pnl_diff": "",
                    "holding_minutes": "",
                    "rule": rule,
                    "entry_price": t.entry_price,
                    "initial_stop_loss": t.stop_loss,
                    "initial_take_profit": t.take_profit,
                    "trailing_stop_final": "",
                    "m1_bars_used": "",
                    "entry_time_mode": entry_time_mode,
                    "notes": "",
                }
            )
            continue

        if open_until is not None and effective_entry_time <= open_until:
            rows.append(
                {
                    "original_trade_index": t.trade_index,
                    "accepted_entry": False,
                    "skipped_reason": "skipped_due_to_open_position",
                    "signal_type": t.signal_type,
                    "entry_time": _safe_iso(t.entry_time),
                    "entry_effective_time": _safe_iso(effective_entry_time),
                    "original_exit_time": _safe_iso(t.baseline_exit_time),
                    "m1_exit_time": "",
                    "m1_exit_reason": "",
                    "original_pnl": t.baseline_pnl,
                    "m1_replay_pnl": "",
                    "pnl_diff": "",
                    "holding_minutes": "",
                    "rule": rule,
                    "entry_price": t.entry_price,
                    "initial_stop_loss": t.stop_loss,
                    "initial_take_profit": t.take_profit,
                    "trailing_stop_final": "",
                    "m1_bars_used": "",
                    "entry_time_mode": entry_time_mode,
                    "notes": "",
                }
            )
            continue

        adjusted_trade = replace(t, entry_time=effective_entry_time)
        res = _evaluate_for_rule(adjusted_trade, rule, bars, index_map, max_holding_minutes)
        if res.holding_bars <= 0:
            raise RuntimeError(f"Invalid replay result: exit on entry bar detected for trade_index={t.trade_index}")

        open_until = res.exit_time
        d = res.diagnostics or {}
        rows.append(
            {
                "original_trade_index": t.trade_index,
                "accepted_entry": True,
                "skipped_reason": "",
                "signal_type": t.signal_type,
                "entry_time": _safe_iso(t.entry_time),
                "entry_effective_time": _safe_iso(effective_entry_time),
                "original_exit_time": _safe_iso(t.baseline_exit_time),
                "m1_exit_time": _safe_iso(res.exit_time),
                "m1_exit_reason": res.exit_reason,
                "original_pnl": t.baseline_pnl,
                "m1_replay_pnl": res.pnl,
                "pnl_diff": res.pnl - t.baseline_pnl,
                "holding_minutes": res.holding_bars,
                "rule": rule,
                "entry_price": t.entry_price,
                "initial_stop_loss": t.stop_loss,
                "initial_take_profit": t.take_profit,
                "trailing_stop_final": d.get("trailing_stop_final", t.stop_loss if rule in TRAILING_RULES else ""),
                "m1_bars_used": res.holding_bars,
                "entry_time_mode": entry_time_mode,
                "notes": d.get("ambiguity_note", ""),
            }
        )

    accepted = [r for r in rows if r["accepted_entry"]]
    skipped = [r for r in rows if not r["accepted_entry"]]
    pnls = [float(r["m1_replay_pnl"]) for r in accepted]
    exit_counts = Counter(str(r["m1_exit_reason"]) for r in accepted)
    holds = [int(r["holding_minutes"]) for r in accepted]

    summary = {
        "rule": rule,
        "entry_time_mode": entry_time_mode,
        "entry_timeframe_minutes": entry_timeframe_minutes,
        "original_trade_count": len(rows),
        "accepted_trade_count": len(accepted),
        "skipped_entry_count": len(skipped),
        "skipped_due_to_open_position_count": sum(1 for r in skipped if r["skipped_reason"] == "skipped_due_to_open_position"),
        "win_count": sum(1 for p in pnls if p > 0),
        "loss_count": sum(1 for p in pnls if p < 0),
        "win_rate": (sum(1 for p in pnls if p > 0) / len(pnls) * 100.0) if pnls else 0.0,
        "total_pnl": sum(pnls),
        "average_pnl": (sum(pnls) / len(pnls)) if pnls else 0.0,
        "median_pnl": median(pnls) if pnls else 0.0,
        "exit_reason_counts": dict(exit_counts),
        "average_holding_minutes": (sum(holds) / len(holds)) if holds else 0.0,
        "max_holding_minutes": max(holds) if holds else 0,
        "delta_vs_m5_baseline": sum(pnls) - M5_REFERENCE_TOTAL_PNL["baseline_fixed_exit"],
        "delta_vs_m5_position_aware_simple_trailing": sum(pnls) - M5_REFERENCE_TOTAL_PNL["simple_trailing_after_1R"],
        "comparison_memo": (
            "M5 reference total_pnl: simple_trailing_after_1R=2.732, "
            "conservative=0.508, next_bar_activation=-0.077"
        ),
    }
    return rows, summary


def write_outputs(output_dir: Path, rows: list[dict[str, Any]], summary: dict[str, Any], spread_pips: float) -> None:
    trades_csv = output_dir / "m1_exit_replay_trades.csv"
    summary_csv = output_dir / "m1_exit_replay_summary.csv"
    summary_md = output_dir / "m1_exit_replay_summary.md"

    with trades_csv.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "original_trade_index", "accepted_entry", "skipped_reason", "signal_type", "entry_time", "original_exit_time",
            "entry_effective_time", "m1_exit_time", "m1_exit_reason", "original_pnl", "m1_replay_pnl", "pnl_diff",
            "holding_minutes", "rule", "entry_price", "initial_stop_loss", "initial_take_profit", "trailing_stop_final",
            "m1_bars_used", "entry_time_mode", "notes",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        serial = dict(summary)
        serial["exit_reason_counts"] = json.dumps(serial["exit_reason_counts"], ensure_ascii=False)
        w = csv.DictWriter(f, fieldnames=list(serial.keys()))
        w.writeheader()
        w.writerow(serial)

    lines = [
        "# M1 Exit Replay Summary",
        "",
        "## 注意",
        "- M5 entry固定でM1 exitを再評価する構造検証であり、BacktestRunner統合前の分析段階。",
        "- spread=0.2 pips fallback前提、手数料・スリッページ・スワップ未反映。",
        "- M1でも同一バー内のOHLC順序は不明であり、曖昧性は完全には消えない。",
        "- 収益性評価ではなくexit候補の構造検証。",
        "",
    ]
    for k, v in summary.items():
        lines.append(f"- {k}: {v}")
    lines.append(f"- spread_pips_assumption: {spread_pips}")
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    trade_logs = Path(args.trade_logs)
    m1_dat = Path(args.m1_dat_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from scripts.analyze_counterfactual_exits import load_trade_records

    trades = load_trade_records(trade_logs)
    if not trades:
        raise RuntimeError("No usable trade rows found in trade_logs")

    start, end = _parse_trade_logs_window(
        trades,
        args.max_holding_minutes,
        args.entry_time_mode,
        args.entry_timeframe_minutes,
    )
    bars, index_map = load_m1_bars_in_range(m1_dat, start, end)

    rows, summary = run_m1_replay(
        trades,
        bars,
        index_map,
        args.rule,
        args.max_holding_minutes,
        entry_time_mode=args.entry_time_mode,
        entry_timeframe_minutes=args.entry_timeframe_minutes,
    )
    write_outputs(output_dir, rows, summary, args.spread_pips)

    print(f"[done] output_dir={output_dir}")
    print(f"[done] trades_csv={output_dir / 'm1_exit_replay_trades.csv'}")
    print(f"[done] summary_csv={output_dir / 'm1_exit_replay_summary.csv'}")
    print(f"[done] summary_md={output_dir / 'm1_exit_replay_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
