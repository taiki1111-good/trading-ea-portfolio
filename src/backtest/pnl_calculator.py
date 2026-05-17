from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PnLCalculator:
    """Raw PnL calculator for initial backtest skeleton.

    Notes:
    - Raw price difference base.
    - lot is applied as `price_diff * lot`.
    - spread / fee / swap are intentionally NOT modeled in this initial skeleton (TODO/TBD).
    """

    @staticmethod
    def calculate(direction: str, entry_price: float, exit_price: float, lot: float) -> float:
        if direction == "long":
            diff = exit_price - entry_price
        elif direction == "short":
            diff = entry_price - exit_price
        else:
            raise ValueError(f"Unsupported direction: {direction}")

        return diff * lot

