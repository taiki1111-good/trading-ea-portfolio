from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from src.data.types import PriceBar, PriceFrame
from src.evaluator.metrics_calculator import MetricsCalculator
from src.evaluator.report_assembler import ReportAssembler
from src.evaluator.signal_analyzer import SignalAnalyzer

from .backtest_logger_adapter import BacktestLoggerAdapter
from .exit_rule_engine import ExitRuleEngine
from .pnl_calculator import PnLCalculator
from .position_tracker import PositionTracker
from .types import BacktestConfig, BacktestPosition, BacktestResult, BacktestSummary, BacktestTrade


@dataclass(frozen=True)
class EntryEvent:
    entry_index: int
    direction: str
    lot: float
    stop_loss: float
    take_profit: float
    entry_reason: str
    signal_reason: str = ""
    risk_reason: str = ""
    filter_reason: str = ""
    fallback_used: bool = False
    structure_source: str = ""
    recent_third_timestamp: str = ""
    recent_third_direction: str = ""
    temporal_lag_bars: int | None = None
    temporal_lookback_bars: int | None = None
    breakout_direction: str = ""


EntryEventProvider = Callable[[int, List[PriceBar]], Optional[EntryEvent]]


class BacktestRunner:
    """Minimal BacktestRunner skeleton for research backtest.

    Input:
    - Receives a Data-layer validated/normalized price_frame (bars).
    - Does NOT re-run DataLoader for each bar.

    Signal/RiskFilter integration:
    - In current research phase, integration is supplied via `entry_event_provider`
      (typically `PipelineAdapter`) rather than hard-wiring modules in this runner.

    Future leak prevention:
    - At each timestep i, only bars[:i+1] can be used for any decision.
    - This runner passes `bars[:i+1]` to the provider and does not expose future bars.

    Intrabar leak prevention (initial fixed rule):
    - Entry is treated as filled at the current bar close (bar i close).
    - Exit checks start from the next bar (i+1). No exit on the entry bar.

    Notes:
    - This runner does NOT connect to real broker / OANDA API / real order sending.
    - This is a research/structure-validation skeleton, not operation-like execution.
    - `decision_logs/state_logs/event_logs` are still minimal; current traceability is trade_logs-first.
    """

    @staticmethod
    def run(
        price_frame: PriceFrame,
        config: BacktestConfig,
        entry_event_provider: Optional[EntryEventProvider] = None,
    ) -> BacktestResult:
        bars = list(price_frame)
        tracker = PositionTracker()

        trades: List[BacktestTrade] = []
        trade_logs: List[Dict[str, Any]] = []
        decision_logs: List[Dict[str, Any]] = []

        start_time: Optional[datetime] = bars[0].timestamp if bars else None
        end_time: Optional[datetime] = bars[-1].timestamp if bars else None

        def default_entry_provider(i: int, window: List[PriceBar]) -> Optional[EntryEvent]:
            _ = window
            return None

        provider = entry_event_provider or default_entry_provider
        reset_hook = getattr(provider, "reset_run_state", None)
        if callable(reset_hook):
            reset_hook()

        for i, bar in enumerate(bars):
            # Future leak prevention: only the current window can be used.
            window = bars[: i + 1]

            if not tracker.has_open_position():
                entry_event = provider(i, window)
                trace_hook = getattr(provider, "get_last_decision_trace", None)
                if callable(trace_hook):
                    trace = trace_hook()
                    if trace:
                        decision_logs.append(
                            {
                                "log_time": datetime.now(timezone.utc).isoformat(),
                                "bar_index": i,
                                "timestamp": bar.timestamp.isoformat(),
                                **trace,
                            }
                        )
                if entry_event is not None:
                    if not entry_event.entry_reason.strip():
                        raise ValueError("entry_reason must be non-empty")
                    opened = tracker.open_position(
                        BacktestPosition(
                            direction=entry_event.direction,  # type: ignore[arg-type]
                            entry_price=bar.close,
                            entry_time=bar.timestamp,
                            lot=entry_event.lot,
                            stop_loss=entry_event.stop_loss,
                            take_profit=entry_event.take_profit,
                            entry_index=i,
                            entry_reason=entry_event.entry_reason,
                            signal_reason=entry_event.signal_reason,
                            risk_reason=entry_event.risk_reason,
                            filter_reason=entry_event.filter_reason,
                            fallback_used=entry_event.fallback_used,
                            structure_source=entry_event.structure_source,
                            recent_third_timestamp=entry_event.recent_third_timestamp,
                            recent_third_direction=entry_event.recent_third_direction,
                            temporal_lag_bars=entry_event.temporal_lag_bars,
                            temporal_lookback_bars=entry_event.temporal_lookback_bars,
                            breakout_direction=entry_event.breakout_direction,
                        )
                    )
                    if not opened:
                        # single position only; ignore entry
                        continue
                    # Exit decision on the entry bar is intentionally suppressed by ExitRuleEngine
                    # (`no_exit_on_entry_bar`) to prevent intrabar leak.

            position = tracker.get_position()
            if position is None:
                continue

            decision = ExitRuleEngine.evaluate(
                position=position,
                current_bar=bar,
                current_index=i,
                config=config,
            )
            if not decision.should_exit:
                continue
            if decision.exit_price is None:
                raise ValueError("ExitDecision.should_exit=True requires exit_price")
            if not decision.exit_reason.strip():
                raise ValueError("exit_reason must be non-empty")

            pnl = PnLCalculator.calculate(
                direction=position.direction,
                entry_price=position.entry_price,
                exit_price=decision.exit_price,
                lot=position.lot,
            )
            trade = BacktestTrade(
                direction=position.direction,
                entry_price=position.entry_price,
                exit_price=decision.exit_price,
                entry_time=position.entry_time,
                exit_time=bar.timestamp,
                lot=position.lot,
                pnl=pnl,
                realized_pnl=pnl,
                exit_reason=decision.exit_reason,
                entry_reason=position.entry_reason,
                signal_reason=position.signal_reason,
                risk_reason=position.risk_reason,
                filter_reason=position.filter_reason,
                fallback_used=position.fallback_used,
                structure_source=position.structure_source,
                recent_third_timestamp=position.recent_third_timestamp,
                recent_third_direction=position.recent_third_direction,
                temporal_lag_bars=position.temporal_lag_bars,
                temporal_lookback_bars=position.temporal_lookback_bars,
                breakout_direction=position.breakout_direction,
            )
            trades.append(trade)
            trade_logs.append(
                BacktestLoggerAdapter.to_trade_log(
                    trade=trade,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                )
            )
            tracker.close_position()

        total_pnl = sum(trade.realized_pnl for trade in trades)
        average_pnl = (total_pnl / len(trades)) if trades else None
        summary = BacktestSummary(
            run_id=config.run_id,
            start_time=start_time,
            end_time=end_time,
            bar_count=len(bars),
            trade_count=len(trades),
            total_pnl=total_pnl,
            average_pnl=average_pnl,
            summary_reason="Backtest completed with initial skeleton runner",
        )

        # Evaluator integration (minimal): compute metrics + signal stats from trade_logs only.
        metrics_result = MetricsCalculator.calculate(trade_logs)
        signal_stats, signal_warnings = SignalAnalyzer.analyze(trade_logs)
        evaluator_result = ReportAssembler.assemble(
            metrics_result=metrics_result,
            structure_stats={},
            filter_stats={},
            signal_stats=signal_stats,
            warnings=list(signal_warnings),
        )

        return BacktestResult(
            config=config,
            trades=trades,
            trade_logs=trade_logs,
            decision_logs=decision_logs,
            state_logs=[],
            event_logs=[],
            summary=summary,
            evaluator_result=evaluator_result.summary_report.__dict__,
        )
