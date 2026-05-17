#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from scripts.analyze_counterfactual_exits import ExitResult
from scripts.analyze_counterfactual_exits import TradeRecord
from scripts.analyze_counterfactual_exits import evaluate_fixed_rule
from scripts.analyze_counterfactual_exits import load_price_bars
from scripts.analyze_counterfactual_exits import load_trade_records
from scripts.analyze_counterfactual_exits import pnl_for

TRAILING_RULES = {
    "simple_trailing_after_1R",
    "simple_trailing_after_1R_conservative",
    "simple_trailing_after_1R_next_bar_activation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Position-aware counterfactual replay using existing entry candidates.")
    parser.add_argument("--price-csv", required=True)
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
    parser.add_argument("--max-holding-bars", required=True, type=int)
    return parser.parse_args()


def _safe_iso(v: Any) -> str:
    return v.isoformat() if v is not None else ""


def _distance_r(trade: TradeRecord) -> float:
    return abs(trade.entry_price - trade.stop_loss)


def evaluate_trailing_variant_rule(
    trade: TradeRecord,
    bars: list[Any],
    index_map: dict[Any, int],
    max_holding_bars: int,
    rule_name: str,
) -> ExitResult:
    entry_i = index_map[trade.entry_time]
    last_i = min(len(bars) - 1, entry_i + max_holding_bars)
    r = _distance_r(trade)
    stop_loss = trade.stop_loss
    base_tp = trade.take_profit
    best_favorable = trade.entry_price
    active = False
    activate_next_bar = False

    intrabar_ambiguous = False
    activation_and_stop_same_bar = False
    conservative_exit_applied = False
    ambiguity_note = ""
    trailing_path: list[float] = []
    worst_adverse = trade.entry_price

    for i in range(entry_i + 1, last_i + 1):
        b = bars[i]
        if activate_next_bar:
            active = True
            activate_next_bar = False

        if trade.direction == "long":
            prior_best = best_favorable
            best_favorable = max(best_favorable, b.high)
            worst_adverse = min(worst_adverse, b.low)
            activation_hit = best_favorable >= trade.entry_price + r
            same_bar_stop_hit = b.low <= stop_loss
            if activation_hit and same_bar_stop_hit and (not active):
                intrabar_ambiguous = True
                activation_and_stop_same_bar = True
                ambiguity_note = "long: 1R activation and stop reachable in same bar"
                if rule_name == "simple_trailing_after_1R_conservative":
                    conservative_exit_applied = True
                    return ExitResult(
                        trade.trade_index,
                        rule_name,
                        b.timestamp,
                        "stop_loss",
                        trade.stop_loss,
                        pnl_for(trade.direction, trade.entry_price, trade.stop_loss),
                        i - entry_i,
                        diagnostics={
                            "trailing_stop_final": trade.stop_loss,
                            "intrabar_ambiguous": intrabar_ambiguous,
                            "activation_and_stop_same_bar": activation_and_stop_same_bar,
                            "conservative_exit_applied": conservative_exit_applied,
                            "ambiguity_note": ambiguity_note,
                        },
                    )
            if activation_hit and (not active):
                if rule_name == "simple_trailing_after_1R_next_bar_activation":
                    activate_next_bar = True
                else:
                    active = True
            if active:
                stop_loss = max(stop_loss, best_favorable - r)
            trailing_path.append(stop_loss)
            if b.low <= stop_loss:
                return ExitResult(
                    trade.trade_index,
                    rule_name,
                    b.timestamp,
                    "trailing_stop" if active else "stop_loss",
                    stop_loss,
                    pnl_for(trade.direction, trade.entry_price, stop_loss),
                    i - entry_i,
                    diagnostics={
                        "trailing_stop_final": stop_loss,
                        "intrabar_ambiguous": intrabar_ambiguous,
                        "activation_and_stop_same_bar": activation_and_stop_same_bar,
                        "conservative_exit_applied": conservative_exit_applied,
                        "ambiguity_note": ambiguity_note,
                    },
                )
            if b.high >= base_tp:
                return ExitResult(
                    trade.trade_index,
                    rule_name,
                    b.timestamp,
                    "take_profit",
                    base_tp,
                    pnl_for(trade.direction, trade.entry_price, base_tp),
                    i - entry_i,
                    diagnostics={
                        "trailing_stop_final": stop_loss,
                        "intrabar_ambiguous": intrabar_ambiguous,
                        "activation_and_stop_same_bar": activation_and_stop_same_bar,
                        "conservative_exit_applied": conservative_exit_applied,
                        "ambiguity_note": ambiguity_note,
                    },
                )
            best_favorable = max(prior_best, best_favorable)
        else:
            prior_best = best_favorable
            best_favorable = min(best_favorable, b.low)
            worst_adverse = max(worst_adverse, b.high)
            activation_hit = best_favorable <= trade.entry_price - r
            same_bar_stop_hit = b.high >= stop_loss
            if activation_hit and same_bar_stop_hit and (not active):
                intrabar_ambiguous = True
                activation_and_stop_same_bar = True
                ambiguity_note = "short: 1R activation and stop reachable in same bar"
                if rule_name == "simple_trailing_after_1R_conservative":
                    conservative_exit_applied = True
                    return ExitResult(
                        trade.trade_index,
                        rule_name,
                        b.timestamp,
                        "stop_loss",
                        trade.stop_loss,
                        pnl_for(trade.direction, trade.entry_price, trade.stop_loss),
                        i - entry_i,
                        diagnostics={
                            "trailing_stop_final": trade.stop_loss,
                            "intrabar_ambiguous": intrabar_ambiguous,
                            "activation_and_stop_same_bar": activation_and_stop_same_bar,
                            "conservative_exit_applied": conservative_exit_applied,
                            "ambiguity_note": ambiguity_note,
                        },
                    )
            if activation_hit and (not active):
                if rule_name == "simple_trailing_after_1R_next_bar_activation":
                    activate_next_bar = True
                else:
                    active = True
            if active:
                stop_loss = min(stop_loss, best_favorable + r)
            trailing_path.append(stop_loss)
            if b.high >= stop_loss:
                return ExitResult(
                    trade.trade_index,
                    rule_name,
                    b.timestamp,
                    "trailing_stop" if active else "stop_loss",
                    stop_loss,
                    pnl_for(trade.direction, trade.entry_price, stop_loss),
                    i - entry_i,
                    diagnostics={
                        "trailing_stop_final": stop_loss,
                        "intrabar_ambiguous": intrabar_ambiguous,
                        "activation_and_stop_same_bar": activation_and_stop_same_bar,
                        "conservative_exit_applied": conservative_exit_applied,
                        "ambiguity_note": ambiguity_note,
                    },
                )
            if b.low <= base_tp:
                return ExitResult(
                    trade.trade_index,
                    rule_name,
                    b.timestamp,
                    "take_profit",
                    base_tp,
                    pnl_for(trade.direction, trade.entry_price, base_tp),
                    i - entry_i,
                    diagnostics={
                        "trailing_stop_final": stop_loss,
                        "intrabar_ambiguous": intrabar_ambiguous,
                        "activation_and_stop_same_bar": activation_and_stop_same_bar,
                        "conservative_exit_applied": conservative_exit_applied,
                        "ambiguity_note": ambiguity_note,
                    },
                )
            best_favorable = min(prior_best, best_favorable)

    close_bar = bars[last_i]
    return ExitResult(
        trade.trade_index,
        rule_name,
        close_bar.timestamp,
        "close",
        close_bar.close,
        pnl_for(trade.direction, trade.entry_price, close_bar.close),
        last_i - entry_i,
        diagnostics={
            "trailing_stop_final": stop_loss,
            "intrabar_ambiguous": intrabar_ambiguous,
            "activation_and_stop_same_bar": activation_and_stop_same_bar,
            "conservative_exit_applied": conservative_exit_applied,
            "ambiguity_note": ambiguity_note,
        },
    )


