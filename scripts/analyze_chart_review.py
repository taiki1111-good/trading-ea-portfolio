#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ISSUE_CATEGORIES = [
    "entry_ok",
    "exit_too_early",
    "htf_against_entry",
    "range_noise_breakout",
    "entry_too_late",
    "sl_tp_too_fixed",
    "unclear",
]

ENTRY_ISSUE_CATEGORIES = {"entry_too_late", "htf_against_entry", "range_noise_breakout"}
EXIT_ISSUE_CATEGORIES = {"exit_too_early", "sl_tp_too_fixed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze visual chart review CSV for MTF review summary.")
    parser.add_argument("--review-csv", required=True, help="Path to chart_review_template.csv")
    parser.add_argument("--output-dir", required=True, help="Directory to save analysis CSV/MD")
    return parser.parse_args()


def norm(value: Any, default: str = "(empty)") -> str:
    text = str(value or "").strip()
    return text if text else default


def to_float(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except Exception:
        return None


def pnl_sign(value: Any) -> str:
    p = to_float(value)
    if p is None:
        return "unknown"
    if p > 0:
        return "positive"
    if p < 0:
        return "negative"
    return "zero"


def counter_to_sorted_dict(counter: Counter[str]) -> dict[str, int]:
    return {k: counter[k] for k in sorted(counter.keys())}


def cross_tab(rows: list[dict[str, str]], left: str, right: str) -> dict[str, dict[str, int]]:
    table: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        l = norm(r.get(left))
        rr = norm(r.get(right))
        table[l][rr] += 1
    return {k: counter_to_sorted_dict(v) for k, v in sorted(table.items(), key=lambda x: x[0])}


def detect_priority(counts: Counter[str], high_priority_issues: int) -> tuple[str, list[str]]:
    htf = counts.get("htf_against_entry", 0)
    exit_like = counts.get("sl_tp_too_fixed", 0) + counts.get("exit_too_early", 0)
    noise = counts.get("range_noise_breakout", 0)
    late = counts.get("entry_too_late", 0)

    category_max = 0
    if counts:
        category_max = max(counts.values())

    reasons: list[str] = []
    if htf == category_max or htf >= max(1, high_priority_issues // 2):
        reasons.append("htf_against_entry が最多または high priority で多い")
        return "本物のH1/H4 HTFContext導入を優先候補", reasons
    if exit_like == category_max or exit_like >= max(1, high_priority_issues // 2):
        reasons.append("sl_tp_too_fixed / exit_too_early が多い")
        return "exit strategy experiments を優先候補", reasons
    if noise == category_max or noise >= max(1, category_max):
        reasons.append("range_noise_breakout が多い")
        return "breakout条件・range filter改善を優先候補", reasons
    if late == category_max or late >= max(1, category_max):
        reasons.append("entry_too_late が多い")
        return "temporal_lag / entry timing改善を優先候補", reasons

    reasons.append("明確な最多傾向が弱く、複合要因")
    return "複合課題のため、exit戦略とHTF整合性を並行で比較検証", reasons


def main() -> int:
    args = parse_args()
    review_path = Path(args.review_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not review_path.exists():
        raise FileNotFoundError(f"review CSV not found: {review_path}")

    with review_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [{k: str(v) for k, v in row.items()} for row in reader]

    review_count = len(rows)

    visual_entry_counts = Counter(norm(r.get("visual_entry_ok")) for r in rows)
    visual_exit_counts = Counter(norm(r.get("visual_exit_ok")) for r in rows)
    issue_counts = Counter(norm(r.get("issue_category")) for r in rows)
    priority_counts = Counter(norm(r.get("priority")).lower() for r in rows)

    signal_issue = cross_tab(rows, "signal_type", "issue_category")
    exit_issue = cross_tab(rows, "exit_reason", "issue_category")

    pnl_issue_table: dict[str, Counter[str]] = defaultdict(Counter)
    lag_issue_table: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        p_sign = pnl_sign(r.get("pnl"))
        issue = norm(r.get("issue_category"))
        lag = norm(r.get("temporal_lag_bars"))
        pnl_issue_table[p_sign][issue] += 1
        lag_issue_table[lag][issue] += 1

    pnl_issue = {k: counter_to_sorted_dict(v) for k, v in sorted(pnl_issue_table.items(), key=lambda x: x[0])}
    lag_issue = {k: counter_to_sorted_dict(v) for k, v in sorted(lag_issue_table.items(), key=lambda x: x[0])}

    high_priority_issue_count = sum(1 for r in rows if norm(r.get("priority")).lower() == "high")
    entry_problem_count = sum(issue_counts.get(cat, 0) for cat in ENTRY_ISSUE_CATEGORIES)
    exit_problem_count = sum(issue_counts.get(cat, 0) for cat in EXIT_ISSUE_CATEGORIES)
    htf_against_entry_count = issue_counts.get("htf_against_entry", 0)
    range_noise_count = issue_counts.get("range_noise_breakout", 0)

    priority_label, priority_reasons = detect_priority(issue_counts, high_priority_issue_count)

    analysis = {
        "review_count": review_count,
        "visual_entry_ok_counts": counter_to_sorted_dict(visual_entry_counts),
        "visual_exit_ok_counts": counter_to_sorted_dict(visual_exit_counts),
        "issue_category_counts": counter_to_sorted_dict(issue_counts),
        "priority_counts": counter_to_sorted_dict(priority_counts),
        "signal_type_x_issue_category": signal_issue,
        "exit_reason_x_issue_category": exit_issue,
        "pnl_sign_x_issue_category": pnl_issue,
        "temporal_lag_bars_x_issue_category": lag_issue,
        "high_priority_issue_count": high_priority_issue_count,
        "entry_problem_count": entry_problem_count,
        "exit_problem_count": exit_problem_count,
        "htf_against_entry_count": htf_against_entry_count,
        "range_noise_breakout_count": range_noise_count,
        "tentative_improvement_priority": priority_label,
        "tentative_priority_reasons": priority_reasons,
    }

    out_csv = output_dir / "chart_review_analysis.csv"
    out_md = output_dir / "chart_review_analysis.md"

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        for k, v in analysis.items():
            writer.writerow({"metric": k, "value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v})

    lines = [
        "# Chart Review Analysis",
        "",
        "## 注意",
        "- これは30件の目視レビューであり、統計的な収益性評価ではない。",
        "- H1/H4は現行BT判断には未使用であり、visual reference only。",
        "- 現行BTはM5-derived pipeline windowで動いている。",
        "- 今回の目的は、次の設計判断の材料作成である。",
        "",
        "## Summary",
        f"- review_count: {review_count}",
        f"- visual_entry_ok counts: {counter_to_sorted_dict(visual_entry_counts)}",
        f"- visual_exit_ok counts: {counter_to_sorted_dict(visual_exit_counts)}",
        f"- issue_category counts: {counter_to_sorted_dict(issue_counts)}",
        f"- priority counts: {counter_to_sorted_dict(priority_counts)}",
        f"- signal_type x issue_category: {signal_issue}",
        f"- exit_reason x issue_category: {exit_issue}",
        f"- pnl sign x issue_category: {pnl_issue}",
        f"- temporal_lag_bars x issue_category: {lag_issue}",
        f"- high priority issue count: {high_priority_issue_count}",
        f"- entry問題件数: {entry_problem_count}",
        f"- exit問題件数: {exit_problem_count}",
        f"- HTF逆行件数: {htf_against_entry_count}",
        f"- range/noise件数: {range_noise_count}",
        "",
        "## 暫定改善優先度",
        f"- 判定: {priority_label}",
        f"- 根拠: {priority_reasons}",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[done] review_csv={review_path}")
    print(f"[done] output_csv={out_csv}")
    print(f"[done] output_md={out_md}")
    print(f"[summary] review_count={review_count}, tentative_priority={priority_label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
