#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close"]
OPTIONAL_COLUMNS = ["volume", "spread_pips", "source", "data_valid_flag"]


@dataclass
class DryRunResult:
    decision_logs: list[dict[str, Any]]
    event_logs: list[dict[str, Any]]
    state_logs: list[dict[str, Any]]
    warning_logs: list[dict[str, Any]]
    summary: dict[str, Any]


def _crosses_weekend(prev_ts: pd.Timestamp, current_ts: pd.Timestamp) -> bool:
    if current_ts <= prev_ts:
        return False
    for day in pd.date_range(prev_ts.floor("D"), current_ts.floor("D"), freq="D", tz="UTC"):
        if day.dayofweek >= 5:
            return True
    return False


def _classify_gap(prev_ts: pd.Timestamp, current_ts: pd.Timestamp) -> dict[str, Any]:
    gap_duration = current_ts - prev_ts
    if _crosses_weekend(prev_ts, current_ts):
        return {
            "gap_class": "expected_weekend_gap",
            "expected_gap_flag": True,
            "gap_duration": str(gap_duration),
            "previous_timestamp": prev_ts.isoformat(),
            "current_timestamp": current_ts.isoformat(),
            "gap_reason": "weekend_or_market_closure_candidate",
            "gap_action": "record_as_expected_gap",
            "gap_requires_investigation": False,
        }
    if current_ts > prev_ts:
        return {
            "gap_class": "ordinary_missing_bar_gap",
            "expected_gap_flag": False,
            "gap_duration": str(gap_duration),
            "previous_timestamp": prev_ts.isoformat(),
            "current_timestamp": current_ts.isoformat(),
            "gap_reason": "missing_bar_candidate",
            "gap_action": "investigate_missing_bars",
            "gap_requires_investigation": True,
        }
    return {
        "gap_class": "unknown_gap",
        "expected_gap_flag": False,
        "gap_duration": str(gap_duration),
        "previous_timestamp": prev_ts.isoformat(),
        "current_timestamp": current_ts.isoformat(),
        "gap_reason": "classification_unknown",
        "gap_action": "inspect_gap",
        "gap_requires_investigation": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CSV replay dry-run skeleton.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--warmup-start", required=True)
    parser.add_argument("--replay-start", required=True)
    parser.add_argument("--replay-end", required=True)
    parser.add_argument("--expected-timeframe-minutes", type=int, default=5)
    return parser.parse_args()


def _parse_utc_timestamp(raw: str) -> pd.Timestamp:
    return pd.to_datetime(raw, utc=True)


def _validate_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def load_and_prepare_input(csv_path: Path) -> tuple[pd.DataFrame, set[pd.Timestamp], set[pd.Timestamp]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"input CSV not found: {csv_path}")
    raw = pd.read_csv(csv_path)
    _validate_required_columns(raw)

    out_of_order_timestamps: set[pd.Timestamp] = set()
    parsed_original = pd.to_datetime(raw["timestamp"], utc=True)
    prev_ts: pd.Timestamp | None = None
    for ts in parsed_original:
        if prev_ts is not None and ts < prev_ts:
            out_of_order_timestamps.add(ts)
        prev_ts = ts

    df = raw.copy()
    df["timestamp"] = parsed_original
    df = df.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    duplicate_timestamps = set(df.loc[df["timestamp"].duplicated(keep=False), "timestamp"].tolist())
    return df, duplicate_timestamps, out_of_order_timestamps


def split_warmup_replay(
    df: pd.DataFrame,
    warmup_start: pd.Timestamp,
    replay_start: pd.Timestamp,
    replay_end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    warmup_mask = (df["timestamp"] >= warmup_start) & (df["timestamp"] < replay_start)
    replay_mask = (df["timestamp"] >= replay_start) & (df["timestamp"] < replay_end)
    return df.loc[warmup_mask].copy(), df.loc[replay_mask].copy()


def run_csv_replay_dry_run(
    df: pd.DataFrame,
    duplicate_timestamps: set[pd.Timestamp],
    out_of_order_timestamps: set[pd.Timestamp],
    run_id: str,
    warmup_start: pd.Timestamp,
    replay_start: pd.Timestamp,
    replay_end: pd.Timestamp,
    expected_timeframe_minutes: int,
) -> DryRunResult:
    warmup_df, replay_df = split_warmup_replay(df, warmup_start, replay_start, replay_end)
    expected_delta = pd.Timedelta(minutes=expected_timeframe_minutes)
    warmup_ready_flag = len(warmup_df) > 0

    decision_logs: list[dict[str, Any]] = []
    event_logs: list[dict[str, Any]] = []
    state_logs: list[dict[str, Any]] = []
    warning_logs: list[dict[str, Any]] = []

    duplicate_count = 0
    data_gap_count = 0
    out_of_order_count = 0
    expected_weekend_gap_count = 0
    ordinary_missing_bar_gap_count = 0
    unknown_gap_count = 0
    last_processed_timestamp: pd.Timestamp | None = None

    for _, row in replay_df.iterrows():
        ts: pd.Timestamp = row["timestamp"]
        warning_flags: list[str] = []
        data_gap_flag = False
        duplicate_bar_flag = ts in duplicate_timestamps
        out_of_order_flag = ts in out_of_order_timestamps

        if duplicate_bar_flag:
            duplicate_count += 1
            warning_flags.append("duplicate_timestamp")
            msg = "duplicate timestamp detected"
            warning_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "warning_type": "duplicate_timestamp",
                    "severity": "warning",
                    "message": msg,
                    "gap_class": "",
                    "expected_gap_flag": "",
                    "gap_duration": "",
                    "previous_timestamp": "",
                    "current_timestamp": ts.isoformat(),
                    "gap_reason": "",
                    "gap_action": "",
                    "gap_requires_investigation": "",
                }
            )
            event_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "event_type": "data_quality",
                    "severity": "warning",
                    "message": msg,
                    "source": "csv_replay",
                    "recovery_action": "inspect_input_csv",
                    "resolved_flag": False,
                    "gap_class": "",
                    "expected_gap_flag": "",
                    "gap_duration": "",
                    "previous_timestamp": "",
                    "current_timestamp": ts.isoformat(),
                    "gap_reason": "",
                    "gap_action": "",
                    "gap_requires_investigation": "",
                }
            )

        if out_of_order_flag:
            out_of_order_count += 1
            warning_flags.append("out_of_order_timestamp")
            msg = "out-of-order timestamp detected in original CSV order"
            warning_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "warning_type": "out_of_order_timestamp",
                    "severity": "warning",
                    "message": msg,
                    "gap_class": "",
                    "expected_gap_flag": "",
                    "gap_duration": "",
                    "previous_timestamp": "",
                    "current_timestamp": ts.isoformat(),
                    "gap_reason": "",
                    "gap_action": "",
                    "gap_requires_investigation": "",
                }
            )
            event_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "event_type": "data_quality",
                    "severity": "warning",
                    "message": msg,
                    "source": "csv_replay",
                    "recovery_action": "inspect_input_csv_order",
                    "resolved_flag": False,
                    "gap_class": "",
                    "expected_gap_flag": "",
                    "gap_duration": "",
                    "previous_timestamp": "",
                    "current_timestamp": ts.isoformat(),
                    "gap_reason": "",
                    "gap_action": "",
                    "gap_requires_investigation": "",
                }
            )

        if last_processed_timestamp is not None and (ts - last_processed_timestamp) > expected_delta:
            data_gap_flag = True
            data_gap_count += 1
            warning_flags.append("data_gap")
            msg = f"data gap detected: expected {expected_delta}, got {ts - last_processed_timestamp}"
            gap_info = _classify_gap(last_processed_timestamp, ts)
            if gap_info["gap_class"] == "expected_weekend_gap":
                expected_weekend_gap_count += 1
            elif gap_info["gap_class"] == "ordinary_missing_bar_gap":
                ordinary_missing_bar_gap_count += 1
            else:
                unknown_gap_count += 1
            warning_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "warning_type": "data_gap",
                    "severity": "warning",
                    "message": msg,
                    **gap_info,
                }
            )
            event_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "event_type": "data_quality",
                    "severity": "warning",
                    "message": msg,
                    "source": "csv_replay",
                    "recovery_action": "check_missing_bars",
                    "resolved_flag": False,
                    **gap_info,
                }
            )

        data_valid = row["data_valid_flag"] if "data_valid_flag" in row.index and pd.notna(row["data_valid_flag"]) else True
        decision_reason = "csv_replay_skeleton:no_signal_no_trade"
        decision_logs.append(
            {
                "timestamp": ts.isoformat(),
                "mode": "csv_replay",
                "input_bar_status": "replay",
                "data_valid_flag": bool(data_valid),
                "warmup_ready_flag": warmup_ready_flag,
                "entry_signal": False,
                "exit_signal": False,
                "signal_type": "none",
                "trade_ok": False,
                "decision_reason": decision_reason,
                "paper_order_action": "none",
                "paper_position_state": "flat",
                "warning_flags": "|".join(warning_flags),
            }
        )
        state_logs.append(
            {
                "timestamp": ts.isoformat(),
                "current_timestamp": ts.isoformat(),
                "last_processed_timestamp": last_processed_timestamp.isoformat() if last_processed_timestamp is not None else "",
                "warmup_ready_flag": warmup_ready_flag,
                "data_gap_flag": data_gap_flag,
                "duplicate_bar_flag": duplicate_bar_flag,
                "out_of_order_flag": out_of_order_flag,
                "paper_position_state": "flat",
            }
        )
        last_processed_timestamp = ts

    summary = {
        "run_id": run_id,
        "mode": "csv_replay",
        "warmup_bar_count": len(warmup_df),
        "replay_bar_count": len(replay_df),
        "warning_count": len(warning_logs),
        "duplicate_bar_count": duplicate_count,
        "data_gap_count": data_gap_count,
        "out_of_order_count": out_of_order_count,
        "decision_log_count": len(decision_logs),
        "expected_weekend_gap_count": expected_weekend_gap_count,
        "ordinary_missing_bar_gap_count": ordinary_missing_bar_gap_count,
        "unknown_gap_count": unknown_gap_count,
    }
    return DryRunResult(
        decision_logs=decision_logs,
        event_logs=event_logs,
        state_logs=state_logs,
        warning_logs=warning_logs,
        summary=summary,
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(output_dir: Path, result: DryRunResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_dir / "near_live_decision_logs.csv",
        result.decision_logs,
        [
            "timestamp",
            "mode",
            "input_bar_status",
            "data_valid_flag",
            "warmup_ready_flag",
            "entry_signal",
            "exit_signal",
            "signal_type",
            "trade_ok",
            "decision_reason",
            "paper_order_action",
            "paper_position_state",
            "warning_flags",
        ],
    )
    _write_csv(
        output_dir / "near_live_event_logs.csv",
        result.event_logs,
        [
            "timestamp",
            "event_type",
            "severity",
            "message",
            "source",
            "recovery_action",
            "resolved_flag",
            "gap_class",
            "expected_gap_flag",
            "gap_duration",
            "previous_timestamp",
            "current_timestamp",
            "gap_reason",
            "gap_action",
            "gap_requires_investigation",
        ],
    )
    _write_csv(
        output_dir / "near_live_state_logs.csv",
        result.state_logs,
        [
            "timestamp",
            "current_timestamp",
            "last_processed_timestamp",
            "warmup_ready_flag",
            "data_gap_flag",
            "duplicate_bar_flag",
            "out_of_order_flag",
            "paper_position_state",
        ],
    )
    _write_csv(
        output_dir / "near_live_validation_warnings.csv",
        result.warning_logs,
        [
            "timestamp",
            "warning_type",
            "severity",
            "message",
            "gap_class",
            "expected_gap_flag",
            "gap_duration",
            "previous_timestamp",
            "current_timestamp",
            "gap_reason",
            "gap_action",
            "gap_requires_investigation",
        ],
    )
    _write_csv(output_dir / "near_live_summary.csv", [result.summary], list(result.summary.keys()))

    md = [
        "# near-live CSV replay dry-run summary",
        "",
        "- 実注文なし",
        "- 収益性確認ではない",
        "- CSV replay dry-run skeleton",
        f"- warnings: {result.summary['warning_count']}",
        f"- duplicate_bar_count: {result.summary['duplicate_bar_count']}",
        f"- data_gap_count: {result.summary['data_gap_count']}",
        f"- out_of_order_count: {result.summary['out_of_order_count']}",
    ]
    (output_dir / "near_live_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    warmup_start = _parse_utc_timestamp(args.warmup_start)
    replay_start = _parse_utc_timestamp(args.replay_start)
    replay_end = _parse_utc_timestamp(args.replay_end)
    if not (warmup_start <= replay_start < replay_end):
        raise ValueError("Invalid period bounds: must satisfy warmup_start <= replay_start < replay_end")

    df, duplicate_timestamps, out_of_order_timestamps = load_and_prepare_input(input_csv)
    result = run_csv_replay_dry_run(
        df=df,
        duplicate_timestamps=duplicate_timestamps,
        out_of_order_timestamps=out_of_order_timestamps,
        run_id=args.run_id,
        warmup_start=warmup_start,
        replay_start=replay_start,
        replay_end=replay_end,
        expected_timeframe_minutes=args.expected_timeframe_minutes,
    )
    write_outputs(output_dir, result)
    print(f"[summary] run_id={args.run_id}")
    print(f"[summary] replay_bar_count={result.summary['replay_bar_count']}")
    print(f"[summary] warning_count={result.summary['warning_count']}")
    print(f"[summary] output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
