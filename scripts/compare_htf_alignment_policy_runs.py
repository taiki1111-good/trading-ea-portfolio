#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EntryKey:
    direction: str
    entry_time: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare entry set differences between HTF alignment policy runs.")
    p.add_argument("--base-run-dir", required=True, help="Base run directory path.")
    p.add_argument("--compare-run-dir", action="append", required=True, help="Compare run directory path. Repeatable.")
    p.add_argument("--output-csv", required=True)
    p.add_argument("--output-md", required=True)
    return p.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_summary(run_dir: Path) -> dict[str, Any]:
    rows = read_csv_rows(run_dir / "backtest_summary.csv")
    if not rows:
        raise RuntimeError(f"empty summary: {run_dir}")
    return rows[0]


def normalize_ts(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return s


def parse_ts(raw: str) -> datetime | None:
    text = normalize_ts(raw)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def entry_key_from_trade_row(row: dict[str, Any]) -> EntryKey:
    direction = str(row.get("direction") or row.get("signal_type") or "").strip()
    if direction.endswith("_entry"):
        direction = direction.replace("_entry", "")
    return EntryKey(direction=direction, entry_time=normalize_ts(str(row.get("entry_time", "")).strip()))


def collect_entry_keys(trades: list[dict[str, Any]]) -> set[EntryKey]:
    return {entry_key_from_trade_row(r) for r in trades if entry_key_from_trade_row(r).entry_time}


def collect_total_pnl(trades: list[dict[str, Any]]) -> float:
    total = 0.0
    for r in trades:
        try:
            total += float(str(r.get("pnl", "")).strip())
        except Exception:
            continue
    return total


def shifted_5min_count(base_only: set[EntryKey], compare_only: set[EntryKey]) -> int:
    base_index = {(k.direction, k.entry_time): k for k in base_only}
    c = 0
    for item in compare_only:
        dt = parse_ts(item.entry_time)
        if dt is None:
            continue
        probe = dt + timedelta(minutes=5)
        key = (item.direction, probe.isoformat())
        if key in base_index:
            c += 1
    return c


def as_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key, "")).strip().lower()


def _is_htf_rejection_trace(row: dict[str, Any]) -> bool:
    fail_stage = _text(row, "fail_stage")
    reason = _text(row, "decision_reason")
    filter_reason = _text(row, "htf_filter_reason")
    joined = " ".join([fail_stage, reason, filter_reason])
    if "direction_alignment" in fail_stage:
        return True
    keywords = ["htf", "reject", "rejected", "neutral", "strict", "filter", "against", "mismatch"]
    return any(k in joined for k in keywords)


def neutral_counts(decision_rows: list[dict[str, Any]]) -> tuple[int, int]:
    passed = 0
    rejected = 0
    for r in decision_rows:
        htf_enabled = as_bool(r.get("htf_filter_enabled")) is True
        htf_bias_neutral = _text(r, "htf_bias") == "neutral"
        policy = _text(r, "htf_neutral_policy")
        aligned = as_bool(r.get("htf_direction_aligned"))
        entry_signal = as_bool(r.get("entry_signal"))
        trade_ok = as_bool(r.get("trade_ok"))
        has_entry_candidate = entry_signal is True or trade_ok is True

        if (
            htf_enabled
            and htf_bias_neutral
            and policy == "permissive"
            and aligned is True
            and has_entry_candidate
        ):
            passed += 1

        if (
            htf_enabled
            and htf_bias_neutral
            and policy == "strict"
            and aligned is False
            and _is_htf_rejection_trace(r)
        ):
            rejected += 1
    return passed, rejected


def compare_pair(base_run: Path, comp_run: Path) -> dict[str, Any]:
    base_summary = load_summary(base_run)
    comp_summary = load_summary(comp_run)

    base_trades = read_csv_rows(base_run / "trade_logs.csv")
    comp_trades = read_csv_rows(comp_run / "trade_logs.csv")
    comp_decisions = read_csv_rows(comp_run / "decision_logs.csv")

    base_keys = collect_entry_keys(base_trades)
    comp_keys = collect_entry_keys(comp_trades)

    common = base_keys & comp_keys
    comp_only = comp_keys - base_keys
    base_only = base_keys - comp_keys
    shifted = shifted_5min_count(base_only, comp_only)
    neutral_passed, neutral_rejected = neutral_counts(comp_decisions)

    base_pnl = collect_total_pnl(base_trades)
    comp_pnl = collect_total_pnl(comp_trades)

    return {
        "base_run_id": base_summary.get("run_id", base_run.name),
        "compare_run_id": comp_summary.get("run_id", comp_run.name),
        "base_trade_count": len(base_keys),
        "compare_trade_count": len(comp_keys),
        "common_count": len(common),
        "compare_only_count": len(comp_only),
        "base_only_count": len(base_only),
        "shifted_5min_count": shifted,
        "neutral_passed_count": neutral_passed,
        "neutral_rejected_count": neutral_rejected,
        "total_pnl_diff": comp_pnl - base_pnl,
        "notes": "structure validation only; not profitability confirmation",
    }


def main() -> int:
    args = parse_args()
    base_run = Path(args.base_run_dir)
    compare_runs = [Path(p) for p in args.compare_run_dir]

    rows = [compare_pair(base_run, c) for c in compare_runs]

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "base_run_id",
        "compare_run_id",
        "base_trade_count",
        "compare_trade_count",
        "common_count",
        "compare_only_count",
        "base_only_count",
        "shifted_5min_count",
        "neutral_passed_count",
        "neutral_rejected_count",
        "total_pnl_diff",
        "notes",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    lines = [
        "# HTF Alignment Policy Entry Set Diff",
        "",
        "- structure validation only (not profitability confirmation)",
        "- spread=0.2 pips fallback, commission/slippage/swap not reflected",
        "",
    ]
    for r in rows:
        lines.append(
            f"- base={r['base_run_id']} compare={r['compare_run_id']} "
            f"base_trade_count={r['base_trade_count']} compare_trade_count={r['compare_trade_count']} "
            f"common_count={r['common_count']} compare_only_count={r['compare_only_count']} "
            f"base_only_count={r['base_only_count']} shifted_5min_count={r['shifted_5min_count']} "
            f"neutral_passed_count={r['neutral_passed_count']} neutral_rejected_count={r['neutral_rejected_count']} "
            f"total_pnl_diff={r['total_pnl_diff']:.6f}"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[done] output_csv={out_csv}")
    print(f"[done] output_md={out_md}")
    print(f"[summary] compared_pairs={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
