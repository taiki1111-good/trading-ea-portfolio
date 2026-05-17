#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.pipeline_adapter import PipelineAdapter
from src.backtest.pipeline_adapter import PipelineAdapterConfig
from src.data.types import PriceBar


REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close"]


@dataclass
class PipelineDryRunResult:
    decision_logs: list[dict[str, Any]]
    event_logs: list[dict[str, Any]]
    state_logs: list[dict[str, Any]]
    warning_logs: list[dict[str, Any]]
    summary: dict[str, Any]


HTF_DECISION_LOG_FIELDS = [
    "htf_filter_enabled",
    "htf_timeframe_policy",
    "htf_neutral_policy",
    "htf_trend_dir",
    "htf_bias",
    "htf_direction_aligned",
    "htf_filter_reason",
    "htf_context_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CSV replay pipeline dry-run skeleton.")
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


def _is_true(v: str) -> bool:
    return (v or "").strip().lower() in {"true", "1", "yes"}


def _validate_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


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


def row_to_price_bar(row: dict[str, Any]) -> PriceBar:
    spread_raw = row.get("spread_pips", None)
    if spread_raw is None or (isinstance(spread_raw, float) and pd.isna(spread_raw)):
        spread_raw = row.get("spread", None)
    if spread_raw is None or (isinstance(spread_raw, float) and pd.isna(spread_raw)):
        spread = 0.0
    else:
        spread = float(spread_raw)

    volume_raw = row.get("volume", None)
    if volume_raw is None or (isinstance(volume_raw, float) and pd.isna(volume_raw)):
        volume = 0.0
    else:
        volume = float(volume_raw)

    ts = pd.to_datetime(row["timestamp"], utc=True).to_pydatetime()
    return PriceBar(
        timestamp=ts,
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        spread=spread,
        volume=volume,
    )


