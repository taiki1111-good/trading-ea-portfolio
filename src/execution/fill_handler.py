from __future__ import annotations

from src.execution.types import FillResult, OrderRequest, OrderResultType


class FillHandler:
    @staticmethod
    def process(
        order_result: OrderResultType,
        order_request: OrderRequest | None,
        broker_response_raw: dict,
    ) -> FillResult:
        if order_result == "filled" and order_request is not None:
            price = order_request.entry_price_candidate
            return FillResult(
                fill_price=price,
                execution_price=price,
                execution_reason="order was filled in dry run with entry_price_candidate",
            )

        return FillResult(
            fill_price=None,
            execution_price=None,
            execution_reason=(
                f"order_result={order_result} indicates no fill occurred"
            ),
        )
