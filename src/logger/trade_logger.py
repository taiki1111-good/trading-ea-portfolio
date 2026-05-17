from __future__ import annotations

from typing import Optional

from .types import TradeLogRecord, _normalize_reason, utc_now


class TradeLogger:
    @staticmethod
    def log(
        order_result: str,
        lot: Optional[float] = None,
        fill_price: Optional[float] = None,
        execution_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        signal_type: Optional[str] = None,
        trade_ok: bool = False,
        risk_reason: Optional[str] = None,
        execution_reason: Optional[str] = None,
        pnl: Optional[float] = None,
        realized_pnl: Optional[float] = None,
        unrealized_pnl: Optional[float] = None,
    ) -> TradeLogRecord:
        return TradeLogRecord(
            log_time=utc_now(),
            order_result=order_result,
            lot=lot,
            fill_price=fill_price,
            execution_price=execution_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            signal_type=_normalize_reason(signal_type or "", "none"),
            trade_ok=trade_ok,
            risk_reason=_normalize_reason(risk_reason or "", "risk reason unavailable"),
            execution_reason=_normalize_reason(execution_reason or "", "execution reason unavailable"),
            pnl=pnl,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
        )
