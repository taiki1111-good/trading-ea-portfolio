from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

Direction = Literal["long", "short"]
ExitReason = Literal["stop_loss", "take_profit", "close", "none"]


@dataclass(frozen=True)
class BacktestConfig:
    run_id: str
    max_holding_bars: int
    initial_balance: Optional[float] = None


@dataclass(frozen=True)
class BacktestPosition:
    direction: Direction
    entry_price: float
    entry_time: datetime
    lot: float
    stop_loss: float
    take_profit: float
    entry_index: int
    entry_reason: str = ""
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


@dataclass(frozen=True)
class ExitDecision:
    should_exit: bool
    exit_price: Optional[float]
    exit_reason: str


@dataclass(frozen=True)
class BacktestTrade:
    direction: Direction
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    lot: float
    pnl: float
    realized_pnl: float
    exit_reason: str
    entry_reason: str = ""
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


@dataclass(frozen=True)
class BacktestSummary:
    run_id: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    bar_count: int
    trade_count: int
    total_pnl: float
    average_pnl: Optional[float]
    summary_reason: str


@dataclass(frozen=True)
class BacktestResult:
    config: BacktestConfig
    trades: List[BacktestTrade] = field(default_factory=list)
    trade_logs: List[Dict[str, Any]] = field(default_factory=list)
    decision_logs: List[Dict[str, Any]] = field(default_factory=list)
    state_logs: List[Dict[str, Any]] = field(default_factory=list)
    event_logs: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[BacktestSummary] = None
    evaluator_result: Optional[Dict[str, Any]] = None
