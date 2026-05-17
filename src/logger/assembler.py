from __future__ import annotations

from .types import DecisionLogRecord, EventLogRecord, LoggerBundle, StateLogRecord, TradeLogRecord


class LogAssembler:
    @staticmethod
    def assemble(
        decision_log: DecisionLogRecord,
        trade_log: TradeLogRecord,
        state_log: StateLogRecord,
        event_log: EventLogRecord,
    ) -> LoggerBundle:
        return LoggerBundle(
            decision_log=decision_log,
            trade_log=trade_log,
            state_log=state_log,
            event_log=event_log,
        )
