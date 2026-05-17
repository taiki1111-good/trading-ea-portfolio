#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any


@dataclass
class PriceBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class TradeRecord:
    trade_index: int
    signal_type: str
    direction: str
    entry_time: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    baseline_exit_time: datetime | None
    baseline_exit_reason: str
    baseline_pnl: float


@dataclass
class ExitResult:
    trade_index: int
    rule_name: str
    exit_time: datetime
    exit_reason: str
    exit_price: float
    pnl: float
    holding_bars: int
    diagnostics: dict[str, Any] | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze counterfactual exits with fixed existing entries.")
    parser.add_argument("--price-csv", required=True)
    parser.add_argument("--trade-logs", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-holding-bars", type=int, required=True)
    parser.add_argument("--sl-multiplier-list", required=True, help="comma-separated, e.g. 1.5,2.0")
    parser.add_argument("--tp-multiplier-list", required=True, help="comma-separated, e.g. 1.5,2.0")
    parser.add_argument("--include-trailing", action="store_true")
    parser.add_argument("--include-breakeven", action="store_true")
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


def parse_multiplier_list(value: str, name: str) -> list[float]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        raise ValueError(f"{name} must not be empty")
    result: list[float] = []
    for p in parts:
        v = float(p)
        if v <= 0:
            raise ValueError(f"{name} values must be > 0: {p}")
        result.append(v)
    return result


def load_price_bars(path: Path) -> tuple[list[PriceBar], dict[datetime, int]]:
    if not path.exists():
        raise FileNotFoundError(f"price_csv not found: {path}")
    bars: list[PriceBar] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "open", "high", "low", "close"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"price_csv missing required columns: {sorted(missing)}")
        for row in reader:
            ts = parse_iso(row.get("timestamp"))
            o = to_float(row.get("open"))
            h = to_float(row.get("high"))
            l = to_float(row.get("low"))
            c = to_float(row.get("close"))
            if None in {ts, o, h, l, c}:
                continue
            bars.append(PriceBar(timestamp=ts, open=o, high=h, low=l, close=c))
    bars.sort(key=lambda x: x.timestamp)
    index_map = {b.timestamp: i for i, b in enumerate(bars)}
    return bars, index_map


def load_trade_records(path: Path) -> list[TradeRecord]:
    if not path.exists():
        raise FileNotFoundError(f"trade_logs not found: {path}")
    rows: list[TradeRecord] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "signal_type",
            "entry_time",
            "stop_loss",
            "take_profit",
            "pnl",
            "exit_reason",
            "exit_time",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"trade_logs missing required columns: {sorted(missing)}")

        for idx, row in enumerate(reader):
            signal_type = str(row.get("signal_type", "")).strip()
            if signal_type not in {"long_entry", "short_entry"}:
                continue
            direction = "long" if signal_type == "long_entry" else "short"
            entry_time = parse_iso(row.get("entry_time"))
            if entry_time is None:
                continue
            entry_price = to_float(row.get("fill_price"))
            if entry_price is None:
                entry_price = to_float(row.get("execution_price"))
            stop_loss = to_float(row.get("stop_loss"))
            take_profit = to_float(row.get("take_profit"))
            pnl = to_float(row.get("pnl"))
            if None in {entry_price, stop_loss, take_profit, pnl}:
                continue
            rows.append(
                TradeRecord(
                    trade_index=idx,
                    signal_type=signal_type,
                    direction=direction,
                    entry_time=entry_time,
                    entry_price=float(entry_price),
                    stop_loss=float(stop_loss),
                    take_profit=float(take_profit),
                    baseline_exit_time=parse_iso(row.get("exit_time")),
                    baseline_exit_reason=str(row.get("exit_reason", "")).strip(),
                    baseline_pnl=float(pnl),
                )
            )
    return rows