def run_csv_replay_pipeline_dry_run(
    df: pd.DataFrame,
    duplicate_timestamps: set[pd.Timestamp],
    out_of_order_timestamps: set[pd.Timestamp],
    run_id: str,
    warmup_start: pd.Timestamp,
    replay_start: pd.Timestamp,
    replay_end: pd.Timestamp,
    expected_timeframe_minutes: int,
    adapter: Any | None = None,
) -> PipelineDryRunResult:
    warmup_df, replay_df = split_warmup_replay(df, warmup_start, replay_start, replay_end)
    warmup_ready_flag = len(warmup_df) > 0
    expected_delta = pd.Timedelta(minutes=expected_timeframe_minutes)
    bars = [row_to_price_bar(r) for r in replay_df.to_dict(orient="records")]
    pipeline_adapter = adapter or PipelineAdapter(PipelineAdapterConfig())

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

    pipeline_adapter_called_count = 0
    pipeline_adapter_error_count = 0
    pipeline_adapter_skipped_count = 0
    entry_signal_true_count = 0
    exit_signal_true_count = 0
    trade_ok_true_count = 0
    paper_order_candidate_count = 0
    real_order_sent_count = 0
    no_real_order_integrity_violation_count = 0

    last_processed_timestamp: pd.Timestamp | None = None
    last_pipeline_status = "init"
    last_pipeline_error_type = ""
    last_pipeline_error_message = ""

    for i, bar in enumerate(bars):
        ts = pd.Timestamp(bar.timestamp)
        warning_flags: list[str] = []
        data_gap_flag = False
        duplicate_bar_flag = ts in duplicate_timestamps
        out_of_order_flag = ts in out_of_order_timestamps

        if duplicate_bar_flag:
            duplicate_count += 1
            warning_flags.append("duplicate_timestamp")
            warning_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "warning_type": "duplicate_timestamp",
                    "severity": "warning",
                    "message": "duplicate timestamp detected",
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
            warning_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "warning_type": "out_of_order_timestamp",
                    "severity": "warning",
                    "message": "out-of-order timestamp detected in original CSV order",
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
                    "message": f"data gap detected: expected {expected_delta}, got {ts - last_processed_timestamp}",
                    **gap_info,
                }
            )

        trace: dict[str, Any] = {}
        entry_event = None
        pipeline_adapter_called = False
        pipeline_adapter_status = "skipped"
        pipeline_error_type = ""
        pipeline_error_message = ""

        if not warmup_ready_flag:
            pipeline_adapter_skipped_count += 1
            pipeline_error_message = "warmup_not_ready"
        else:
            pipeline_adapter_called = True
            pipeline_adapter_called_count += 1
            window = bars[: i + 1]
            current_index = len(window) - 1
            try:
                entry_event = pipeline_adapter(current_index=current_index, window=window)
                trace_hook = getattr(pipeline_adapter, "get_last_decision_trace", None)
                if callable(trace_hook):
                    trace = trace_hook() or {}
                pipeline_adapter_status = "ok"
            except Exception as exc:  # noqa: BLE001
                pipeline_adapter_status = "error"
                pipeline_adapter_error_count += 1
                pipeline_error_type = type(exc).__name__
                pipeline_error_message = str(exc)
                event_logs.append(
                    {
                        "timestamp": ts.isoformat(),
                        "event_type": "pipeline_adapter_error",
                        "severity": "error",
                        "message": pipeline_error_message or "pipeline adapter error",
                        "source": "csv_replay_pipeline",
                        "recovery_action": "record_and_continue",
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

        entry_signal = bool(trace.get("entry_signal", entry_event is not None))
        exit_signal = bool(trace.get("exit_signal", False))
        signal_type = str(trace.get("signal_type", "none"))
        signal_reason = str(trace.get("decision_reason", ""))
        trade_ok = bool(trace.get("trade_ok", entry_event is not None and pipeline_adapter_status == "ok"))
        filter_reason = str(trace.get("htf_filter_reason", ""))
        htf_filter_enabled = _is_true(str(trace.get("htf_filter_enabled", "")))
        htf_timeframe_policy = str(trace.get("htf_timeframe_policy", ""))
        htf_neutral_policy = str(trace.get("htf_neutral_policy", ""))
        htf_trend_dir = str(trace.get("htf_trend_dir", ""))
        htf_bias = str(trace.get("htf_bias", ""))
        htf_direction_aligned = _is_true(str(trace.get("htf_direction_aligned", "")))
        htf_filter_reason = str(trace.get("htf_filter_reason", ""))
        htf_context_reason = str(trace.get("htf_context_reason", ""))
        decision_reason = str(trace.get("decision_reason", "")) or (
            "pipeline_adapter_error" if pipeline_adapter_status == "error" else pipeline_error_message or "no_entry"
        )

        lot = ""
        stop_loss = ""
        take_profit = ""
        paper_order_action = "none"
        if entry_event is not None and pipeline_adapter_status == "ok":
            lot = str(entry_event.lot)
            stop_loss = str(entry_event.stop_loss)
            take_profit = str(entry_event.take_profit)
            signal_reason = entry_event.signal_reason or signal_reason
            filter_reason = entry_event.filter_reason or filter_reason
            paper_order_action = "paper_candidate"
            paper_order_candidate_count += 1

        real_order_sent = False
        broker_order_id = ""
        no_real_order_integrity_ok = (not real_order_sent) and (broker_order_id == "") and (
            paper_order_action in {"none", "paper_candidate"}
        )
        if not no_real_order_integrity_ok:
            no_real_order_integrity_violation_count += 1
            event_logs.append(
                {
                    "timestamp": ts.isoformat(),
                    "event_type": "no_real_order_integrity_violation",
                    "severity": "error",
                    "message": "no_real_order_integrity violated",
                    "source": "csv_replay_pipeline",
                    "recovery_action": "record_and_continue",
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

        if entry_signal:
            entry_signal_true_count += 1
        if exit_signal:
            exit_signal_true_count += 1
        if trade_ok:
            trade_ok_true_count += 1
        if real_order_sent:
            real_order_sent_count += 1

        decision_logs.append(
            {
                "timestamp": ts.isoformat(),
                "mode": "csv_replay_pipeline",
                "input_bar_status": "replay",
                "data_valid_flag": True,
                "warmup_ready_flag": warmup_ready_flag,
                "pipeline_mode": "pipeline",
                "pipeline_adapter_called": pipeline_adapter_called,
                "pipeline_adapter_status": pipeline_adapter_status,
                "pipeline_error_type": pipeline_error_type,
                "pipeline_error_message": pipeline_error_message,
                "entry_signal": entry_signal,
                "exit_signal": exit_signal,
                "signal_type": signal_type,
                "signal_reason": signal_reason,
                "trade_ok": trade_ok,
                "htf_filter_enabled": htf_filter_enabled,
                "htf_timeframe_policy": htf_timeframe_policy,
                "htf_neutral_policy": htf_neutral_policy,
                "htf_trend_dir": htf_trend_dir,
                "htf_bias": htf_bias,
                "htf_direction_aligned": htf_direction_aligned,
                "htf_filter_reason": htf_filter_reason,
                "htf_context_reason": htf_context_reason,
                "filter_reason": filter_reason,
                "lot": lot,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "paper_order_action": paper_order_action,
                "real_order_sent": real_order_sent,
                "broker_order_id": broker_order_id,
                "no_real_order_integrity_ok": no_real_order_integrity_ok,
                "decision_reason": decision_reason,
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
                "pipeline_mode": "pipeline",
                "pipeline_adapter_last_status": pipeline_adapter_status,
                "last_pipeline_error_type": pipeline_error_type,
                "last_pipeline_error_message": pipeline_error_message,
                "paper_position_state": "flat",
                "real_order_sent": real_order_sent,
                "no_real_order_integrity_ok": no_real_order_integrity_ok,
            }
        )

        if pipeline_adapter_status == "error":
            last_pipeline_status = "error"
            last_pipeline_error_type = pipeline_error_type
            last_pipeline_error_message = pipeline_error_message
        else:
            last_pipeline_status = pipeline_adapter_status
            last_pipeline_error_type = ""
            last_pipeline_error_message = ""

        last_processed_timestamp = ts

    summary = {
        "run_id": run_id,
        "mode": "csv_replay_pipeline",
        "warmup_bar_count": len(warmup_df),
        "replay_bar_count": len(replay_df),
        "decision_log_count": len(decision_logs),
        "warning_count": len(warning_logs),
        "duplicate_bar_count": duplicate_count,
        "data_gap_count": data_gap_count,
        "out_of_order_count": out_of_order_count,
        "expected_weekend_gap_count": expected_weekend_gap_count,
        "ordinary_missing_bar_gap_count": ordinary_missing_bar_gap_count,
        "unknown_gap_count": unknown_gap_count,
        "pipeline_adapter_called_count": pipeline_adapter_called_count,
        "pipeline_adapter_error_count": pipeline_adapter_error_count,
        "pipeline_adapter_skipped_count": pipeline_adapter_skipped_count,
        "entry_signal_true_count": entry_signal_true_count,
        "exit_signal_true_count": exit_signal_true_count,
        "trade_ok_true_count": trade_ok_true_count,
        "paper_order_candidate_count": paper_order_candidate_count,
        "real_order_sent_count": real_order_sent_count,
        "no_real_order_integrity_violation_count": no_real_order_integrity_violation_count,
    }
    return PipelineDryRunResult(
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


def write_outputs(output_dir: Path, result: PipelineDryRunResult) -> None:
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
            "pipeline_mode",
            "pipeline_adapter_called",
            "pipeline_adapter_status",
            "pipeline_error_type",
            "pipeline_error_message",
            "entry_signal",
            "exit_signal",
            "signal_type",
            "signal_reason",
            "trade_ok",
            "htf_filter_enabled",
            "htf_timeframe_policy",
            "htf_neutral_policy",
            "htf_trend_dir",
            "htf_bias",
            "htf_direction_aligned",
            "htf_filter_reason",
            "htf_context_reason",
            "filter_reason",
            "lot",
            "stop_loss",
            "take_profit",
            "paper_order_action",
            "real_order_sent",
            "broker_order_id",
            "no_real_order_integrity_ok",
            "decision_reason",
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
            "pipeline_mode",
            "pipeline_adapter_last_status",
            "last_pipeline_error_type",
            "last_pipeline_error_message",
            "paper_position_state",
            "real_order_sent",
            "no_real_order_integrity_ok",
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
        "# near-live CSV replay pipeline dry-run summary",
        "",
        "- 実注文なし",
        "- 収益性確認ではない",
        "- 実 broker / OANDA API / 実注文送信なし",
        "- 一次summary（pipeline dry-run 実行結果の記録）",
        "- dry-run安全性とログ整合性の確認であり、passは収益性や実運用品質を意味しない",
        "- CSV replay pipeline dry-run skeleton",
        f"- replay_bar_count: {result.summary['replay_bar_count']}",
        f"- pipeline_adapter_called_count: {result.summary['pipeline_adapter_called_count']}",
        f"- pipeline_adapter_error_count: {result.summary['pipeline_adapter_error_count']}",
        f"- real_order_sent_count: {result.summary['real_order_sent_count']}",
        f"- no_real_order_integrity_violation_count: {result.summary['no_real_order_integrity_violation_count']}",
        f"- warning_count: {result.summary['warning_count']}",
        f"- expected_weekend_gap_count: {result.summary['expected_weekend_gap_count']}",
        f"- ordinary_missing_bar_gap_count: {result.summary['ordinary_missing_bar_gap_count']}",
        f"- unknown_gap_count: {result.summary['unknown_gap_count']}",
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
    result = run_csv_replay_pipeline_dry_run(
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
    print(f"[summary] pipeline_adapter_error_count={result.summary['pipeline_adapter_error_count']}")
    print(f"[summary] output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
