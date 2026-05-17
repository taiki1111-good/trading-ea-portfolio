from src.execution.order_sender import OrderSender
from src.execution.types import ExecutionConfig, OrderRequest


def test_order_sender_returns_filled_in_dry_run():
    order_request = OrderRequest(
        order_side="buy",
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        entry_price_candidate=1.1,
        signal_type="long_entry",
    )
    result = OrderSender.send(order_request, ExecutionConfig(dry_run=True))

    assert result.order_result == "filled"
    assert result.broker_response_raw["dry_run"] is True
    assert result.execution_reason


def test_order_sender_returns_none_for_missing_request():
    result = OrderSender.send(None, ExecutionConfig(dry_run=True))

    assert result.order_result == "none"
    assert "no send attempted" in result.execution_reason


def test_order_sender_returns_failed_when_dry_run_false():
    order_request = OrderRequest(
        order_side="sell",
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        entry_price_candidate=1.1,
        signal_type="short_entry",
    )
    result = OrderSender.send(order_request, ExecutionConfig(dry_run=False))

    assert result.order_result == "failed"
    assert "not implemented" in result.execution_reason
    assert result.broker_response_raw["dry_run"] is False