def load_issue_map(trade_logs_path: Path) -> dict[int, str]:
    candidates = [
        trade_logs_path.parent / "mtf_charts" / "chart_review_template.csv",
        trade_logs_path.parent / "chart_review_template.csv",
    ]
    review_path = next((p for p in candidates if p.exists()), None)
    if review_path is None:
        return {}

    mapping: dict[int, str] = {}
    with review_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "trade_index" not in reader.fieldnames:
            return {}
        for row in reader:
            try:
                ti = int(str(row.get("trade_index", "")).strip())
            except Exception:
                continue
            mapping[ti] = str(row.get("issue_category", "")).strip() or "(empty)"
    return mapping


def distance_r(trade: TradeRecord) -> float:
    return abs(trade.entry_price - trade.stop_loss)


def scaled_levels(trade: TradeRecord, sl_mult: float, tp_mult: float) -> tuple[float, float]:
    r = distance_r(trade)
    if trade.direction == "long":
        sl = trade.entry_price - (r * sl_mult)
        tp = trade.entry_price + (r * tp_mult)
    else:
        sl = trade.entry_price + (r * sl_mult)
        tp = trade.entry_price - (r * tp_mult)
    return sl, tp


def pnl_for(direction: str, entry: float, exit_price: float) -> float:
    if direction == "long":
        return exit_price - entry
    return entry - exit_price


def evaluate_fixed_rule(
    trade: TradeRecord,
    bars: list[PriceBar],
    index_map: dict[datetime, int],
    max_holding_bars: int,
    stop_loss: float,
    take_profit: float,
    rule_name: str,
) -> ExitResult:
    if trade.entry_time not in index_map:
        raise ValueError(f"entry_time not found in price bars: trade_index={trade.trade_index}, entry_time={trade.entry_time.isoformat()}")

    entry_i = index_map[trade.entry_time]
    last_i = min(len(bars) - 1, entry_i + max_holding_bars)

    for i in range(entry_i + 1, last_i + 1):
        b = bars[i]
        if trade.direction == "long":
            if b.low <= stop_loss:
                exit_price = stop_loss
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "stop_loss", exit_price, pnl_for(trade.direction, trade.entry_price, exit_price), i - entry_i)
            if b.high >= take_profit:
                exit_price = take_profit
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "take_profit", exit_price, pnl_for(trade.direction, trade.entry_price, exit_price), i - entry_i)
        else:
            if b.high >= stop_loss:
                exit_price = stop_loss
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "stop_loss", exit_price, pnl_for(trade.direction, trade.entry_price, exit_price), i - entry_i)
            if b.low <= take_profit:
                exit_price = take_profit
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "take_profit", exit_price, pnl_for(trade.direction, trade.entry_price, exit_price), i - entry_i)

    close_bar = bars[last_i]
    exit_price = close_bar.close
    return ExitResult(trade.trade_index, rule_name, close_bar.timestamp, "close", exit_price, pnl_for(trade.direction, trade.entry_price, exit_price), last_i - entry_i)


def evaluate_breakeven_rule(
    trade: TradeRecord,
    bars: list[PriceBar],
    index_map: dict[datetime, int],
    max_holding_bars: int,
    rule_name: str,
) -> ExitResult:
    base_sl = trade.stop_loss
    base_tp = trade.take_profit
    r = distance_r(trade)
    active = False
    stop_loss = base_sl

    entry_i = index_map[trade.entry_time]
    last_i = min(len(bars) - 1, entry_i + max_holding_bars)

    for i in range(entry_i + 1, last_i + 1):
        b = bars[i]

        if trade.direction == "long":
            if (not active) and b.high >= trade.entry_price + r:
                active = True
                stop_loss = trade.entry_price
            if b.low <= stop_loss:
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "breakeven_stop" if active else "stop_loss", stop_loss, pnl_for(trade.direction, trade.entry_price, stop_loss), i - entry_i)
            if b.high >= base_tp:
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "take_profit", base_tp, pnl_for(trade.direction, trade.entry_price, base_tp), i - entry_i)
        else:
            if (not active) and b.low <= trade.entry_price - r:
                active = True
                stop_loss = trade.entry_price
            if b.high >= stop_loss:
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "breakeven_stop" if active else "stop_loss", stop_loss, pnl_for(trade.direction, trade.entry_price, stop_loss), i - entry_i)
            if b.low <= base_tp:
                return ExitResult(trade.trade_index, rule_name, b.timestamp, "take_profit", base_tp, pnl_for(trade.direction, trade.entry_price, base_tp), i - entry_i)

    close_bar = bars[last_i]
    return ExitResult(trade.trade_index, rule_name, close_bar.timestamp, "close", close_bar.close, pnl_for(trade.direction, trade.entry_price, close_bar.close), last_i - entry_i)


