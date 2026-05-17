from datetime import datetime, timezone

import pytest

from src.backtest.exit_rule_engine import ExitRuleEngine
from src.backtest.types import BacktestConfig, BacktestPosition
from src.data.types import PriceBar


def _bar(high: float, low: float, close: float) -> PriceBar:
    return PriceBar(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        open=close,
        high=high,
        low=low,
        close=close,
        spread=0.2,
        volume=100.0,
    )


def test_exit_rule_engine_long_take_profit():
    config = BacktestConfig(run_id="t", max_holding_bars=10)
    pos = BacktestPosition(
        direction="long",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=99.0,
        take_profit=101.0,
        entry_index=0,
    )
    decision = ExitRuleEngine.evaluate(
        pos,
        current_bar=_bar(high=101.2, low=99.5, close=100.8),
        current_index=1,
        config=config,
    )
    assert decision.should_exit
    assert decision.exit_reason == "take_profit"
    assert decision.exit_price == pytest.approx(101.0)


def test_exit_rule_engine_no_exit_on_entry_bar_even_if_levels_hit():
    config = BacktestConfig(run_id="t", max_holding_bars=10)
    pos = BacktestPosition(
        direction="long",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=99.0,
        take_profit=101.0,
        entry_index=0,
    )
    decision = ExitRuleEngine.evaluate(
        pos,
        current_bar=_bar(high=101.2, low=98.8, close=100.0),
        current_index=0,
        config=config,
    )
    assert not decision.should_exit
    assert decision.exit_reason == "no_exit_on_entry_bar"


def test_exit_rule_engine_long_stop_loss():
    config = BacktestConfig(run_id="t", max_holding_bars=10)
    pos = BacktestPosition(
        direction="long",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=99.0,
        take_profit=101.0,
        entry_index=0,
    )
    decision = ExitRuleEngine.evaluate(
        pos,
        current_bar=_bar(high=100.3, low=98.8, close=99.2),
        current_index=1,
        config=config,
    )
    assert decision.should_exit
    assert decision.exit_reason == "stop_loss"
    assert decision.exit_price == pytest.approx(99.0)


def test_exit_rule_engine_short_take_profit():
    config = BacktestConfig(run_id="t", max_holding_bars=10)
    pos = BacktestPosition(
        direction="short",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=101.0,
        take_profit=99.0,
        entry_index=0,
    )
    decision = ExitRuleEngine.evaluate(
        pos,
        current_bar=_bar(high=100.4, low=98.7, close=99.1),
        current_index=1,
        config=config,
    )
    assert decision.should_exit
    assert decision.exit_reason == "take_profit"
    assert decision.exit_price == pytest.approx(99.0)


def test_exit_rule_engine_short_stop_loss():
    config = BacktestConfig(run_id="t", max_holding_bars=10)
    pos = BacktestPosition(
        direction="short",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=101.0,
        take_profit=99.0,
        entry_index=0,
    )
    decision = ExitRuleEngine.evaluate(
        pos,
        current_bar=_bar(high=101.2, low=99.6, close=100.9),
        current_index=1,
        config=config,
    )
    assert decision.should_exit
    assert decision.exit_reason == "stop_loss"
    assert decision.exit_price == pytest.approx(101.0)


def test_exit_rule_engine_max_holding_bars_close():
    config = BacktestConfig(run_id="t", max_holding_bars=1)
    pos = BacktestPosition(
        direction="long",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=99.0,
        take_profit=101.0,
        entry_index=0,
    )
    decision = ExitRuleEngine.evaluate(
        pos,
        current_bar=_bar(high=100.5, low=99.5, close=100.2),
        current_index=1,
        config=config,
    )
    assert decision.should_exit
    assert decision.exit_reason == "close"
    assert decision.exit_price == pytest.approx(100.2)


def test_exit_rule_engine_same_bar_sl_tp_prioritizes_stop_loss():
    config = BacktestConfig(run_id="t", max_holding_bars=10)
    pos = BacktestPosition(
        direction="long",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=99.0,
        take_profit=101.0,
        entry_index=0,
    )
    decision = ExitRuleEngine.evaluate(
        pos,
        current_bar=_bar(high=101.2, low=98.8, close=100.0),
        current_index=1,
        config=config,
    )
    assert decision.should_exit
    assert decision.exit_reason == "stop_loss"
    assert decision.exit_price == pytest.approx(99.0)
