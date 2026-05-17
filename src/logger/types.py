from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

OrderResultType = Literal["filled", "rejected", "cancelled", "failed", "none"]
PositionState = Literal["IDLE", "ENTRY_PENDING", "POSITION_OPEN", "EXIT_PENDING", "SUSPENDED", "ERROR"]
SignalType = Literal["long_entry", "short_entry", "exit", "none"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_reason(reason: str, fallback: str) -> str:
    normalized = reason.strip() if reason is not None else ""
    return normalized if normalized else fallback


def _to_dict(record: Any) -> Dict[str, Any]:
    result = asdict(record)
    if "log_time" in result and isinstance(result["log_time"], datetime):
        result["log_time"] = result["log_time"].isoformat()
    if "timestamp" in result and isinstance(result["timestamp"], datetime):
        result["timestamp"] = result["timestamp"].isoformat()
    return result


@dataclass(frozen=True)
class DecisionLogRecord:
    log_time: datetime = field(default_factory=utc_now)
    htf_context_reason: str = "reason unavailable"
    pattern_reason: str = "reason unavailable"
    signal_reason: str = "reason unavailable"
    risk_reason: str = "reason unavailable"
    filter_reason: str = "reason unavailable"
    execution_reason: str = "reason unavailable"
    structure_type: str = "unknown"
    signal_type: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class TradeLogRecord:
    log_time: datetime = field(default_factory=utc_now)
    order_result: OrderResultType = "none"
    lot: Optional[float] = None
    fill_price: Optional[float] = None
    execution_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    signal_type: str = "none"
    trade_ok: bool = False
    risk_reason: str = "reason unavailable"
    execution_reason: str = "reason unavailable"
    pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class StateLogRecord:
    log_time: datetime = field(default_factory=utc_now)
    previous_state: PositionState = "IDLE"
    next_state: PositionState = "IDLE"
    position_state: PositionState = "IDLE"
    transition_reason: str = "reason unavailable"
    order_result: OrderResultType = "none"
    execution_reason: str = "reason unavailable"

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class EventLogRecord:
    log_time: datetime = field(default_factory=utc_now)
    timestamp: datetime = field(default_factory=utc_now)
    event_flag: bool = False
    event_type: str = "unknown"
    event_risk_flag: bool = False
    filter_reason: str = "reason unavailable"

    def to_dict(self) -> Dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class LoggerBundle:
    decision_log: DecisionLogRecord
    trade_log: TradeLogRecord
    state_log: StateLogRecord
    event_log: EventLogRecord

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_log": self.decision_log.to_dict(),
            "trade_log": self.trade_log.to_dict(),
            "state_log": self.state_log.to_dict(),
            "event_log": self.event_log.to_dict(),
        }
