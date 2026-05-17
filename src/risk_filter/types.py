from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.signal.types import SignalType


@dataclass(frozen=True)
class EventFilterConfig:
    enabled: bool = True
    event_types: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SpreadFilterConfig:
    max_spread_pips: float = 0.0


@dataclass(frozen=True)
class TradeLimitConfig:
    max_daily_trades: int = 1
    max_losing_streak: int = 1


@dataclass(frozen=True)
class PositionSizerConfig:
    fixed_lot: float = 0.0


@dataclass(frozen=True)
class StopLossConfig:
    fixed_stop_distance: float = 0.0


@dataclass(frozen=True)
class TakeProfitConfig:
    fixed_take_profit_distance: float = 0.0


@dataclass(frozen=True)
class EventFilterResult:
    event_risk_flag: bool
    event_filter_reason: str


@dataclass(frozen=True)
class SpreadFilterResult:
    spread_ok: bool
    spread_filter_reason: str


@dataclass(frozen=True)
class TradeLimitFilterResult:
    limit_ok: bool
    limit_filter_reason: str
    max_trade_reached_flag: bool


@dataclass(frozen=True)
class PositionSizerResult:
    lot: Optional[float]
    size_reason: str


@dataclass(frozen=True)
class StopLossPlannerResult:
    stop_loss: Optional[float]
    stop_loss_reason: str


@dataclass(frozen=True)
class TakeProfitPlannerResult:
    take_profit: Optional[float]
    take_profit_reason: str


@dataclass(frozen=True)
class RiskFilterResult:
    trade_ok: bool
    lot: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_reason: str
    filter_reason: str
    event_risk_flag: bool
    spread_ok: bool
    limit_ok: bool
    max_trade_reached_flag: bool
    sub_reasons: List[str] = field(default_factory=list)
