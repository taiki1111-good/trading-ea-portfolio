#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd


SESSION_COLUMNS = [
    "session_v2_enabled",
    "session_policy",
    "hour_utc",
    "day_of_week",
    "session_label",
    "is_tokyo_session",
    "is_london_session",
    "is_new_york_session",
    "is_london_ny_overlap",
    "is_low_liquidity_hour",
    "session_risk_flag",
    "session_reason",
    "session_data_valid_flag",
]

GROUP_COLUMNS = [
    "session_label",
    "hour_utc",
    "day_of_week",
    "session_risk_flag",
    "is_low_liquidity_hour",
    "is_tokyo_session",
    "is_london_session",
    "is_new_york_session",
    "is_london_ny_overlap",
    "session_policy",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze Session v2 diagnostic trade decomposition from existing logs.")
    p.add_argument("--decision-logs", required=True)
    p.add_argument("--trade-logs", required=True)
    p.add_argument("--output-dir", required=True)
    return p.parse_args()


def _require_columns(df: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _to_utc(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors="coerce")


def _to_bool_or_none(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _normalize_group_value(group_col: str, value: Any) -> tuple[str, bool]:
    if group_col == "hour_utc":
        if pd.isna(value):
            return "unknown", True
        text = str(value).strip()
        try:
            hour = int(float(text))
        except ValueError:
            return "unknown", True
        if hour < 0 or hour > 23:
            return "unknown", True
        return str(hour), False

    bool_value = _to_bool_or_none(value)
    if bool_value is not None:
        return str(bool_value).lower(), False
    if pd.isna(value):
        return "unknown", False
    return str(value), False


def load_and_join(decision_logs: Path, trade_logs: Path) -> tuple[pd.DataFrame, int]:
    ddf = pd.read_csv(decision_logs)
    tdf = pd.read_csv(trade_logs)
    _require_columns(ddf, ["timestamp", *SESSION_COLUMNS], "decision_logs")
    _require_columns(tdf, ["entry_time", "pnl"], "trade_logs")

    ddf = ddf.copy()
    tdf = tdf.copy()
    ddf["timestamp_utc"] = _to_utc(ddf["timestamp"])
    tdf["entry_time_utc"] = _to_utc(tdf["entry_time"])
    if ddf["timestamp_utc"].isna().any():
        raise ValueError("decision_logs has invalid timestamp values after UTC conversion")
    if tdf["entry_time_utc"].isna().any():
        raise ValueError("trade_logs has invalid entry_time values after UTC conversion")

    ddf = ddf.drop_duplicates(subset=["timestamp_utc"], keep="last")

    joined = tdf.merge(
        ddf[["timestamp_utc", *SESSION_COLUMNS]],
        left_on="entry_time_utc",
        right_on="timestamp_utc",
        how="left",
    )
    unmatched_count = int(joined[SESSION_COLUMNS[0]].isna().sum())
    joined["trade_id"] = range(1, len(joined) + 1)
    joined["direction"] = joined["direction"] if "direction" in joined.columns else ""
    joined["pnl"] = pd.to_numeric(joined["pnl"], errors="coerce").fillna(0.0)
    joined["entry_time"] = joined["entry_time_utc"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    joined["entry_time"] = joined["entry_time"].str.replace(r"(\+|-)(\d{2})(\d{2})$", r"\1\2:\3", regex=True)
    return joined, unmatched_count


def build_group_summary(analysis_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    rows: list[dict[str, Any]] = []
    invalid_hour_count = 0
    for group_col in GROUP_COLUMNS:
        work = analysis_df[[group_col, "pnl"]].copy()
        normalized = work[group_col].apply(lambda x: _normalize_group_value(group_col, x))
        work[group_col] = normalized.apply(lambda t: t[0])
        if group_col == "hour_utc":
            invalid_hour_count += int(normalized.apply(lambda t: bool(t[1])).sum())
        grouped = work.groupby(group_col, dropna=False)
        for value, gdf in grouped:
            trade_count = int(len(gdf))
            total_pnl = float(gdf["pnl"].sum())
            average_pnl = float(total_pnl / trade_count) if trade_count else 0.0
            win_rate = float((gdf["pnl"] > 0).sum() / trade_count) if trade_count else 0.0
            rows.append(
                {
                    "group_name": group_col,
                    "group_value": str(value),
                    "trade_count": trade_count,
                    "total_pnl": total_pnl,
                    "average_pnl": average_pnl,
                    "win_rate": win_rate,
                }
            )
    return pd.DataFrame(rows), invalid_hour_count


def write_markdown(path: Path, summary_df: pd.DataFrame, unmatched_count: int, invalid_hour_count: int) -> None:
    lines = [
        "# Session v2 Diagnostic Trade Group Summary",
        "",
        "- これは既存ログの後処理診断であり、収益性確認ではない。",
        "- Session v2はentryを止めていない（diagnostic_only）。",
        "- session_label はUTC固定近似であり、DST厳密補正なし。",
        "- 実filter化判断ではない。",
        "",
    ]
    if unmatched_count > 0:
        lines.extend(
            [
                "## Warnings",
                f"- unmatched trades (entry_time not found in decision_logs timestamp): {unmatched_count}",
                "",
            ]
        )
    if invalid_hour_count > 0:
        if unmatched_count == 0:
            lines.append("## Warnings")
        lines.extend(
            [
                f"- invalid hour_utc values detected and mapped to unknown: {invalid_hour_count}",
                "",
            ]
        )
    lines.extend(
        [
            "| group_name | group_value | trade_count | total_pnl | average_pnl | win_rate |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in summary_df.iterrows():
        lines.append(
            f"| {row['group_name']} | {row['group_value']} | {int(row['trade_count'])} | "
            f"{float(row['total_pnl']):.10f} | {float(row['average_pnl']):.10f} | {float(row['win_rate']):.6f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis(decision_logs: Path, trade_logs: Path, output_dir: Path) -> tuple[Path, Path, Path, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_df, unmatched_count = load_and_join(decision_logs, trade_logs)

    analysis_out = output_dir / "session_v2_trade_analysis.csv"
    out_cols = ["trade_id", "entry_time", "direction", "pnl", *SESSION_COLUMNS]
    analysis_df[out_cols].to_csv(analysis_out, index=False, encoding="utf-8")

    group_df, invalid_hour_count = build_group_summary(analysis_df)
    group_out = output_dir / "session_v2_group_summary.csv"
    group_df.to_csv(group_out, index=False, encoding="utf-8")

    md_out = output_dir / "session_v2_group_summary.md"
    write_markdown(md_out, group_df, unmatched_count, invalid_hour_count)
    return analysis_out, group_out, md_out, unmatched_count


def main() -> int:
    args = parse_args()
    analysis_out, group_out, md_out, unmatched_count = run_analysis(
        decision_logs=Path(args.decision_logs),
        trade_logs=Path(args.trade_logs),
        output_dir=Path(args.output_dir),
    )
    print(f"[done] trade_analysis={analysis_out}")
    print(f"[done] group_summary_csv={group_out}")
    print(f"[done] group_summary_md={md_out}")
    print(f"[summary] unmatched_trades={unmatched_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