def evaluate_trailing_rule(
    trade: TradeRecord,
    bars: list[PriceBar],
    index_map: dict[datetime, int],
    max_holding_bars: int,
    rule_name: str,
) -> ExitResult:
    base_tp = trade.take_profit
    r = distance_r(trade)
    stop_loss = trade.stop_loss
    active = False
    best_favorable = trade.entry_price

    entry_i = index_map[trade.entry_time]
    last_i = min(len(bars) - 1, entry_i + max_holding_bars)

    trailing_path: list[float] = []
    exit_i = last_i
    exit_reason = "close"
    exit_price = bars[last_i].close
    best_favorable_seen = trade.entry_price
    worst_adverse_seen = trade.entry_price

    for i in range(entry_i + 1, last_i + 1):
        b = bars[i]

        if trade.direction == "long":
            if b.high > best_favorable:
                best_favorable = b.high
            if b.low < worst_adverse_seen:
                worst_adverse_seen = b.low
            if (not active) and best_favorable >= trade.entry_price + r:
                active = True
            if active:
                stop_loss = max(stop_loss, best_favorable - r)
            trailing_path.append(stop_loss)
            if b.low <= stop_loss:
                exit_i = i
                exit_reason = "trailing_stop" if active else "stop_loss"
                exit_price = stop_loss
                best_favorable_seen = best_favorable
                break
            if b.high >= base_tp:
                exit_i = i
                exit_reason = "take_profit"
                exit_price = base_tp
                best_favorable_seen = best_favorable
                break
        else:
            if b.low < best_favorable:
                best_favorable = b.low
            if b.high > worst_adverse_seen:
                worst_adverse_seen = b.high
            if (not active) and best_favorable <= trade.entry_price - r:
                active = True
            if active:
                stop_loss = min(stop_loss, best_favorable + r)
            trailing_path.append(stop_loss)
            if b.high >= stop_loss:
                exit_i = i
                exit_reason = "trailing_stop" if active else "stop_loss"
                exit_price = stop_loss
                best_favorable_seen = best_favorable
                break
            if b.low <= base_tp:
                exit_i = i
                exit_reason = "take_profit"
                exit_price = base_tp
                best_favorable_seen = best_favorable
                break

    if exit_reason == "close":
        close_bar = bars[last_i]
        exit_i = last_i
        exit_price = close_bar.close
        if trade.direction == "long":
            best_favorable_seen = max(
                [trade.entry_price] + [bars[j].high for j in range(entry_i + 1, last_i + 1)]
            )
            worst_adverse_seen = min(
                [trade.entry_price] + [bars[j].low for j in range(entry_i + 1, last_i + 1)]
            )
        else:
            best_favorable_seen = min(
                [trade.entry_price] + [bars[j].low for j in range(entry_i + 1, last_i + 1)]
            )
            worst_adverse_seen = max(
                [trade.entry_price] + [bars[j].high for j in range(entry_i + 1, last_i + 1)]
            )

    used_hi = [bars[j].high for j in range(entry_i + 1, exit_i + 1)]
    used_lo = [bars[j].low for j in range(entry_i + 1, exit_i + 1)]
    no_entry_bar_exit = exit_i > entry_i
    within_max_hold = (exit_i - entry_i) <= max_holding_bars
    no_future_ref = True
    if trade.direction == "long":
        calc_best = max([trade.entry_price] + used_hi) if used_hi else trade.entry_price
        no_future_ref = abs(calc_best - best_favorable_seen) < 1e-12
        trailing_direction_ok = all(
            trailing_path[k] >= trailing_path[k - 1] for k in range(1, len(trailing_path))
        )
    else:
        calc_best = min([trade.entry_price] + used_lo) if used_lo else trade.entry_price
        no_future_ref = abs(calc_best - best_favorable_seen) < 1e-12
        trailing_direction_ok = all(
            trailing_path[k] <= trailing_path[k - 1] for k in range(1, len(trailing_path))
        )

    diagnostics = {
        "entry_index": entry_i,
        "exit_index": exit_i,
        "best_favorable_price_seen": best_favorable_seen,
        "worst_adverse_price_seen": worst_adverse_seen,
        "trailing_stop_final": stop_loss,
        "entry_bar_exit": not no_entry_bar_exit,
        "within_max_holding_bars": within_max_hold,
        "no_future_ref_in_best_favorable": no_future_ref,
        "trailing_direction_ok": trailing_direction_ok,
        "leak_check_passed": (no_entry_bar_exit and within_max_hold and no_future_ref),
    }
    return ExitResult(
        trade.trade_index,
        rule_name,
        bars[exit_i].timestamp,
        exit_reason,
        exit_price,
        pnl_for(trade.direction, trade.entry_price, exit_price),
        exit_i - entry_i,
        diagnostics=diagnostics,
    )


