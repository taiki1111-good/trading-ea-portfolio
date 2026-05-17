from src.risk_filter.assembler import RiskAssembler
from src.risk_filter.event_filter import EventFilter
from src.risk_filter.spread_filter import SpreadFilter
from src.risk_filter.trade_limit_filter import TradeLimitFilter
from src.risk_filter.position_sizer import PositionSizer
from src.risk_filter.stop_loss_planner import StopLossPlanner
from src.risk_filter.take_profit_planner import TakeProfitPlanner
from src.risk_filter.types import (
    EventFilterConfig,
    SpreadFilterConfig,
    TradeLimitConfig,
    PositionSizerConfig,
    StopLossConfig,
    TakeProfitConfig,
)
from src.signal.types import SignalResult


def _build_signal(entry_signal: bool, signal_type: str) -> SignalResult:
    return SignalResult(
        entry_signal=entry_signal,
        exit_signal=False,
        signal_type=signal_type,
        signal_reason=f"signal_type={signal_type}",
        direction_aligned=True,
        pattern_allowed=True,
        sub_reasons=[f"signal_type={signal_type}"],
    )


def _run_risk_filter(signal: SignalResult, event_flag: bool, spread: float, daily_trade_count: int, losing_streak: int):
    event_result = EventFilter.check(event_flag, "cpi", EventFilterConfig())
    spread_result = SpreadFilter.check(spread, SpreadFilterConfig(max_spread_pips=2.5))
    limit_result = TradeLimitFilter.check(
        daily_trade_count=daily_trade_count,
        losing_streak=losing_streak,
        trade_limit_config=TradeLimitConfig(max_daily_trades=3, max_losing_streak=2),
    )
    size_result = PositionSizer.size(1000.0, PositionSizerConfig(fixed_lot=0.1))
    stop_result = StopLossPlanner.plan(signal.signal_type, 1.2345, StopLossConfig(fixed_stop_distance=0.01))
    take_profit_result = TakeProfitPlanner.plan(signal.signal_type, 1.2345, TakeProfitConfig(fixed_take_profit_distance=0.02))

    return RiskAssembler.assemble(
        entry_signal=signal.entry_signal,
        exit_signal=signal.exit_signal,
        signal_type=signal.signal_type,
        signal_reason=signal.signal_reason,
        event_risk_flag=event_result.event_risk_flag,
        spread_ok=spread_result.spread_ok,
        limit_ok=limit_result.limit_ok,
        max_trade_reached_flag=limit_result.max_trade_reached_flag,
        lot=size_result.lot,
        stop_loss=stop_result.stop_loss,
        take_profit=take_profit_result.take_profit,
        sub_reasons=[
            signal.signal_reason,
            event_result.event_filter_reason,
            spread_result.spread_filter_reason,
            limit_result.limit_filter_reason,
            size_result.size_reason,
            stop_result.stop_loss_reason,
            take_profit_result.take_profit_reason,
        ],
    )


def test_signal_to_risk_filter_long_entry_passes():
    signal = _build_signal(True, "long_entry")
    result = _run_risk_filter(signal, event_flag=False, spread=2.0, daily_trade_count=0, losing_streak=0)

    assert result.trade_ok is True
    assert result.lot == 0.1
    assert result.stop_loss == 1.2245
    assert result.take_profit == 1.2545
    assert "fixed_sl_tp" in result.risk_reason
    assert "placeholder_fixed_lot" in result.risk_reason
    assert result.filter_reason == "all risk filters passed"


def test_signal_to_risk_filter_short_entry_passes():
    signal = _build_signal(True, "short_entry")
    result = _run_risk_filter(signal, event_flag=False, spread=2.0, daily_trade_count=0, losing_streak=0)

    assert result.trade_ok is True
    assert result.lot == 0.1
    assert result.stop_loss == 1.2445
    assert result.take_profit == 1.2145


def test_signal_to_risk_filter_none_signal_fails():
    signal = _build_signal(True, "none")
    result = _run_risk_filter(signal, event_flag=False, spread=2.0, daily_trade_count=0, losing_streak=0)

    assert result.trade_ok is False
    assert result.filter_reason


def test_signal_to_risk_filter_exit_signal_type_fails():
    signal = _build_signal(True, "exit")
    result = _run_risk_filter(signal, event_flag=False, spread=2.0, daily_trade_count=0, losing_streak=0)

    assert result.trade_ok is False
    assert "risk_contract_invalid" in result.filter_reason


def test_signal_to_risk_filter_event_flag_true_fails():
    signal = _build_signal(True, "long_entry")
    result = _run_risk_filter(signal, event_flag=True, spread=2.0, daily_trade_count=0, losing_streak=0)

    assert result.trade_ok is False
    assert "event_risk" in result.filter_reason


def test_signal_to_risk_filter_spread_exceeded_fails():
    signal = _build_signal(True, "long_entry")
    result = _run_risk_filter(signal, event_flag=False, spread=5.0, daily_trade_count=0, losing_streak=0)

    assert result.trade_ok is False
    assert "spread_too_wide" in result.filter_reason


def test_signal_to_risk_filter_daily_trade_limit_fails():
    signal = _build_signal(True, "long_entry")
    result = _run_risk_filter(signal, event_flag=False, spread=2.0, daily_trade_count=3, losing_streak=0)

    assert result.trade_ok is False
    assert result.max_trade_reached_flag is True
    assert result.filter_reason
    assert "trade_limit_reached" in result.filter_reason


def test_signal_to_risk_filter_invalid_lot_fails():
    signal = _build_signal(True, "long_entry")
    event_result = EventFilter.check(False, "cpi", EventFilterConfig())
    spread_result = SpreadFilter.check(2.0, SpreadFilterConfig(max_spread_pips=2.5))
    limit_result = TradeLimitFilter.check(
        daily_trade_count=0,
        losing_streak=0,
        trade_limit_config=TradeLimitConfig(max_daily_trades=3, max_losing_streak=2),
    )
    size_result = PositionSizer.size(1000.0, PositionSizerConfig(fixed_lot=0.0))
    stop_result = StopLossPlanner.plan(signal.signal_type, 1.2345, StopLossConfig(fixed_stop_distance=0.01))
    take_profit_result = TakeProfitPlanner.plan(signal.signal_type, 1.2345, TakeProfitConfig(fixed_take_profit_distance=0.02))

    result = RiskAssembler.assemble(
        entry_signal=signal.entry_signal,
        exit_signal=signal.exit_signal,
        signal_type=signal.signal_type,
        signal_reason=signal.signal_reason,
        event_risk_flag=event_result.event_risk_flag,
        spread_ok=spread_result.spread_ok,
        limit_ok=limit_result.limit_ok,
        max_trade_reached_flag=limit_result.max_trade_reached_flag,
        lot=size_result.lot,
        stop_loss=stop_result.stop_loss,
        take_profit=take_profit_result.take_profit,
        sub_reasons=[size_result.size_reason],
    )

    assert result.trade_ok is False
    assert "invalid_lot" in result.risk_reason
