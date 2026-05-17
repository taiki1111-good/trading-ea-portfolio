#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = ["entry_time", "exit_time", "pnl"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze Risk/Stop v0.2 counterfactuals from existing trade logs.")
    p.add_argument("--trade-logs", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--pip-size", type=float, default=0.01)
    p.add_argument("--daily-loss-stop-pips", default="20,30,50")
    p.add_argument("--consecutive-loss-stop-counts", default="2,3")
    return p.parse_args()


def _parse_int_list(raw: str, label: str) -> list[int]:
    values: list[int] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            value = int(text)
        except ValueError as exc:
            raise ValueError(f"{label} must be comma-separated integers: {raw}") from exc
        values.append(value)
    if not values:
        raise ValueError(f"{label} must not be empty")
    if any(v <= 0 for v in values):
        raise ValueError(f"{label} must contain positive integers: {values}")
    return sorted(set(values))


def _require_columns(df: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _to_utc(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors="coerce")


def load_trade_logs(path: Path, pip_size: float) -> pd.DataFrame:
    if pip_size <= 0:
        raise ValueError(f"pip_size must be positive: {pip_size}")

    df = pd.read_csv(path)
    _require_columns(df, REQUIRED_COLUMNS, "trade_logs")
    out = df.copy()
    out["entry_time_utc"] = _to_utc(out["entry_time"])
    out["exit_time_utc"] = _to_utc(out["exit_time"])
    if out["entry_time_utc"].isna().any():
        raise ValueError("trade_logs has invalid entry_time values after UTC conversion")
    if out["exit_time_utc"].isna().any():
        raise ValueError("trade_logs has invalid exit_time values after UTC conversion")

    out["pnl"] = pd.to_numeric(out["pnl"], errors="coerce").fillna(0.0)
    out["direction"] = out["direction"] if "direction" in out.columns else ""
    out["trade_id"] = out["trade_id"] if "trade_id" in out.columns else range(1, len(out) + 1)
    out["trade_id_sort"] = pd.to_numeric(out["trade_id"], errors="coerce").fillna(0).astype(int)
    out = out.sort_values(["exit_time_utc", "entry_time_utc", "trade_id_sort"], kind="stable").reset_index(drop=True)

    out["trade_date_utc"] = out["exit_time_utc"].dt.strftime("%Y-%m-%d")
    out["pnl_pips"] = out["pnl"] / pip_size
    out["daily_pips_before_trade"] = 0.0
    out["daily_pips_after_trade"] = 0.0
    out["consecutive_loss_count_after_trade"] = 0
    out["daily_loss_triggered_thresholds"] = ""
    out["consecutive_loss_triggered_thresholds"] = ""
    return out


def compute_trade_diagnostics(
    trades: pd.DataFrame, daily_thresholds: list[int], consecutive_thresholds: list[int]
) -> tuple[pd.DataFrame, dict[tuple[str, int], dict[str, float]]]:
    out = trades.copy()
    summary: dict[tuple[str, int], dict[str, float]] = {}
    for th in daily_thresholds:
        summary[("daily_loss_stop", th)] = {"stopped": set(), "avoided_pips": 0.0, "missed_pips": 0.0, "trigger_count": 0}
    for th in consecutive_thresholds:
        summary[("consecutive_loss_stop", th)] = {
            "stopped": set(),
            "avoided_pips": 0.0,
            "missed_pips": 0.0,
            "trigger_count": 0,
        }

    for _, day_df in out.groupby("trade_date_utc", sort=False):
        indices = day_df.index.tolist()
        daily_total = 0.0
        loss_streak = 0
        daily_triggered: dict[int, bool] = {th: False for th in daily_thresholds}
        consecutive_triggered: dict[int, bool] = {th: False for th in consecutive_thresholds}

        for pos, idx in enumerate(indices):
            pnl_pips = float(out.at[idx, "pnl_pips"])
            out.at[idx, "daily_pips_before_trade"] = daily_total
            daily_total += pnl_pips
            out.at[idx, "daily_pips_after_trade"] = daily_total

            if pnl_pips < 0:
                loss_streak += 1
            else:
                loss_streak = 0
            out.at[idx, "consecutive_loss_count_after_trade"] = loss_streak

            daily_triggered_now: list[str] = []
            for th in daily_thresholds:
                if not daily_triggered[th] and daily_total <= -float(th):
                    daily_triggered[th] = True
                    daily_triggered_now.append(str(th))
                    info = summary[("daily_loss_stop", th)]
                    info["trigger_count"] += 1
                    for stopped_idx in indices[pos + 1 :]:
                        info["stopped"].add(stopped_idx)

            consecutive_triggered_now: list[str] = []
            for th in consecutive_thresholds:
                if not consecutive_triggered[th] and loss_streak >= th:
                    consecutive_triggered[th] = True
                    consecutive_triggered_now.append(str(th))
                    info = summary[("consecutive_loss_stop", th)]
                    info["trigger_count"] += 1
                    for stopped_idx in indices[pos + 1 :]:
                        info["stopped"].add(stopped_idx)

            out.at[idx, "daily_loss_triggered_thresholds"] = "|".join(daily_triggered_now)
            out.at[idx, "consecutive_loss_triggered_thresholds"] = "|".join(consecutive_triggered_now)

    for key, info in summary.items():
        for idx in info["stopped"]:
            pnl_pips = float(out.at[idx, "pnl_pips"])
            if pnl_pips < 0:
                info["avoided_pips"] += -pnl_pips
            elif pnl_pips > 0:
                info["missed_pips"] += pnl_pips

    return out, summary


def build_summary_rows(summary: dict[tuple[str, int], dict[str, float]], pip_size: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (stop_type, threshold), info in sorted(summary.items(), key=lambda x: (x[0][0], x[0][1])):
        avoided_pips = float(info["avoided_pips"])
        missed_pips = float(info["missed_pips"])
        net_pips = avoided_pips - missed_pips
        rows.append(
            {
                "stop_type": stop_type,
                "threshold": int(threshold),
                "stopped_trade_count": int(len(info["stopped"])),
                "avoided_loss_pips": avoided_pips,
                "missed_profit_pips": missed_pips,
                "net_counterfactual_effect_pips": net_pips,
                "avoided_loss_pnl": avoided_pips * pip_size,
                "missed_profit_pnl": missed_pips * pip_size,
                "net_counterfactual_effect_pnl": net_pips * pip_size,
                "trigger_count": int(info["trigger_count"]),
            }
        )
    return pd.DataFrame(rows)


def write_markdown(path: Path, summary_df: pd.DataFrame) -> None:
    lines = [
        "# Risk/Stop v0.2 Counterfactual Summary",
        "",
        "- これは既存trade_logsの後処理診断であり、収益性確認ではない。",
        "- Risk/Stopは本体停止ロジックではない。",
        "- 代表月単独で本採用判断しない。",
        "- lot sizing未導入のため評価限界がある。",
        "",
        "| stop_type | threshold | stopped_trade_count | avoided_loss_pips | missed_profit_pips | net_counterfactual_effect_pips | avoided_loss_pnl | missed_profit_pnl | net_counterfactual_effect_pnl | trigger_count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in summary_df.iterrows():
        lines.append(
            f"| {row['stop_type']} | {int(row['threshold'])} | {int(row['stopped_trade_count'])} | "
            f"{float(row['avoided_loss_pips']):.6f} | {float(row['missed_profit_pips']):.6f} | {float(row['net_counterfactual_effect_pips']):.6f} | "
            f"{float(row['avoided_loss_pnl']):.10f} | {float(row['missed_profit_pnl']):.10f} | {float(row['net_counterfactual_effect_pnl']):.10f} | {int(row['trigger_count'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis(
    trade_logs: Path,
    output_dir: Path,
    pip_size: float,
    daily_thresholds: list[int],
    consecutive_thresholds: list[int],
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trades = load_trade_logs(trade_logs, pip_size)
    analyzed, summary_raw = compute_trade_diagnostics(trades, daily_thresholds, consecutive_thresholds)

    trade_out = output_dir / "risk_stop_v2_trade_analysis.csv"
    trade_cols = [
        "trade_id",
        "entry_time",
        "exit_time",
        "trade_date_utc",
        "direction",
        "pnl",
        "pnl_pips",
        "daily_pips_before_trade",
        "daily_pips_after_trade",
        "consecutive_loss_count_after_trade",
        "daily_loss_triggered_thresholds",
        "consecutive_loss_triggered_thresholds",
    ]
    analyzed[trade_cols].to_csv(trade_out, index=False, encoding="utf-8")

    summary_df = build_summary_rows(summary_raw, pip_size)
    summary_out = output_dir / "risk_stop_v2_summary.csv"
    summary_df.to_csv(summary_out, index=False, encoding="utf-8")

    md_out = output_dir / "risk_stop_v2_summary.md"
    write_markdown(md_out, summary_df)
    return trade_out, summary_out, md_out


def main() -> int:
    args = parse_args()
    daily_thresholds = _parse_int_list(args.daily_loss_stop_pips, "daily_loss_stop_pips")
    consecutive_thresholds = _parse_int_list(args.consecutive_loss_stop_counts, "consecutive_loss_stop_counts")
    trade_out, summary_out, md_out = run_analysis(
        trade_logs=Path(args.trade_logs),
        output_dir=Path(args.output_dir),
        pip_size=args.pip_size,
        daily_thresholds=daily_thresholds,
        consecutive_thresholds=consecutive_thresholds,
    )
    print(f"[done] trade_analysis={trade_out}")
    print(f"[done] summary_csv={summary_out}")
    print(f"[done] summary_md={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
