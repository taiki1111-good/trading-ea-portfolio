from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

OrderResultType = Literal["filled", "rejected", "cancelled", "failed", "none"]
PositionState = Literal["IDLE", "ENTRY_PENDING", "POSITION_OPEN", "EXIT_PENDING", "SUSPENDED", "ERROR"]
OrderSide = Literal["buy", "sell"]
SignalType = Literal["long_entry", "short_entry", "exit", "none"]


@dataclass(frozen=True)
class ExecutionConfig:
    dry_run: bool = True


@dataclass(frozen=True)
class OrderRequest:
    order_side: OrderSide
    lot: float
    stop_loss: float
    take_profit: float
    entry_price_candidate: float
    signal_type: SignalType


@dataclass(frozen=True)
class OrderRequestResult:
    order_request: Optional[OrderRequest]
    request_reason: str


@dataclass(frozen=True)
class OrderSendResult:
    order_result: OrderResultType
    broker_response_raw: Dict[str, Any]
    execution_reason: str


@dataclass(frozen=True)
class FillResult:
    fill_price: Optional[float]
    execution_price: Optional[float]
    execution_reason: str


@dataclass(frozen=True)
class StateTransitionResult:
    previous_state: PositionState
    next_state: PositionState
    transition_reason: str
