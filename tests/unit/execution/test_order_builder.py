from src.execution.order_builder import OrderBuilder
from src.execution.types import ExecutionConfig


def test_order_builder_creates_buy_request_for_long_entry():
    result = OrderBuilder.build(
        trade_ok=True,
        signal_type="long_entry",
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        entry_price_candidate=1.1,
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.order_request is not None
    assert result.order_request.order_side == "buy"
    assert result.request_reason == "order request created successfully"


def test_order_builder_creates_sell_request_for_short_entry():
    result = OrderBuilder.build(
        trade_ok=True,
        signal_type="short_entry",
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        entry_price_candidate=1.1,
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.order_request is not None
    assert result.order_request.order_side == "sell"


def test_order_builder_returns_none_when_trade_ok_false():
    result = OrderBuilder.build(
        trade_ok=False,
        signal_type="long_entry",
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        entry_price_candidate=1.1,
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.order_request is None
    assert "trade_ok is false" in result.request_reason


def test_order_builder_returns_none_for_missing_values():
    result = OrderBuilder.build(
        trade_ok=True,
        signal_type="long_entry",
        lot=None,
        stop_loss=None,
        take_profit=None,
        entry_price_candidate=None,
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.order_request is None
    assert result.request_reason
