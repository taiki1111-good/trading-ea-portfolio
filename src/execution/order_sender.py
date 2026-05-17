from __future__ import annotations

from src.execution.types import OrderRequest, OrderSendResult, ExecutionConfig


class OrderSender:
    @staticmethod
    def send(order_request: OrderRequest | None, execution_config: ExecutionConfig) -> OrderSendResult:
        if order_request is None:
            return OrderSendResult(
                order_result="none",
                broker_response_raw={"reason": "no order_request provided"},
                execution_reason="order_request is None, no send attempted",
            )

        if execution_config.dry_run:
            return OrderSendResult(
                order_result="filled",
                broker_response_raw={
                    "dry_run": True,
                    "order_side": order_request.order_side,
                    "lot": order_request.lot,
                },
                execution_reason="dry run order simulated as filled",
            )

        return OrderSendResult(
            order_result="failed",
            broker_response_raw={
                "dry_run": False,
                "reason": "real broker sending is not implemented",
            },
            execution_reason="real broker sending is not implemented",
        )
