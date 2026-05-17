#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.backtest.backtest_logger_adapter import BacktestLoggerAdapter
from src.backtest.backtest_runner import EntryEvent
from src.backtest.backtest_runner import EntryEventProvider
from src.backtest.exit_rule_engine import ExitRuleEngine
from src.backtest.pipeline_adapter import PipelineAdapter
from src.backtest.pipeline_adapter import PipelineAdapterConfig
from src.backtest.pnl_calculator import PnLCalculator
from src.backtest.position_tracker import PositionTracker
from src.backtest.types import BacktestConfig
from src.backtest.types import BacktestPosition
from src.backtest.types import BacktestResult
from src.backtest.types import BacktestSummary
from src.backtest.types import BacktestTrade
from src.data.price_loader import PriceDataLoader
from src.data.types import PriceBar
from src.data.types import PriceFrame


@dataclass
class TrailingState:
    active: bool = False
    best_favorable: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run experimental exit policy backtest on M5 slice.')
    parser.add_argument('--input-csv', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-holding-bars', type=int, required=True)
    parser.add_argument('--exit-policy', choices=['fixed_sl_tp', 'simple_trailing_after_1R'], default='fixed_sl_tp')
    parser.add_argument('--trailing-activation-r', type=float, default=1.0)
    parser.add_argument('--entry-time-mode', default='bar_timestamp')
    parser.add_argument('--third-candidate-lookback-bars', type=int, default=5)
    parser.add_argument('--disable-heuristic-fallback', action='store_true')
    parser.add_argument('--disable-temporal-third-break', action='store_true')
    parser.add_argument('--max-entries-per-recent-third-candidate', type=int, default=None)
    parser.add_argument('--htf-filter-enabled', action='store_true')
    parser.add_argument('--htf-timeframe-policy', default='H1_only', choices=['H1_only'])
    parser.add_argument('--htf-neutral-policy', default='permissive', choices=['permissive', 'strict'])
    parser.add_argument('--htf-v2-enabled', action='store_true')
    parser.add_argument('--htf-v2-policy', default='diagnostic_only', choices=['diagnostic_only'])
    parser.add_argument('--htf-v2-h4-ma-fast', type=int, default=20)
    parser.add_argument('--htf-v2-h4-ma-slow', type=int, default=50)
    parser.add_argument('--htf-v2-h1-ma-fast', type=int, default=20)
    parser.add_argument('--htf-v2-slope-window', type=int, default=3)
    parser.add_argument('--sr-v2-enabled', action='store_true')
    parser.add_argument('--sr-v2-policy', default='diagnostic_only', choices=['diagnostic_only'])
    parser.add_argument('--sr-v2-window-bars', type=int, default=48)
    parser.add_argument('--sr-v2-near-threshold-pips', type=float, default=10.0)
    parser.add_argument('--sr-v2-pip-size', type=float, default=0.01)
    parser.add_argument('--sr-v2-use-atr-normalized', action='store_true')
    parser.add_argument('--session-v2-enabled', action='store_true')
    parser.add_argument('--session-v2-policy', default='diagnostic_only', choices=['diagnostic_only'])
    parser.add_argument('--session-v2-timezone', default='UTC')
    parser.add_argument('--session-v2-use-day-of-week', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--session-v2-use-hour-bucket', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--session-v2-use-dst-adjustment', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--start', default='', help='Optional UTC inclusive start bound.')
    parser.add_argument('--end', default='', help='Optional UTC exclusive end bound.')
    parser.add_argument('--warmup-start', default='', help='Optional UTC inclusive warmup start bound for indicator history.')
    parser.add_argument('--progress-every-bars', type=int, default=1000)
    parser.add_argument('--partial-save-every-bars', type=int, default=0)
    return parser.parse_args()


def _parse_utc_bound(raw: str) -> datetime | None:
    text = str(raw or '').strip()
    if not text:
        return None
    if 'T' not in text:
        text = text + 'T00:00:00+00:00'
    elif text.endswith('Z'):
        text = text[:-1] + '+00:00'
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _slice_price_frame(price_frame: PriceFrame, start: datetime | None, end: datetime | None) -> list[PriceBar]:
    bars = list(price_frame)
    if start is None and end is None:
        return bars
    out: list[PriceBar] = []
    for b in bars:
        if start is not None and b.timestamp < start:
            continue
        if end is not None and b.timestamp >= end:
            continue
        out.append(b)
    return out


def _evaluate_trailing_exit(
    position: BacktestPosition,
    current_bar: PriceBar,
    current_index: int,
    config: BacktestConfig,
    trailing_state: TrailingState,
    trailing_activation_r: float,
) -> tuple[bool, float | None, str, TrailingState]:
    if current_index <= position.entry_index:
        return False, None, 'no_exit_on_entry_bar', trailing_state

    holding_bars = current_index - position.entry_index
    if holding_bars >= config.max_holding_bars:
        return True, current_bar.close, 'close', trailing_state

    r = abs(position.entry_price - position.stop_loss) * trailing_activation_r
    if r <= 0:
        return False, None, 'no_exit', trailing_state

    if trailing_state.best_favorable == 0.0:
        trailing_state.best_favorable = position.entry_price

    stop = position.stop_loss

    if position.direction == 'long':
        trailing_state.best_favorable = max(trailing_state.best_favorable, current_bar.high)
        if (not trailing_state.active) and trailing_state.best_favorable >= position.entry_price + r:
            trailing_state.active = True
        if trailing_state.active:
            stop = max(stop, trailing_state.best_favorable - r)
        if current_bar.low <= stop:
            return True, stop, 'trailing_stop' if trailing_state.active else 'stop_loss', trailing_state
        if current_bar.high >= position.take_profit:
            return True, position.take_profit, 'take_profit', trailing_state
        return False, None, 'no_exit', trailing_state

    trailing_state.best_favorable = min(trailing_state.best_favorable, current_bar.low)
    if (not trailing_state.active) and trailing_state.best_favorable <= position.entry_price - r:
        trailing_state.active = True
    if trailing_state.active:
        stop = min(stop, trailing_state.best_favorable + r)
    if current_bar.high >= stop:
        return True, stop, 'trailing_stop' if trailing_state.active else 'stop_loss', trailing_state
    if current_bar.low <= position.take_profit:
        return True, position.take_profit, 'take_profit', trailing_state
    return False, None, 'no_exit', trailing_state


def run_backtest_exit_experiment(
    price_frame: PriceFrame,
    config: BacktestConfig,
    entry_event_provider: EntryEventProvider,
    exit_policy: str,
    evaluation_start: datetime | None = None,
    evaluation_end: datetime | None = None,
    trailing_activation_r: float = 1.0,
    entry_time_mode: str = 'bar_timestamp',
    progress_every_bars: int = 1000,
    partial_save_every_bars: int = 0,
    partial_trade_logs_path: Path | None = None,
) -> BacktestResult:
    bars = list(price_frame)
    tracker = PositionTracker()
    trades: list[BacktestTrade] = []
    trade_logs: list[dict[str, Any]] = []
    decision_logs: list[dict[str, Any]] = []
    evaluation_bars = [
        b for b in bars
        if (evaluation_start is None or b.timestamp >= evaluation_start)
        and (evaluation_end is None or b.timestamp < evaluation_end)
    ]
    start_time = evaluation_bars[0].timestamp if evaluation_bars else None
    end_time = evaluation_bars[-1].timestamp if evaluation_bars else None

    provider = entry_event_provider
    reset_hook = getattr(provider, 'reset_run_state', None)
    if callable(reset_hook):
        reset_hook()

    trailing_state = TrailingState()
    t0 = time.time()

    for i, bar in enumerate(bars):
        try:
            window = bars[: i + 1]
            is_evaluation_bar = (
                (evaluation_start is None or bar.timestamp >= evaluation_start)
                and (evaluation_end is None or bar.timestamp < evaluation_end)
            )
            if not is_evaluation_bar:
                continue

            if not tracker.has_open_position():
                ev = provider(i, window)
                trace_hook = getattr(provider, 'get_last_decision_trace', None)
                if callable(trace_hook):
                    trace = trace_hook()
                    if trace:
                        decision_logs.append({'log_time': datetime.now(timezone.utc).isoformat(), 'bar_index': i, 'timestamp': bar.timestamp.isoformat(), **trace})
                if ev is not None:
                    opened = tracker.open_position(
                        BacktestPosition(
                            direction=ev.direction,
                            entry_price=bar.close,
                            entry_time=bar.timestamp,
                            lot=ev.lot,
                            stop_loss=ev.stop_loss,
                            take_profit=ev.take_profit,
                            entry_index=i,
                            entry_reason=ev.entry_reason,
                            signal_reason=ev.signal_reason,
                            risk_reason=ev.risk_reason,
                            filter_reason=ev.filter_reason,
                            fallback_used=ev.fallback_used,
                            structure_source=ev.structure_source,
                            recent_third_timestamp=ev.recent_third_timestamp,
                            recent_third_direction=ev.recent_third_direction,
                            temporal_lag_bars=ev.temporal_lag_bars,
                            temporal_lookback_bars=ev.temporal_lookback_bars,
                            breakout_direction=ev.breakout_direction,
                        )
                    )
                    if opened:
                        trailing_state = TrailingState(active=False, best_favorable=bar.close)

            pos = tracker.get_position()
            if pos is None:
                continue

            if exit_policy == 'fixed_sl_tp':
                decision = ExitRuleEngine.evaluate(pos, bar, i, config)
                should_exit = decision.should_exit
                exit_price = decision.exit_price
                exit_reason = decision.exit_reason
            elif exit_policy == 'simple_trailing_after_1R':
                should_exit, exit_price, exit_reason, trailing_state = _evaluate_trailing_exit(
                    pos,
                    bar,
                    i,
                    config,
                    trailing_state,
                    trailing_activation_r,
                )
            else:
                raise ValueError(f'unsupported exit_policy: {exit_policy}')

            if not should_exit:
                continue
            if exit_price is None:
                raise ValueError('exit_price is required when should_exit is true')

            pnl = PnLCalculator.calculate(pos.direction, pos.entry_price, exit_price, pos.lot)
            trade = BacktestTrade(
                direction=pos.direction,
                entry_price=pos.entry_price,
                exit_price=exit_price,
                entry_time=pos.entry_time,
                exit_time=bar.timestamp,
                lot=pos.lot,
                pnl=pnl,
                realized_pnl=pnl,
                exit_reason=exit_reason,
                entry_reason=pos.entry_reason,
                signal_reason=pos.signal_reason,
                risk_reason=pos.risk_reason,
                filter_reason=pos.filter_reason,
                fallback_used=pos.fallback_used,
                structure_source=pos.structure_source,
                recent_third_timestamp=pos.recent_third_timestamp,
                recent_third_direction=pos.recent_third_direction,
                temporal_lag_bars=pos.temporal_lag_bars,
                temporal_lookback_bars=pos.temporal_lookback_bars,
                breakout_direction=pos.breakout_direction,
            )
            trades.append(trade)
            holding_bars = i - pos.entry_index
            row = BacktestLoggerAdapter.to_trade_log(trade, pos.stop_loss, pos.take_profit)
            row['exit_policy'] = exit_policy
            row['trailing_activation_R'] = trailing_activation_r
            row['entry_time_mode'] = entry_time_mode
            row['holding_bars'] = holding_bars
            row['pnl'] = pnl
            trade_logs.append(row)
            tracker.close_position()
        finally:
            if partial_save_every_bars > 0 and partial_trade_logs_path is not None and (i + 1) % partial_save_every_bars == 0:
                _write_csv(partial_trade_logs_path, trade_logs)
            if progress_every_bars > 0 and ((i + 1) % progress_every_bars == 0 or (i + 1) == len(bars)):
                elapsed = time.time() - t0
                print(
                    f"[progress] total_bars={len(bars)} processed_bars={i+1} "
                    f"current_timestamp={bar.timestamp.isoformat()} trade_count={len(trades)} elapsed_seconds={elapsed:.2f}"
                )

    total_pnl = sum(t.realized_pnl for t in trades)
    avg = (total_pnl / len(trades)) if trades else None
    summary = BacktestSummary(
        run_id=config.run_id,
        start_time=start_time,
        end_time=end_time,
        bar_count=len(evaluation_bars),
        trade_count=len(trades),
        total_pnl=total_pnl,
        average_pnl=avg,
        summary_reason=f'experimental exit policy run: {exit_policy}',
    )
    return BacktestResult(config=config, trades=trades, trade_logs=trade_logs, decision_logs=decision_logs, state_logs=[], event_logs=[], summary=summary, evaluator_result=None)


def _to_iso(value: Any) -> str:
    if value is None:
        return ''
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not input_csv.exists():
        raise FileNotFoundError(f'input CSV not found: {input_csv}')

    price_frame = PriceDataLoader.load_from_csv(str(input_csv), timeframe='M5')
    start = _parse_utc_bound(args.start)
    end = _parse_utc_bound(args.end)
    warmup_start = _parse_utc_bound(args.warmup_start)
    if warmup_start is not None and start is not None and warmup_start > start:
        raise ValueError('warmup-start must be earlier than or equal to start')

    evaluation_bars = _slice_price_frame(price_frame, start, end)
    if not evaluation_bars:
        raise ValueError('No bars in selected [start, end) period')
    if warmup_start is None:
        indicator_bars = evaluation_bars
    else:
        indicator_bars = _slice_price_frame(price_frame, warmup_start, end)
        if not indicator_bars:
            raise ValueError('No bars in selected [warmup_start, end) period')
    warmup_bar_count = len([b for b in indicator_bars if start is not None and b.timestamp < start])
    print(
        f"[info] selected_bars={len(evaluation_bars)} "
        f"range=[{evaluation_bars[0].timestamp.isoformat()}, {evaluation_bars[-1].timestamp.isoformat()}]"
    )
    print(
        f"[info] indicator_input_bars={len(indicator_bars)} "
        f"indicator_range=[{indicator_bars[0].timestamp.isoformat()}, {indicator_bars[-1].timestamp.isoformat()}] "
        f"warmup_bar_count={warmup_bar_count}"
    )
    config = BacktestConfig(run_id=args.run_id, max_holding_bars=args.max_holding_bars)
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=not args.disable_heuristic_fallback,
            third_candidate_lookback_bars=args.third_candidate_lookback_bars,
            allow_temporal_third_break=not args.disable_temporal_third_break,
            max_entries_per_recent_third_candidate=args.max_entries_per_recent_third_candidate,
            htf_filter_enabled=args.htf_filter_enabled,
            htf_timeframe_policy=args.htf_timeframe_policy,
            htf_neutral_policy=args.htf_neutral_policy,
            htf_v2_enabled=args.htf_v2_enabled,
            htf_v2_policy=args.htf_v2_policy,
            htf_v2_h4_ma_fast=args.htf_v2_h4_ma_fast,
            htf_v2_h4_ma_slow=args.htf_v2_h4_ma_slow,
            htf_v2_h1_ma_fast=args.htf_v2_h1_ma_fast,
            htf_v2_slope_window=args.htf_v2_slope_window,
            sr_v2_enabled=args.sr_v2_enabled,
            sr_v2_policy=args.sr_v2_policy,
            sr_v2_window_bars=args.sr_v2_window_bars,
            sr_v2_near_threshold_pips=args.sr_v2_near_threshold_pips,
            sr_v2_pip_size=args.sr_v2_pip_size,
            sr_v2_use_atr_normalized=args.sr_v2_use_atr_normalized,
            session_v2_enabled=args.session_v2_enabled,
            session_v2_policy=args.session_v2_policy,
            session_v2_timezone=args.session_v2_timezone,
            session_v2_use_day_of_week=args.session_v2_use_day_of_week,
            session_v2_use_hour_bucket=args.session_v2_use_hour_bucket,
            session_v2_use_dst_adjustment=args.session_v2_use_dst_adjustment,
        )
    )

    result = run_backtest_exit_experiment(
        indicator_bars,
        config,
        adapter,
        exit_policy=args.exit_policy,
        evaluation_start=start,
        evaluation_end=end,
        trailing_activation_r=args.trailing_activation_r,
        entry_time_mode=args.entry_time_mode,
        progress_every_bars=args.progress_every_bars,
        partial_save_every_bars=args.partial_save_every_bars,
        partial_trade_logs_path=(output_dir / 'partial_trade_logs.csv') if args.partial_save_every_bars > 0 else None,
    )

    _write_csv(output_dir / 'trade_logs.csv', result.trade_logs)
    _write_csv(output_dir / 'decision_logs.csv', result.decision_logs)

    summary = {
        'run_id': args.run_id,
        'input_csv': str(input_csv),
        'exit_policy': args.exit_policy,
        'trailing_activation_R': args.trailing_activation_r,
        'entry_time_mode': args.entry_time_mode,
        'bar_count': result.summary.bar_count if result.summary else 0,
        'trade_count': result.summary.trade_count if result.summary else 0,
        'total_pnl': result.summary.total_pnl if result.summary else 0.0,
        'average_pnl': result.summary.average_pnl if result.summary else '',
        'start_time': _to_iso(result.summary.start_time if result.summary else None),
        'end_time': _to_iso(result.summary.end_time if result.summary else None),
        'notes': 'spread=0.2 pips fallback dataset assumption; commission/slippage/swap not reflected; experimental exit structure check only.',
        'warmup_start': args.warmup_start,
        'warmup_bar_count': warmup_bar_count,
        'evaluation_start': args.start,
        'evaluation_end': args.end,
        'evaluation_bar_count': len(evaluation_bars),
        'indicator_input_start': indicator_bars[0].timestamp.isoformat(),
        'indicator_input_end': indicator_bars[-1].timestamp.isoformat(),
        'start_bound': args.start,
        'end_bound': args.end,
        'htf_v2_enabled': args.htf_v2_enabled,
        'htf_v2_policy': args.htf_v2_policy,
        'htf_v2_h4_ma_fast': args.htf_v2_h4_ma_fast,
        'htf_v2_h4_ma_slow': args.htf_v2_h4_ma_slow,
        'htf_v2_h1_ma_fast': args.htf_v2_h1_ma_fast,
        'htf_v2_slope_window': args.htf_v2_slope_window,
        'sr_v2_enabled': args.sr_v2_enabled,
        'sr_v2_policy': args.sr_v2_policy,
        'sr_v2_window_bars': args.sr_v2_window_bars,
        'sr_v2_near_threshold_pips': args.sr_v2_near_threshold_pips,
        'sr_v2_pip_size': args.sr_v2_pip_size,
        'sr_v2_use_atr_normalized': args.sr_v2_use_atr_normalized,
        'session_v2_enabled': args.session_v2_enabled,
        'session_v2_policy': args.session_v2_policy,
        'session_v2_timezone': args.session_v2_timezone,
        'session_v2_use_day_of_week': args.session_v2_use_day_of_week,
        'session_v2_use_hour_bucket': args.session_v2_use_hour_bucket,
        'session_v2_use_dst_adjustment': args.session_v2_use_dst_adjustment,
    }
    with (output_dir / 'backtest_summary.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(summary.keys()))
        w.writeheader()
        w.writerow(summary)

    (output_dir / 'backtest_summary.md').write_text(
        '\n'.join([
            '# Experimental Exit Backtest Summary',
            '',
            f"- run_id: {summary['run_id']}",
            f"- exit_policy: {summary['exit_policy']}",
            f"- trailing_activation_R: {summary['trailing_activation_R']}",
            f"- entry_time_mode: {summary['entry_time_mode']}",
            f"- trade_count: {summary['trade_count']}",
            f"- total_pnl: {summary['total_pnl']}",
            f"- average_pnl: {summary['average_pnl']}",
            f"- notes: {summary['notes']}",
        ]) + '\n',
        encoding='utf-8',
    )

    print(f"[summary] run_id={args.run_id}")
    print(f"[summary] exit_policy={args.exit_policy}")
    print(f"[summary] trade_count={summary['trade_count']}")
    print(f"[summary] total_pnl={summary['total_pnl']}")
    print(f"[summary] output_dir={output_dir}")

    run_metadata = {
        'run_id': args.run_id,
        'exit_policy': args.exit_policy,
        'trailing_activation_R': args.trailing_activation_r,
        'entry_time_mode': args.entry_time_mode,
        'input_csv': str(input_csv),
        'warmup_start': args.warmup_start,
        'warmup_bar_count': warmup_bar_count,
        'evaluation_start': args.start,
        'evaluation_end': args.end,
        'evaluation_bar_count': len(evaluation_bars),
        'indicator_input_start': indicator_bars[0].timestamp.isoformat(),
        'indicator_input_end': indicator_bars[-1].timestamp.isoformat(),
        'start_bound': args.start,
        'end_bound': args.end,
        'htf_v2_enabled': args.htf_v2_enabled,
        'htf_v2_policy': args.htf_v2_policy,
        'htf_v2_h4_ma_fast': args.htf_v2_h4_ma_fast,
        'htf_v2_h4_ma_slow': args.htf_v2_h4_ma_slow,
        'htf_v2_h1_ma_fast': args.htf_v2_h1_ma_fast,
        'htf_v2_slope_window': args.htf_v2_slope_window,
        'sr_v2_enabled': args.sr_v2_enabled,
        'sr_v2_policy': args.sr_v2_policy,
        'sr_v2_window_bars': args.sr_v2_window_bars,
        'sr_v2_near_threshold_pips': args.sr_v2_near_threshold_pips,
        'sr_v2_pip_size': args.sr_v2_pip_size,
        'sr_v2_use_atr_normalized': args.sr_v2_use_atr_normalized,
        'session_v2_enabled': args.session_v2_enabled,
        'session_v2_policy': args.session_v2_policy,
        'session_v2_timezone': args.session_v2_timezone,
        'session_v2_use_day_of_week': args.session_v2_use_day_of_week,
        'session_v2_use_hour_bucket': args.session_v2_use_hour_bucket,
        'session_v2_use_dst_adjustment': args.session_v2_use_dst_adjustment,
        'bar_count': summary['bar_count'],
        'trade_count': summary['trade_count'],
        'notes': summary['notes'],
    }
    (output_dir / 'run_metadata.json').write_text(json.dumps(run_metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