def _evaluate_for_rule(
    trade: TradeRecord,
    rule: str,
    bars: list[Any],
    index_map: dict[Any, int],
    max_holding_bars: int,
) -> ExitResult:
    if rule in TRAILING_RULES:
        return evaluate_trailing_variant_rule(trade, bars, index_map, max_holding_bars, rule)
    return evaluate_fixed_rule(
        trade,
        bars,
        index_map,
        max_holding_bars,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        rule_name=rule,
    )


def _load_independent_trailing_stats(trade_logs_path: Path) -> dict[str, Any] | None:
    details = trade_logs_path.parent / "counterfactual_exit" / "counterfactual_exit_trade_details.csv"
    if not details.exists():
        return None
    rows = list(csv.DictReader(details.open("r", encoding="utf-8", newline="")))
    if not rows:
        return None
    pnls = [float(r["cf_pnl"]) for r in rows if r.get("cf_pnl", "") != ""]
    return {
        "trade_count": len(pnls),
        "total_pnl": sum(pnls),
        "average_pnl": (sum(pnls) / len(pnls)) if pnls else 0.0,
        "median_pnl": median(pnls) if pnls else 0.0,
    }


def run_replay(
    trades: list[TradeRecord],
    bars: list[Any],
    index_map: dict[Any, int],
    rule: str,
    max_holding_bars: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = sorted(trades, key=lambda t: (t.entry_time, t.trade_index))
    open_until_i = -1
    rows: list[dict[str, Any]] = []

    for t in candidates:
        entry_i = index_map.get(t.entry_time)
        if entry_i is None:
            rows.append(
                {
                    "original_trade_index": t.trade_index,
                    "accepted_entry": False,
                    "skipped_reason": "entry_time_not_in_price",
                    "signal_type": t.signal_type,
                    "entry_time": _safe_iso(t.entry_time),
                    "original_exit_time": _safe_iso(t.baseline_exit_time),
                    "replay_exit_time": "",
                    "replay_exit_reason": "",
                    "original_pnl": t.baseline_pnl,
                    "replay_pnl": "",
                    "pnl_diff": "",
                    "holding_bars": "",
                    "rule": rule,
                    "entry_price": t.entry_price,
                    "replay_stop_loss": t.stop_loss,
                    "replay_take_profit": t.take_profit,
                    "trailing_stop_final": "",
                    "intrabar_ambiguous": False,
                    "activation_and_stop_same_bar": False,
                    "conservative_exit_applied": False,
                    "ambiguity_note": "",
                    "notes": "",
                }
            )
            continue
        if entry_i <= open_until_i:
            rows.append(
                {
                    "original_trade_index": t.trade_index,
                    "accepted_entry": False,
                    "skipped_reason": "skipped_due_to_open_position",
                    "signal_type": t.signal_type,
                    "entry_time": _safe_iso(t.entry_time),
                    "original_exit_time": _safe_iso(t.baseline_exit_time),
                    "replay_exit_time": "",
                    "replay_exit_reason": "",
                    "original_pnl": t.baseline_pnl,
                    "replay_pnl": "",
                    "pnl_diff": "",
                    "holding_bars": "",
                    "rule": rule,
                    "entry_price": t.entry_price,
                    "replay_stop_loss": t.stop_loss,
                    "replay_take_profit": t.take_profit,
                    "trailing_stop_final": "",
                    "intrabar_ambiguous": False,
                    "activation_and_stop_same_bar": False,
                    "conservative_exit_applied": False,
                    "ambiguity_note": "",
                    "notes": "",
                }
            )
            continue

        res = _evaluate_for_rule(t, rule, bars, index_map, max_holding_bars)
        exit_i = index_map.get(res.exit_time, entry_i)
        open_until_i = max(open_until_i, exit_i)
        d = res.diagnostics or {}
        rows.append(
            {
                "original_trade_index": t.trade_index,
                "accepted_entry": True,
                "skipped_reason": "",
                "signal_type": t.signal_type,
                "entry_time": _safe_iso(t.entry_time),
                "original_exit_time": _safe_iso(t.baseline_exit_time),
                "replay_exit_time": _safe_iso(res.exit_time),
                "replay_exit_reason": res.exit_reason,
                "original_pnl": t.baseline_pnl,
                "replay_pnl": res.pnl,
                "pnl_diff": res.pnl - t.baseline_pnl,
                "holding_bars": res.holding_bars,
                "rule": rule,
                "entry_price": t.entry_price,
                "replay_stop_loss": d.get("trailing_stop_final", t.stop_loss),
                "replay_take_profit": t.take_profit,
                "trailing_stop_final": d.get("trailing_stop_final", ""),
                "intrabar_ambiguous": bool(d.get("intrabar_ambiguous", False)),
                "activation_and_stop_same_bar": bool(d.get("activation_and_stop_same_bar", False)),
                "conservative_exit_applied": bool(d.get("conservative_exit_applied", False)),
                "ambiguity_note": d.get("ambiguity_note", ""),
                "notes": "",
            }
        )

    accepted = [r for r in rows if r["accepted_entry"]]
    skipped = [r for r in rows if not r["accepted_entry"]]
    replay_pnls = [float(r["replay_pnl"]) for r in accepted]
    exit_counts = Counter(str(r["replay_exit_reason"]) for r in accepted)
    overlap_free = True
    accepted_sorted = sorted(accepted, key=lambda r: r["entry_time"])
    last_exit = None
    for r in accepted_sorted:
        if last_exit is not None and r["entry_time"] <= last_exit:
            overlap_free = False
            break
        last_exit = r["replay_exit_time"]

    summary = {
        "rule": rule,
        "original_trade_count": len(rows),
        "accepted_trade_count": len(accepted),
        "skipped_entry_count": len(skipped),
        "skipped_due_to_open_position_count": sum(1 for r in skipped if r["skipped_reason"] == "skipped_due_to_open_position"),
        "win_count": sum(1 for p in replay_pnls if p > 0),
        "loss_count": sum(1 for p in replay_pnls if p < 0),
        "win_rate": (sum(1 for p in replay_pnls if p > 0) / len(replay_pnls) * 100.0) if replay_pnls else 0.0,
        "total_pnl": sum(replay_pnls),
        "average_pnl": (sum(replay_pnls) / len(replay_pnls)) if replay_pnls else 0.0,
        "median_pnl": median(replay_pnls) if replay_pnls else 0.0,
        "exit_reason_counts": dict(exit_counts),
        "average_holding_bars": (sum(int(r["holding_bars"]) for r in accepted if r["holding_bars"] != "") / len(accepted)) if accepted else 0.0,
        "max_holding_bars": max((int(r["holding_bars"]) for r in accepted if r["holding_bars"] != ""), default=0),
        "intrabar_ambiguous_count": sum(1 for r in accepted if r["intrabar_ambiguous"]),
        "activation_and_stop_same_bar_count": sum(1 for r in accepted if r["activation_and_stop_same_bar"]),
        "conservative_exit_applied_count": sum(1 for r in accepted if r["conservative_exit_applied"]),
        "accepted_plus_skipped_match": (len(accepted) + len(skipped)) == len(rows),
        "position_overlap_detected": not overlap_free,
        "entry_bar_exit_detected": any(int(r["holding_bars"]) == 0 for r in accepted if r["holding_bars"] != ""),
        "max_holding_violation_detected": any(int(r["holding_bars"]) > max_holding_bars for r in accepted if r["holding_bars"] != ""),
    }
    return rows, summary


def main() -> int:
    args = parse_args()
    price_csv = Path(args.price_csv)
    trade_logs = Path(args.trade_logs)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bars, index_map = load_price_bars(price_csv)
    trades = load_trade_records(trade_logs)
    if not trades:
        raise RuntimeError("No usable trade rows found in trade_logs")

    rows, summary = run_replay(trades, bars, index_map, args.rule, args.max_holding_bars)
    _, baseline_summary = run_replay(trades, bars, index_map, "baseline_fixed_exit", args.max_holding_bars)
    indep = _load_independent_trailing_stats(trade_logs)

    summary["delta_vs_baseline_total_pnl"] = summary["total_pnl"] - baseline_summary["total_pnl"]
    summary["delta_vs_baseline_win_rate"] = summary["win_rate"] - baseline_summary["win_rate"]
    if indep is not None and args.rule in TRAILING_RULES:
        summary["delta_vs_independent_trailing_total_pnl"] = summary["total_pnl"] - indep["total_pnl"]
        summary["delta_vs_independent_trailing_average_pnl"] = summary["average_pnl"] - indep["average_pnl"]
    else:
        summary["delta_vs_independent_trailing_total_pnl"] = ""
        summary["delta_vs_independent_trailing_average_pnl"] = ""

    trades_csv = out_dir / "position_aware_counterfactual_trades.csv"
    summary_csv = out_dir / "position_aware_counterfactual_summary.csv"
    summary_md = out_dir / "position_aware_counterfactual_summary.md"

    with trades_csv.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "original_trade_index", "accepted_entry", "skipped_reason", "signal_type", "entry_time",
            "original_exit_time", "replay_exit_time", "replay_exit_reason", "original_pnl", "replay_pnl",
            "pnl_diff", "holding_bars", "rule", "entry_price", "replay_stop_loss", "replay_take_profit",
            "trailing_stop_final", "intrabar_ambiguous", "activation_and_stop_same_bar", "conservative_exit_applied",
            "ambiguity_note", "notes",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        fields = list(summary.keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        row = dict(summary)
        row["exit_reason_counts"] = json.dumps(row["exit_reason_counts"], ensure_ascii=False)
        w.writerow(row)

    md_lines = [
        "# Position-aware Counterfactual Replay Summary",
        "",
        "## 注意",
        "- これは既存entry候補を使った後追い検証であり、正式なBacktestRunner統合ではない。",
        "- 同時保有なし（position保有中のentry候補はskip）で再生した構造検証。",
        "- M5 OHLC では intrabar sequence 不明のため、trailing activation/stop 同一バー曖昧性を監査する。",
        "- spread=0.2 pips fallback 前提、手数料・スリッページ・スワップ未反映。",
        "- 収益性評価ではなく exit改善候補の構造検証。",
        "",
        f"- rule: {args.rule}",
        f"- original_trade_count: {summary['original_trade_count']}",
        f"- accepted_trade_count: {summary['accepted_trade_count']}",
        f"- skipped_entry_count: {summary['skipped_entry_count']}",
        f"- skipped_due_to_open_position_count: {summary['skipped_due_to_open_position_count']}",
        f"- win_rate: {summary['win_rate']:.2f}",
        f"- total_pnl: {summary['total_pnl']:.6f}",
        f"- average_pnl: {summary['average_pnl']:.6f}",
        f"- median_pnl: {summary['median_pnl']:.6f}",
        f"- exit_reason_counts: {summary['exit_reason_counts']}",
        f"- intrabar_ambiguous_count: {summary['intrabar_ambiguous_count']}",
        f"- activation_and_stop_same_bar_count: {summary['activation_and_stop_same_bar_count']}",
        f"- conservative_exit_applied_count: {summary['conservative_exit_applied_count']}",
        f"- average_holding_bars: {summary['average_holding_bars']:.2f}",
        f"- max_holding_bars: {summary['max_holding_bars']}",
        f"- delta_vs_baseline_total_pnl: {summary['delta_vs_baseline_total_pnl']}",
        f"- delta_vs_baseline_win_rate: {summary['delta_vs_baseline_win_rate']}",
        f"- delta_vs_independent_trailing_total_pnl: {summary['delta_vs_independent_trailing_total_pnl']}",
        f"- delta_vs_independent_trailing_average_pnl: {summary['delta_vs_independent_trailing_average_pnl']}",
        "",
        "## Validation",
        f"- accepted_trade_count + skipped_entry_count == original_trade_count: {summary['accepted_plus_skipped_match']}",
        f"- position_overlap_detected: {summary['position_overlap_detected']}",
        f"- entry_bar_exit_detected: {summary['entry_bar_exit_detected']}",
        f"- max_holding_violation_detected: {summary['max_holding_violation_detected']}",
    ]
    summary_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[done] output_trades_csv={trades_csv}")
    print(f"[done] output_summary_csv={summary_csv}")
    print(f"[done] output_summary_md={summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
