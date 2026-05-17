from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from .types import BacktestTrade


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class BacktestLoggerAdapter:
    """Adapter: BacktestTrade -> trade_log dict (Logger/Evaluator compatible).

    This adapter does NOT write to persistence directly.
    """

    @staticmethod
    def to_trade_log(trade: BacktestTrade, stop_loss: float, take_profit: float) -> Dict[str, Any]:
        signal_type = "long_entry" if trade.direction == "long" else "short_entry"

        # Note: For backtest skeleton, we treat the trade log as a closed-trade record.
        # `fill_price` is mapped to entry_price, `execution_price` to exit_price.
        return {
            "log_time": _utc_now().isoformat(),
            "entry_time": trade.entry_time.isoformat(),
            "exit_time": trade.exit_time.isoformat(),
            "signal_type": signal_type,
            "order_result": "filled",
            "lot": trade.lot,
            "fill_price": trade.entry_price,
            "execution_price": trade.exit_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "pnl": trade.pnl,
            "realized_pnl": trade.realized_pnl,
            "exit_reason": trade.exit_reason,
            "entry_reason": trade.entry_reason,
            "signal_reason": trade.signal_reason,
            "risk_reason": trade.risk_reason,
            "filter_reason": trade.filter_reason,
            "fallback_used": trade.fallback_used,
            "structure_source": trade.structure_source,
            "recent_third_timestamp": trade.recent_third_timestamp,
            "recent_third_direction": trade.recent_third_direction,
            "temporal_lag_bars": trade.temporal_lag_bars,
            "temporal_lookback_bars": trade.temporal_lookback_bars,
            "breakout_direction": trade.breakout_direction,
        }
