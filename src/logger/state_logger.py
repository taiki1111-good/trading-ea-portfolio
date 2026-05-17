from __future__ import annotations

from typing import Optional

from .types import PositionState, StateLogRecord, _normalize_reason, utc_now


class StateLogger:
    @staticmethod
    def log(
        previous_state: PositionState,
        next_state: PositionState,
        position_state: PositionState,
        transition_reason: Optional[str] = None,
        order_result: Optional[str] = None,
        execution_reason: Optional[str] = None,
    ) -> StateLogRecord:
        return StateLogRecord(
            log_time=utc_now(),
            previous_state=previous_state,
            next_state=next_state,
            position_state=position_state,
            transition_reason=_normalize_reason(transition_reason or "", "transition reason unavailable"),
            order_result=order_result or "none",
            execution_reason=_normalize_reason(execution_reason or "", "execution reason unavailable"),
        )
