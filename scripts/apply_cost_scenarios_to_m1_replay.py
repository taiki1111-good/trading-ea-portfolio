#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CostScenarioConfig:
    scenario_name: str
    instrument: str
    pip_size: float
    slippage_pips_round_turn: float
    commission_pips_round_turn: float
    additional_spread_pips: float
    spread_already_included: bool
    swap_mode: str
    notes: str


REQUIRED_COLUMNS = [
    "m1_replay_pnl",
    "accepted_entry",
    "rule",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply cost scenarios to existing m1 replay trades as post-process evaluation."
    )
    parser.add_argument("--input-trades", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--scenario-name", required=True)
    parser.add_argument("--instrument", default="USDJPY")
    parser.add_argument("--pip-size", type=float, default=0.01)
    parser.add_argument("--slippage-pips-round-turn", type=float, default=0.0)
    parser.add_argument("--commission-pips-round-turn", type=float, default=0.0)
    parser.add_argument("--additional-spread-pips", type=float, default=0.0)
    parser.add_argument(
        "--spread-already-included",
        action="store_true",
        help="Mark that baseline spread is already included in source pnl. Avoid double-counting by defaulting additional spread to 0.",
    )
    parser.add_argument("--swap-mode", choices=["none", "note_only"], default="none")
    parser.add_argument("--notes", default="")
    return parser.parse_args()


def _parse_bool(text: str) -> bool:
    return str(text).strip().lower() in {"1", "true", "yes", "y"}


def _parse_optional_float(text: str) -> float | None:
    s = str(text).strip()
    if s == "":
        return None
    return float(s)


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
        if missing:
            raise ValueError(
                f"input csv missing required columns: {missing}. required={REQUIRED_COLUMNS}"
            )
        return list(reader)


def apply_cost_adjustment(
    rows: list[dict[str, str]],
    cfg: CostScenarioConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    adjusted_rows: list[dict[str, Any]] = []
    summary_by_rule: dict[str, dict[str, Any]] = {}

    total_cost_pips_each_trade = (
        cfg.additional_spread_pips
        + cfg.slippage_pips_round_turn
        + cfg.commission_pips_round_turn
    )

    for row in rows:
        accepted = _parse_bool(row.get("accepted_entry", ""))
        pnl = _parse_optional_float(row.get("m1_replay_pnl", ""))
        if not accepted or pnl is None:
            continue

        gross_pnl = pnl
        gross_pips = gross_pnl / cfg.pip_size
        net_pips = gross_pips - total_cost_pips_each_trade
        net_pnl = net_pips * cfg.pip_size

        out_row = dict(row)
        out_row["gross_pnl"] = gross_pnl
        out_row["gross_pips"] = gross_pips
        out_row["additional_spread_pips"] = cfg.additional_spread_pips
        out_row["slippage_pips_round_turn"] = cfg.slippage_pips_round_turn
        out_row["commission_pips_round_turn"] = cfg.commission_pips_round_turn
        out_row["total_cost_pips"] = total_cost_pips_each_trade
        out_row["net_pips"] = net_pips
        out_row["net_pnl"] = net_pnl
        out_row["cost_scenario_name"] = cfg.scenario_name
        out_row["spread_already_included"] = cfg.spread_already_included
        out_row["swap_mode"] = cfg.swap_mode
        adjusted_rows.append(out_row)

        rule = str(row.get("rule", "")).strip() or "unknown_rule"
        item = summary_by_rule.setdefault(
            rule,
            {
                "cost_scenario_name": cfg.scenario_name,
                "rule": rule,
                "accepted_trade_count": 0,
                "gross_total_pnl": 0.0,
                "gross_total_pips": 0.0,
                "total_cost_pips": 0.0,
                "net_total_pips": 0.0,
                "net_total_pnl": 0.0,
                "gross_win_count": 0,
                "net_win_count": 0,
                "notes": cfg.notes,
            },
        )
        item["accepted_trade_count"] += 1
        item["gross_total_pnl"] += gross_pnl
        item["gross_total_pips"] += gross_pips
        item["total_cost_pips"] += total_cost_pips_each_trade
        item["net_total_pips"] += net_pips
        item["net_total_pnl"] += net_pnl
        if gross_pnl > 0:
            item["gross_win_count"] += 1
        if net_pnl > 0:
            item["net_win_count"] += 1

    summary_rows: list[dict[str, Any]] = []
    for _, item in sorted(summary_by_rule.items(), key=lambda kv: kv[0]):
        count = int(item["accepted_trade_count"])
        gross_avg = item["gross_total_pips"] / count if count > 0 else 0.0
        net_avg = item["net_total_pips"] / count if count > 0 else 0.0
        gross_wr = (item["gross_win_count"] / count * 100.0) if count > 0 else 0.0
        net_wr = (item["net_win_count"] / count * 100.0) if count > 0 else 0.0
        summary_rows.append(
            {
                "cost_scenario_name": item["cost_scenario_name"],
                "rule": item["rule"],
                "accepted_trade_count": count,
                "gross_total_pnl": item["gross_total_pnl"],
                "gross_total_pips": item["gross_total_pips"],
                "total_cost_pips": item["total_cost_pips"],
                "net_total_pips": item["net_total_pips"],
                "net_total_pnl": item["net_total_pnl"],
                "gross_average_pips": gross_avg,
                "net_average_pips": net_avg,
                "win_rate_gross": gross_wr,
                "win_rate_net": net_wr,
                "notes": item["notes"],
            }
        )

    return adjusted_rows, summary_rows


def write_cost_adjusted_trades(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_cost_adjusted_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "cost_scenario_name",
        "rule",
        "accepted_trade_count",
        "gross_total_pnl",
        "gross_total_pips",
        "total_cost_pips",
        "net_total_pips",
        "net_total_pnl",
        "gross_average_pips",
        "net_average_pips",
        "win_rate_gross",
        "win_rate_net",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_markdown(
    path: Path,
    cfg: CostScenarioConfig,
    summary_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Cost-Adjusted M1 Replay Summary",
        "",
        "## 注意",
        "- 本結果は構造検証であり、収益性確認ではない。",
        "- BacktestRunner本体へは未組み込みの後処理評価である。",
        "- swapはv0.1では実控除に入れていない（none/note_only）。",
        "",
        "## Scenario",
        f"- name: `{cfg.scenario_name}`",
        f"- instrument: `{cfg.instrument}`",
        f"- pip_size: `{cfg.pip_size}`",
        f"- spread_already_included: `{cfg.spread_already_included}`",
        f"- additional_spread_pips: `{cfg.additional_spread_pips}`",
        f"- slippage_pips_round_turn: `{cfg.slippage_pips_round_turn}`",
        f"- commission_pips_round_turn: `{cfg.commission_pips_round_turn}`",
        f"- swap_mode: `{cfg.swap_mode}`",
        f"- notes: `{cfg.notes}`",
        "",
        "## Rule Summary",
    ]
    if not summary_rows:
        lines.append("- accepted_entry=True かつ m1_replay_pnl が有効な行がありません。")
    else:
        for row in summary_rows:
            lines.append(
                "- "
                f"{row['rule']}: accepted={row['accepted_trade_count']}, "
                f"gross_total_pnl={row['gross_total_pnl']:.6f}, gross_total_pips={row['gross_total_pips']:.3f}, "
                f"total_cost_pips={row['total_cost_pips']:.3f}, net_total_pips={row['net_total_pips']:.3f}, "
                f"net_total_pnl={row['net_total_pnl']:.6f}, gross_avg_pips={row['gross_average_pips']:.3f}, "
                f"net_avg_pips={row['net_average_pips']:.3f}, win_rate_gross={row['win_rate_gross']:.2f}, "
                f"win_rate_net={row['win_rate_net']:.2f}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    cfg = CostScenarioConfig(
        scenario_name=args.scenario_name,
        instrument=args.instrument,
        pip_size=float(args.pip_size),
        slippage_pips_round_turn=float(args.slippage_pips_round_turn),
        commission_pips_round_turn=float(args.commission_pips_round_turn),
        additional_spread_pips=float(args.additional_spread_pips),
        spread_already_included=bool(args.spread_already_included),
        swap_mode=args.swap_mode,
        notes=args.notes,
    )

    input_path = Path(args.input_trades)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(input_path)
    adjusted_rows, summary_rows = apply_cost_adjustment(rows, cfg)

    out_trades = output_dir / "cost_adjusted_trades.csv"
    out_summary_csv = output_dir / "cost_adjusted_summary.csv"
    out_summary_md = output_dir / "cost_adjusted_summary.md"

    write_cost_adjusted_trades(out_trades, adjusted_rows)
    write_cost_adjusted_summary(out_summary_csv, summary_rows)
    write_summary_markdown(out_summary_md, cfg, summary_rows)

    print(f"[done] output_trades={out_trades}")
    print(f"[done] output_summary_csv={out_summary_csv}")
    print(f"[done] output_summary_md={out_summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
