#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import pandas as pd


TARGET_REQUIRED_COLUMNS = [
    "validation_target_id",
    "period_start",
    "period_end",
    "period_type",
    "run_id",
    "run_dir",
    "module_name",
    "candidate_name",
    "policy",
    "notes",
]

SUMMARY_COLUMNS = [
    "validation_run_id",
    "validation_target_id",
    "module_name",
    "candidate_name",
    "policy",
    "period_start",
    "period_end",
    "period_type",
    "run_id",
    "run_dir",
    "trade_count",
    "total_pnl",
    "average_pnl",
    "win_rate",
    "max_drawdown",
    "avoided_loss",
    "missed_profit",
    "net_counterfactual_effect",
    "label_coverage",
    "stopped_trade_count",
    "sample_size_flag",
    "cost_adjusted_flag",
    "data_quality_flag",
    "decision_status",
    "decision_reason",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Validation v0.2 summary from existing run outputs.")
    p.add_argument("--targets", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--validation-run-id", default="validation_v0_2_minimal")
    return p.parse_args()


def _require_columns(df: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _to_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _sample_size_flag(trade_count: float | None) -> str:
    if trade_count is None:
        return "unknown"
    if trade_count < 20:
        return "low"
    if trade_count < 50:
        return "medium"
    return "normal"


def _read_backtest_summary(run_dir: Path) -> dict[str, float | None] | None:
    path = run_dir / "backtest_summary.csv"
    if not path.exists():
        return None
    rows = pd.read_csv(path)
    if rows.empty:
        return None
    row = rows.iloc[0]
    return {
        "trade_count": _to_float(row.get("trade_count")),
        "total_pnl": _to_float(row.get("total_pnl")),
        "average_pnl": _to_float(row.get("average_pnl")),
        "win_rate": _to_float(row.get("win_rate")),
    }


def _read_trade_metrics(run_dir: Path) -> dict[str, float | None] | None:
    path = run_dir / "trade_logs.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if "pnl" not in df.columns:
        return None
    pnl = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)
    trade_count = float(len(df))
    total_pnl = float(pnl.sum())
    average_pnl = float(total_pnl / trade_count) if trade_count else None
    win_rate = float((pnl > 0).sum() / trade_count) if trade_count else None
    return {
        "trade_count": trade_count,
        "total_pnl": total_pnl,
        "average_pnl": average_pnl,
        "win_rate": win_rate,
    }


def _read_risk_stop_summary(run_dir: Path) -> dict[str, float | None] | None:
    candidates = [
        run_dir / "risk_stop_v2_analysis" / "risk_stop_v2_summary.csv",
        run_dir / "risk_stop_v2_summary.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return None
    df = pd.read_csv(path)
    if df.empty:
        return {
            "net_counterfactual_effect": None,
            "avoided_loss": None,
            "missed_profit": None,
            "stopped_trade_count": None,
            "trigger_count": None,
        }
    return {
        "net_counterfactual_effect": float(pd.to_numeric(df.get("net_counterfactual_effect_pips"), errors="coerce").fillna(0.0).sum()),
        "avoided_loss": float(pd.to_numeric(df.get("avoided_loss_pips"), errors="coerce").fillna(0.0).sum()),
        "missed_profit": float(pd.to_numeric(df.get("missed_profit_pips"), errors="coerce").fillna(0.0).sum()),
        "stopped_trade_count": float(pd.to_numeric(df.get("stopped_trade_count"), errors="coerce").fillna(0.0).sum()),
        "trigger_count": float(pd.to_numeric(df.get("trigger_count"), errors="coerce").fillna(0.0).sum()),
    }


def _detect_cost_adjusted(run_dir: Path) -> bool:
    return (run_dir / "cost_adjusted_summary.csv").exists()


def _decide(
    module_name: str,
    period_type: str,
    trade_count: float | None,
    sample_size_flag: str,
    cost_adjusted_flag: bool,
    risk_stop_metrics: dict[str, float | None] | None,
) -> tuple[str, str]:
    if trade_count is None:
        return "insufficient_sample", "missing trade_count/source"
    if sample_size_flag == "low":
        return "insufficient_sample", f"trade_count={int(trade_count)} is low sample"

    module = module_name.strip().lower()
    if module in {"htf_v2", "sr_v2", "session_v2"}:
        return "keep_as_explanation_layer", "diagnostic label layer; no filter promotion from representative month only"

    if module == "risk_stop_v2":
        if risk_stop_metrics is None:
            return "continue_diagnostic", "risk_stop summary missing; keep diagnostic"
        net = risk_stop_metrics.get("net_counterfactual_effect")
        trigger_count = risk_stop_metrics.get("trigger_count")
        if net is not None and net < 0:
            return "pause_no_go", f"net_counterfactual_effect={net:.6f} < 0"
        if trigger_count is not None and trigger_count <= 0:
            return "continue_diagnostic", "no stop trigger in current period"
        return "continue_diagnostic", "needs adverse-month confirmation"

    if module == "exit_policy":
        if not cost_adjusted_flag:
            return "needs_cost_adjusted_check", "cost_adjusted_summary missing"
        return "continue_diagnostic", "cost adjusted check available; keep multi-month diagnostic"

    if period_type == "representative_month":
        return "continue_diagnostic", "representative month alone; implementation decision is deferred"
    return "continue_diagnostic", "default diagnostic status"


def build_summary(targets_csv: Path, output_dir: Path, validation_run_id: str) -> tuple[Path, Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = pd.read_csv(targets_csv)
    _require_columns(targets, TARGET_REQUIRED_COLUMNS, "validation_targets")

    summary_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    warnings_all: list[str] = []

    for _, row in targets.iterrows():
        target_id = str(row["validation_target_id"])
        run_dir = Path(str(row["run_dir"]))
        module_name = str(row["module_name"])
        period_type = str(row["period_type"])
        warnings: list[str] = []

        metrics = _read_backtest_summary(run_dir)
        if metrics is None:
            warnings.append("backtest_summary.csv missing or unreadable; fallback to trade_logs.csv")
            metrics = _read_trade_metrics(run_dir)
        if metrics is None:
            warnings.append("trade_logs.csv missing or unreadable; core metrics left empty")
            metrics = {"trade_count": None, "total_pnl": None, "average_pnl": None, "win_rate": None}
            data_quality_flag = "missing_source"
        else:
            data_quality_flag = "ok"

        risk_metrics = None
        if module_name == "risk_stop_v2":
            risk_metrics = _read_risk_stop_summary(run_dir)
            if risk_metrics is None:
                warnings.append("risk_stop_v2_summary.csv missing for risk_stop_v2 module")

        cost_adjusted_flag = _detect_cost_adjusted(run_dir)
        sample_size_flag = _sample_size_flag(metrics.get("trade_count"))
        decision_status, decision_reason = _decide(
            module_name=module_name,
            period_type=period_type,
            trade_count=metrics.get("trade_count"),
            sample_size_flag=sample_size_flag,
            cost_adjusted_flag=cost_adjusted_flag,
            risk_stop_metrics=risk_metrics,
        )

        avoided_loss = risk_metrics.get("avoided_loss") if risk_metrics else None
        missed_profit = risk_metrics.get("missed_profit") if risk_metrics else None
        net_counterfactual_effect = risk_metrics.get("net_counterfactual_effect") if risk_metrics else None
        stopped_trade_count = risk_metrics.get("stopped_trade_count") if risk_metrics else None

        summary_row = {
            "validation_run_id": validation_run_id,
            "validation_target_id": target_id,
            "module_name": module_name,
            "candidate_name": str(row["candidate_name"]),
            "policy": str(row["policy"]),
            "period_start": str(row["period_start"]),
            "period_end": str(row["period_end"]),
            "period_type": period_type,
            "run_id": str(row["run_id"]),
            "run_dir": str(row["run_dir"]),
            "trade_count": metrics.get("trade_count"),
            "total_pnl": metrics.get("total_pnl"),
            "average_pnl": metrics.get("average_pnl"),
            "win_rate": metrics.get("win_rate"),
            "max_drawdown": None,
            "avoided_loss": avoided_loss,
            "missed_profit": missed_profit,
            "net_counterfactual_effect": net_counterfactual_effect,
            "label_coverage": None,
            "stopped_trade_count": stopped_trade_count,
            "sample_size_flag": sample_size_flag,
            "cost_adjusted_flag": cost_adjusted_flag,
            "data_quality_flag": data_quality_flag,
            "decision_status": decision_status,
            "decision_reason": decision_reason,
        }
        summary_rows.append(summary_row)

        warning_text = " | ".join(warnings)
        decision_rows.append(
            {
                "validation_target_id": target_id,
                "module_name": module_name,
                "decision_status": decision_status,
                "decision_reason": decision_reason,
                "warnings": warning_text,
            }
        )
        for w in warnings:
            warnings_all.append(f"{target_id}: {w}")

    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    decision_df = pd.DataFrame(
        decision_rows,
        columns=["validation_target_id", "module_name", "decision_status", "decision_reason", "warnings"],
    )

    layer_rows: list[dict[str, str]] = []
    for module_name, gdf in summary_df.groupby("module_name", dropna=False):
        statuses = list(gdf["decision_status"].dropna().astype(str).unique())
        if "pause_no_go" in statuses:
            current_status = "pause_no_go"
            next_action = "multi_month_recheck_before_any_integration"
        elif "keep_as_explanation_layer" in statuses:
            current_status = "keep_as_explanation_layer"
            next_action = "continue_diagnostic_multi_month"
        elif "needs_cost_adjusted_check" in statuses:
            current_status = "needs_cost_adjusted_check"
            next_action = "prepare_cost_adjusted_summary"
        elif "insufficient_sample" in statuses:
            current_status = "insufficient_sample"
            next_action = "collect_more_samples"
        else:
            current_status = "continue_diagnostic"
            next_action = "continue_diagnostic"
        layer_rows.append(
            {
                "module_name": str(module_name),
                "current_status": current_status,
                "next_action": next_action,
                "notes": "derived from minimal validation summary rules",
            }
        )

    layer_df = pd.DataFrame(layer_rows, columns=["module_name", "current_status", "next_action", "notes"])

    summary_csv = output_dir / "validation_v0_2_summary.csv"
    decision_csv = output_dir / "validation_v0_2_decision_log.csv"
    layer_csv = output_dir / "validation_v0_2_layer_status.csv"
    summary_md = output_dir / "validation_v0_2_summary.md"

    summary_df.to_csv(summary_csv, index=False, encoding="utf-8")
    decision_df.to_csv(decision_csv, index=False, encoding="utf-8")
    layer_df.to_csv(layer_csv, index=False, encoding="utf-8")
    _write_markdown(summary_md, summary_df, warnings_all)
    return summary_csv, decision_csv, layer_csv, summary_md


def _write_markdown(path: Path, summary_df: pd.DataFrame, warnings: list[str]) -> None:
    lines = [
        "# Validation v0.2 Summary",
        "",
        "- これは既存run/summaryの後処理集約であり、収益性確認ではない。",
        "- 代表月単独で本採用判断しない。",
        "- 不足ファイルがある場合はwarning扱い。",
        "- HTF/SR/Session/RiskStopは現時点で本体filter化保留。",
        "",
    ]
    if warnings:
        lines.append("## Warnings")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.extend(
        [
            "| validation_target_id | module_name | run_id | trade_count | total_pnl | average_pnl | win_rate | sample_size_flag | decision_status | decision_reason |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for _, row in summary_df.iterrows():
        lines.append(
            f"| {row['validation_target_id']} | {row['module_name']} | {row['run_id']} | {row['trade_count']} | "
            f"{row['total_pnl']} | {row['average_pnl']} | {row['win_rate']} | {row['sample_size_flag']} | "
            f"{row['decision_status']} | {row['decision_reason']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    summary_csv, decision_csv, layer_csv, summary_md = build_summary(
        targets_csv=Path(args.targets),
        output_dir=Path(args.output_dir),
        validation_run_id=args.validation_run_id,
    )
    print(f"[done] summary_csv={summary_csv}")
    print(f"[done] decision_log_csv={decision_csv}")
    print(f"[done] layer_status_csv={layer_csv}")
    print(f"[done] summary_md={summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
