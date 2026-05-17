from __future__ import annotations

from dataclasses import dataclass

from src.data.types import PriceBar

from .types import BacktestConfig, BacktestPosition, ExitDecision


@dataclass(frozen=True)
class ExitRuleEngine:
    """Initial exit rules for backtest skeleton.

    Exit check uses ONLY the current bar OHLC.
    Same-bar SL/TP hit is resolved as stop_loss first (conservative).

    Intrabar leak prevention (initial fixed rule):
    - No exit decision is allowed on the entry bar (`current_index == entry_index`).
      Entry is treated as filled at bar close, and exit starts from the next bar.
    """

    @staticmethod
    def evaluate(
        position: BacktestPosition,
        current_bar: PriceBar,
        current_index: int,
        config: BacktestConfig,
    ) -> ExitDecision:
        if current_index < position.entry_index:
            return ExitDecision(
                should_exit=False,
                exit_price=None,
                exit_reason="no_exit_before_entry_index",
            )

        if current_index == position.entry_index:
            return ExitDecision(
                should_exit=False,
                exit_price=None,
                exit_reason="no_exit_on_entry_bar",
            )

        # Number of bars held AFTER entry bar.
        holding_bars = current_index - position.entry_index

        if position.direction == "long":
            sl_hit = current_bar.low <= position.stop_loss
            tp_hit = current_bar.high >= position.take_profit

            if sl_hit:
                return ExitDecision(True, position.stop_loss, "stop_loss")
            if tp_hit:
                return ExitDecision(True, position.take_profit, "take_profit")
            if holding_bars >= config.max_holding_bars:
                return ExitDecision(True, current_bar.close, "close")

            return ExitDecision(False, None, "no_exit")

        if position.direction == "short":
            sl_hit = current_bar.high >= position.stop_loss
            tp_hit = current_bar.low <= position.take_profit

            if sl_hit:
                return ExitDecision(True, position.stop_loss, "stop_loss")
            if tp_hit:
                return ExitDecision(True, position.take_profit, "take_profit")
            if holding_bars >= config.max_holding_bars:
                return ExitDecision(True, current_bar.close, "close")

            return ExitDecision(False, None, "no_exit")

        return ExitDecision(
            should_exit=False,
            exit_price=None,
            exit_reason=f"unsupported_direction:{position.direction}",
        )
