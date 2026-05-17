from src.execution.fill_handler import FillHandler
from src.execution.types import OrderRequest


def test_fill_handler_returns_prices_for_filled_order():
    order_request = OrderRequest(
        order_side="buy",
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        entry_price_candidate=1.1,
        signal_type="long_entry",
    )
    result = FillHandler.process("filled", order_request, {})

    assert result.fill_price == 1.1
    assert result.execution_price == 1.1
    assert "dry run" in result.execution_reason


def test_fill_handler_returns_none_for_failed_order():
    order_request = OrderRequest(
        order_side="sell",
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        entry_price_candidate=1.1,
        signal_type="short_entry",
    )
    result = FillHandler.process("failed", order_request, {})

    assert result.fill_price is None
    assert result.execution_price is None
    assert "no fill occurred" in result.execution_reason