def _safe_iso(value: datetime | None) -> str:
    return value.isoformat() if value is not None else ""


def summarize_rule(rule_name: str, results: list[ExitResult], baseline_map: dict[int, float]) -> dict[str, Any]:
    pnls = [r.pnl for r in results]
    win_count = sum(1 for p in pnls if p > 0)
    loss_count = sum(1 for p in pnls if p < 0)
    exit_counts = Counter(r.exit_reason for r in results)

    improved = 0
    worsened = 0
    unchanged = 0
    for r in results:
        base = baseline_map[r.trade_index]
        if r.pnl > base:
            improved += 1
        elif r.pnl < base:
            worsened += 1
        else:
            unchanged += 1

    return {
        "rule_name": rule_name,
        "trade_count": len(results),
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": (win_count / len(results) * 100.0) if results else 0.0,
        "total_pnl": sum(pnls),
        "average_pnl": (sum(pnls) / len(results)) if results else 0.0,
        "median_pnl": median(pnls) if pnls else 0.0,
        "exit_reason_counts": dict(exit_counts),
        "average_holding_bars": (sum(r.holding_bars for r in results) / len(results)) if results else 0.0,
        "max_holding_bars": max((r.holding_bars for r in results), default=0),
        "improved_trade_count": improved,
        "worsened_trade_count": worsened,
        "unchanged_trade_count": unchanged,
    }


def issue_improvement_counts(results: list[ExitResult], baseline_map: dict[int, float], issue_map: dict[int, str], issue: str) -> dict[str, int]:
    improved = worsened = unchanged = total = 0
    for r in results:
        if issue_map.get(r.trade_index, "") != issue:
            continue
        total += 1
        base = baseline_map[r.trade_index]
        if r.pnl > base:
            improved += 1
        elif r.pnl < base:
            worsened += 1
        else:
            unchanged += 1
    return {
        "issue": issue,
        "trade_count": total,
        "improved": improved,
        "worsened": worsened,
        "unchanged": unchanged,
    }


