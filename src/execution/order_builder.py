from __future__ import annotations

from src.execution.types import (
    OrderRequest,
    OrderRequestResult,
    ExecutionConfig,
    OrderResultType,
    SignalType,
)
from src.signal.types import SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY


class OrderBuilder:
    @staticmethod
    def build(
        trade_ok: bool,
        signal_type: str,
        lot: float | None,
        stop_loss: float | None,
        take_profit: float | None,
        entry_price_candidate: float | None,
        execution_config: ExecutionConfig,
    ) -> OrderRequestResult:
        if not trade_ok:
            return OrderRequestResult(
                order_request=None,
                request_reason="trade_ok is false, no order request generated",
            )

        if signal_type == SIGNAL_LONG_ENTRY:
            order_side = "buy"
        elif signal_type == SIGNAL_SHORT_ENTRY:
            order_side = "sell"
        else:
            return OrderRequestResult(
                order_request=None,
                request_reason=(
                    f"signal_type={signal_type} is not an entry type for order creation"
                ),
            )

        if lot is None or lot <= 0:
            return OrderRequestResult(
                order_request=None,
                request_reason=(
                    "lot is missing or invalid for order creation"
                ),
            )

        if stop_loss is None:
            return OrderRequestResult(
                order_request=None,
                request_reason="stop_loss is missing for order creation",
            )

        if take_profit is None:
            return OrderRequestResult(
                order_request=None,
                request_reason="take_profit is missing for order creation",
            )

        if entry_price_candidate is None:
            return OrderRequestResult(
                order_request=None,
                request_reason="entry_price_candidate is missing for order creation",
            )

        return OrderRequestResult(
            order_request=OrderRequest(
                order_side=order_side,
                lot=lot,
                stop_loss=stop_loss,
                take_profit=take_profit,
                entry_price_candidate=entry_price_candidate,
                signal_type=signal_type,
            ),
            request_reason="order request created successfully",
        )
