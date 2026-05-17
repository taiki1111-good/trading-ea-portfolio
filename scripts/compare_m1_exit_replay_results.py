#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

M5_REFERENCE_TOTAL_PNL = {
    "baseline_fixed_exit": -0.351,
    "simple_trailing_after_1R": 2.732,
    "simple_trailing_after_1R_conservative": 0.508,
    "simple_trailing_after_1R_next_bar_activation": -0.077,
}

RULE_ORDER = [
    "baseline_fixed_exit",
    "simple_trailing_after_1R",
    "simple_trailing_after_1R_conservative",
    "simple_trailing_after_1R_next_bar_activation",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare M1 exit replay results across rules.")
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-md", required=True)
    return parser.parse_args()


def _load_summary(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))
    out = dict(row)
    out["exit_reason_counts"] = json.loads(str(row["exit_reason_counts"]))
    numeric_keys = [
        "original_trade_count", "accepted_trade_count", "skipped_entry_count", "skipped_due_to_open_position_count",
        "win_rate", "total_pnl", "average_pnl", "median_pnl", "average_holding_minutes", "max_holding_minutes",
    ]
    for k in numeric_keys:
        if k in out:
            v = out[k]
            out[k] = float(v) if k in {"win_rate", "total_pnl", "average_pnl", "median_pnl", "average_holding_minutes"} else int(float(v))
    return out


def _load_trades(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["accepted_entry"] = str(r["accepted_entry"]).lower() == "true"
        hm = str(r.get("holding_minutes", "")).strip()
        r["holding_minutes"] = int(hm) if hm else None
    return rows


def _immediate_stop_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [r for r in rows if r["accepted_entry"]]
    hm1 = sum(1 for r in accepted if (r["holding_minutes"] is not None and r["holding_minutes"] <= 1))
    hm2 = sum(1 for r in accepted if (r["holding_minutes"] is not None and r["holding_minutes"] <= 2))
    stop_hm2 = sum(
        1
        for r in accepted
        if r.get("m1_exit_reason") == "stop_loss" and r["holding_minutes"] is not None and r["holding_minutes"] <= 2
    )
    by_signal = Counter(
        r.get("signal_type", "")
        for r in accepted
        if r.get("m1_exit_reason") == "stop_loss" and r["holding_minutes"] is not None and r["holding_minutes"] <= 2
    )
    return {
        "holding_minutes_le_1_count": hm1,
        "holding_minutes_le_2_count": hm2,
        "stop_loss_and_holding_minutes_le_2_count": stop_hm2,
        "immediate_stop_loss_by_signal_type": dict(by_signal),
    }


def main() -> int:
    args = parse_args()
    root = Path(args.input_root)

    rows_out: list[dict[str, Any]] = []
    baseline_total = None

    for rule in RULE_ORDER:
        rule_dir = root / rule
        summary = _load_summary(rule_dir / "m1_exit_replay_summary.csv")
        trades = _load_trades(rule_dir / "m1_exit_replay_trades.csv")
        imm = _immediate_stop_stats(trades)
        exits = summary["exit_reason_counts"]

        if rule == "baseline_fixed_exit":
            baseline_total = float(summary["total_pnl"])
        if baseline_total is None:
            raise RuntimeError("baseline_fixed_exit must be processed first")

        row = {
            "rule": rule,
            "entry_time_mode": summary.get("entry_time_mode", ""),
            "entry_timeframe_minutes": int(float(summary.get("entry_timeframe_minutes", 0))) if summary.get("entry_timeframe_minutes", "") != "" else "",
            "original_trade_count": summary["original_trade_count"],
            "accepted_trade_count": summary["accepted_trade_count"],
            "skipped_entry_count": summary["skipped_entry_count"],
            "skipped_due_to_open_position_count": summary["skipped_due_to_open_position_count"],
            "win_rate": float(summary["win_rate"]),
            "total_pnl": float(summary["total_pnl"]),
            "average_pnl": float(summary["average_pnl"]),
            "median_pnl": float(summary["median_pnl"]),
            "exit_reason_counts": exits,
            "average_holding_minutes": float(summary["average_holding_minutes"]),
            "max_holding_minutes": int(summary["max_holding_minutes"]),
            "delta_vs_m1_baseline": float(summary["total_pnl"]) - float(baseline_total),
            "delta_vs_m5_same_rule": float(summary["total_pnl"]) - M5_REFERENCE_TOTAL_PNL[rule],
            "stop_loss_count": int(exits.get("stop_loss", 0)),
            "trailing_stop_count": int(exits.get("trailing_stop", 0)),
            "take_profit_count": int(exits.get("take_profit", 0)),
            "holding_minutes_le_1_count": imm["holding_minutes_le_1_count"],
            "holding_minutes_le_2_count": imm["holding_minutes_le_2_count"],
            "stop_loss_and_holding_minutes_le_2_count": imm["stop_loss_and_holding_minutes_le_2_count"],
            "immediate_stop_loss_by_signal_type": imm["immediate_stop_loss_by_signal_type"],
        }
        rows_out.append(row)

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        fields = list(rows_out[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows_out:
            x = dict(r)
            x["exit_reason_counts"] = json.dumps(x["exit_reason_counts"], ensure_ascii=False)
            x["immediate_stop_loss_by_signal_type"] = json.dumps(x["immediate_stop_loss_by_signal_type"], ensure_ascii=False)
            w.writerow(x)

    lines = [
        "# M1 Exit Replay Rule Comparison",
        "",
        "## 注意",
        "- spread=0.2 pips fallback 前提。",
        "- 手数料・スリッページ・スワップ未反映。",
        "- 収益性評価ではなく、exit候補の構造比較。",
        "",
        "## Rule Metrics",
    ]
    for r in rows_out:
        lines.append(
            f"- {r['rule']} (entry_time_mode={r['entry_time_mode']}, timeframe_min={r['entry_timeframe_minutes']}): accepted={r['accepted_trade_count']}, skipped={r['skipped_entry_count']}, win_rate={r['win_rate']:.4f}, total_pnl={r['total_pnl']:.6f}, avg_pnl={r['average_pnl']:.6f}, median_pnl={r['median_pnl']:.6f}, exits={r['exit_reason_counts']}, avg_hold={r['average_holding_minutes']:.4f}, max_hold={r['max_holding_minutes']}, delta_vs_m1_baseline={r['delta_vs_m1_baseline']:.6f}, delta_vs_m5_same_rule={r['delta_vs_m5_same_rule']:.6f}"
        )

    lines.extend(["", "## Immediate Stop Tendency"])
    for r in rows_out:
        lines.append(
            f"- {r['rule']}: hold<=1={r['holding_minutes_le_1_count']}, hold<=2={r['holding_minutes_le_2_count']}, stop_loss_and_hold<=2={r['stop_loss_and_holding_minutes_le_2_count']}, by_signal={r['immediate_stop_loss_by_signal_type']}"
        )

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[done] output_csv={out_csv}")
    print(f"[done] output_md={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