def main() -> int:
    args = parse_args()

    price_csv = Path(args.price_csv)
    trade_logs = Path(args.trade_logs)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sl_multipliers = parse_multiplier_list(args.sl_multiplier_list, "sl-multiplier-list")
    tp_multipliers = parse_multiplier_list(args.tp_multiplier_list, "tp-multiplier-list")

    bars, index_map = load_price_bars(price_csv)
    trades = load_trade_records(trade_logs)
    issue_map = load_issue_map(trade_logs)

    if not trades:
        raise RuntimeError("No usable trade rows found in trade_logs")

    baseline_results: list[ExitResult] = []
    for t in trades:
        exit_time = t.baseline_exit_time or t.entry_time
        holding = 0
        if t.entry_time in index_map and t.baseline_exit_time in index_map:
            holding = max(0, index_map[t.baseline_exit_time] - index_map[t.entry_time])
        baseline_results.append(
            ExitResult(
                trade_index=t.trade_index,
                rule_name="baseline_fixed_exit",
                exit_time=exit_time,
                exit_reason=t.baseline_exit_reason or "unknown",
                exit_price=t.entry_price + t.baseline_pnl if t.direction == "long" else t.entry_price - t.baseline_pnl,
                pnl=t.baseline_pnl,
                holding_bars=holding,
            )
        )

    baseline_map = {r.trade_index: r.pnl for r in baseline_results}
    all_rule_results: dict[str, list[ExitResult]] = {"baseline_fixed_exit": baseline_results}

    for slm in sl_multipliers:
        name = f"wider_sl_fixed_tp_slx{slm:g}"
        all_rule_results[name] = [
            evaluate_fixed_rule(t, bars, index_map, args.max_holding_bars, scaled_levels(t, slm, 1.0)[0], scaled_levels(t, slm, 1.0)[1], name)
            for t in trades
        ]

    for tpm in tp_multipliers:
        name = f"fixed_sl_wider_tp_tpx{tpm:g}"
        all_rule_results[name] = [
            evaluate_fixed_rule(t, bars, index_map, args.max_holding_bars, scaled_levels(t, 1.0, tpm)[0], scaled_levels(t, 1.0, tpm)[1], name)
            for t in trades
        ]

    for slm in sl_multipliers:
        for tpm in tp_multipliers:
            name = f"wider_sl_wider_tp_slx{slm:g}_tpx{tpm:g}"
            all_rule_results[name] = [
                evaluate_fixed_rule(t, bars, index_map, args.max_holding_bars, scaled_levels(t, slm, tpm)[0], scaled_levels(t, slm, tpm)[1], name)
                for t in trades
            ]

    if args.include_breakeven:
        name = "breakeven_after_1R"
        all_rule_results[name] = [evaluate_breakeven_rule(t, bars, index_map, args.max_holding_bars, name) for t in trades]

    if args.include_trailing:
        name = "simple_trailing_after_1R"
        all_rule_results[name] = [evaluate_trailing_rule(t, bars, index_map, args.max_holding_bars, name) for t in trades]

    summaries = [summarize_rule(name, results, baseline_map) for name, results in all_rule_results.items()]

    issue_focus = ["sl_tp_too_fixed", "htf_against_entry", "entry_ok"]
    issue_summary_by_rule: dict[str, dict[str, dict[str, int]]] = {}
    for name, results in all_rule_results.items():
        issue_summary_by_rule[name] = {issue: issue_improvement_counts(results, baseline_map, issue_map, issue) for issue in issue_focus}

    out_csv = output_dir / "counterfactual_exit_analysis.csv"
    out_md = output_dir / "counterfactual_exit_analysis.md"
    out_details_csv = output_dir / "counterfactual_exit_trade_details.csv"
    out_audit_md = output_dir / "counterfactual_exit_audit.md"

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "rule_name",
            "trade_count",
            "win_count",
            "loss_count",
            "win_rate",
            "total_pnl",
            "average_pnl",
            "median_pnl",
            "exit_reason_counts",
            "average_holding_bars",
            "max_holding_bars",
            "improved_trade_count",
            "worsened_trade_count",
            "unchanged_trade_count",
            "issue_improvement_summary",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in summaries:
            row_copy = dict(row)
            row_copy["exit_reason_counts"] = json.dumps(row_copy["exit_reason_counts"], ensure_ascii=False)
            row_copy["issue_improvement_summary"] = json.dumps(issue_summary_by_rule[row_copy["rule_name"]], ensure_ascii=False)
            writer.writerow(row_copy)

    baseline_by_trade = {t.trade_index: t for t in trades}
    baseline_result_by_trade = {r.trade_index: r for r in baseline_results}
    trailing_results = all_rule_results.get("simple_trailing_after_1R", [])
    trailing_by_trade = {r.trade_index: r for r in trailing_results}

    with out_details_csv.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "trade_index",
            "signal_type",
            "entry_time",
            "baseline_exit_time",
            "baseline_exit_reason",
            "baseline_pnl",
            "counterfactual_rule",
            "cf_exit_time",
            "cf_exit_reason",
            "cf_pnl",
            "pnl_diff",
            "holding_bars",
            "max_holding_bars",
            "entry_price",
            "initial_stop_loss",
            "initial_take_profit",
            "best_favorable_price_seen",
            "worst_adverse_price_seen",
            "trailing_stop_final",
            "leak_check_passed",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for trade in trades:
            base = baseline_result_by_trade[trade.trade_index]
            cf = trailing_by_trade.get(trade.trade_index)
            notes: list[str] = []
            if cf is None:
                writer.writerow(
                    {
                        "trade_index": trade.trade_index,
                        "signal_type": trade.signal_type,
                        "entry_time": _safe_iso(trade.entry_time),
                        "baseline_exit_time": _safe_iso(base.exit_time),
                        "baseline_exit_reason": base.exit_reason,
                        "baseline_pnl": base.pnl,
                        "counterfactual_rule": "simple_trailing_after_1R",
                        "cf_exit_time": "",
                        "cf_exit_reason": "",
                        "cf_pnl": "",
                        "pnl_diff": "",
                        "holding_bars": "",
                        "max_holding_bars": args.max_holding_bars,
                        "entry_price": trade.entry_price,
                        "initial_stop_loss": trade.stop_loss,
                        "initial_take_profit": trade.take_profit,
                        "best_favorable_price_seen": "",
                        "worst_adverse_price_seen": "",
                        "trailing_stop_final": "",
                        "leak_check_passed": False,
                        "notes": "simple_trailing_after_1R was not requested",
                    }
                )
                continue
            d = cf.diagnostics or {}
            if d.get("entry_bar_exit", False):
                notes.append("entry_bar_exit_detected")
            if not d.get("within_max_holding_bars", True):
                notes.append("max_holding_bars_violation")
            if not d.get("no_future_ref_in_best_favorable", True):
                notes.append("future_ref_suspected")
            if not d.get("trailing_direction_ok", True):
                notes.append("trailing_direction_violation")
            writer.writerow(
                {
                    "trade_index": trade.trade_index,
                    "signal_type": trade.signal_type,
                    "entry_time": _safe_iso(trade.entry_time),
                    "baseline_exit_time": _safe_iso(base.exit_time),
                    "baseline_exit_reason": base.exit_reason,
                    "baseline_pnl": base.pnl,
                    "counterfactual_rule": "simple_trailing_after_1R",
                    "cf_exit_time": _safe_iso(cf.exit_time),
                    "cf_exit_reason": cf.exit_reason,
                    "cf_pnl": cf.pnl,
                    "pnl_diff": cf.pnl - base.pnl,
                    "holding_bars": cf.holding_bars,
                    "max_holding_bars": args.max_holding_bars,
                    "entry_price": trade.entry_price,
                    "initial_stop_loss": trade.stop_loss,
                    "initial_take_profit": trade.take_profit,
                    "best_favorable_price_seen": d.get("best_favorable_price_seen", ""),
                    "worst_adverse_price_seen": d.get("worst_adverse_price_seen", ""),
                    "trailing_stop_final": d.get("trailing_stop_final", ""),
                    "leak_check_passed": bool(d.get("leak_check_passed", False)),
                    "notes": ";".join(notes),
                }
            )

    baseline_trade_count_match = len(baseline_results) == len(trades)
    baseline_pnl_match = all(abs(t.baseline_pnl - baseline_result_by_trade[t.trade_index].pnl) < 1e-12 for t in trades)
    baseline_exit_reason_match = all(
        t.baseline_exit_reason == baseline_result_by_trade[t.trade_index].exit_reason for t in trades
    )

    top_lines: list[str] = []
    if trailing_results:
        diffs: list[tuple[TradeRecord, ExitResult, float]] = []
        for t in trades:
            cf = trailing_by_trade[t.trade_index]
            diffs.append((t, cf, cf.pnl - t.baseline_pnl))
        improved = sorted(diffs, key=lambda x: x[2], reverse=True)[:10]
        worsened = sorted(diffs, key=lambda x: x[2])[:10]
        top_lines.extend(
            [
                "# Counterfactual Exit Audit",
                "",
                "## Baseline Consistency",
                f"- baseline_trade_count_match: {baseline_trade_count_match}",
                f"- baseline_pnl_match: {baseline_pnl_match}",
                f"- baseline_exit_reason_match: {baseline_exit_reason_match}",
                "",
                "## simple_trailing_after_1R Top 10 Improved",
            ]
        )
        for t, cf, d in improved:
            top_lines.append(
                f"- trade_index={t.trade_index}, signal={t.signal_type}, entry={_safe_iso(t.entry_time)}, baseline_pnl={t.baseline_pnl:.6f}, cf_pnl={cf.pnl:.6f}, diff={d:.6f}, base_exit={t.baseline_exit_reason}, cf_exit={cf.exit_reason}, hold={cf.holding_bars}"
            )
        top_lines.append("")
        top_lines.append("## simple_trailing_after_1R Top 10 Worsened")
        for t, cf, d in worsened:
            top_lines.append(
                f"- trade_index={t.trade_index}, signal={t.signal_type}, entry={_safe_iso(t.entry_time)}, baseline_pnl={t.baseline_pnl:.6f}, cf_pnl={cf.pnl:.6f}, diff={d:.6f}, base_exit={t.baseline_exit_reason}, cf_exit={cf.exit_reason}, hold={cf.holding_bars}"
            )
    else:
        top_lines.extend(
            [
                "# Counterfactual Exit Audit",
                "",
                "simple_trailing_after_1R was not requested; audit ranking was skipped.",
            ]
        )
    out_audit_md.write_text("\n".join(top_lines) + "\n", encoding="utf-8")

    lines = [
        "# Counterfactual Exit Analysis",
        "",
        "## 注意",
        "- これは既存entry固定の後追い分析である。",
        "- これは実際のBacktestRunner結果ではない。",
        "- 手数料・スリッページ・スワップ未反映。",
        "- spread=0.2 pips fallback 前提の構造検証データに依存する。",
        "- 収益性評価ではなく exit改善候補の構造検証である。",
        "- htf_against_entry が一定数あるため、exit改善だけで採用判断しない。",
        "- 次に本物のHTFContext導入と比較する必要がある。",
        "",
        "## Summary",
        f"- price_csv: {price_csv}",
        f"- trade_logs: {trade_logs}",
        f"- trade_count: {len(trades)}",
        f"- rules: {[s['rule_name'] for s in summaries]}",
        "",
        "## Rule Metrics",
    ]

    for s in summaries:
        lines.extend(
            [
                f"- {s['rule_name']}: trade_count={s['trade_count']}, win_rate={s['win_rate']:.2f}, total_pnl={s['total_pnl']:.6f}, avg_pnl={s['average_pnl']:.6f}, median_pnl={s['median_pnl']:.6f}, improved={s['improved_trade_count']}, worsened={s['worsened_trade_count']}, unchanged={s['unchanged_trade_count']}, avg_holding_bars={s['average_holding_bars']:.2f}, max_holding_bars={s['max_holding_bars']}, exit_reason_counts={s['exit_reason_counts']}",
                f"  - issue_improvement(sl_tp_too_fixed / htf_against_entry / entry_ok): {issue_summary_by_rule[s['rule_name']]}",
            ]
        )

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[done] output_csv={out_csv}")
    print(f"[done] output_md={out_md}")
    print(f"[done] output_details_csv={out_details_csv}")
    print(f"[done] output_audit_md={out_audit_md}")
    print(f"[summary] trade_count={len(trades)}, rules={len(summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
