import math

from src.risk_filter.reason_catalog import (
    RISK_INVALID_ACCOUNT_BALANCE,
    RISK_INVALID_LOT,
    RISK_PLACEHOLDER_FIXED_LOT,
)
from src.risk_filter.types import PositionSizerConfig, PositionSizerResult


class PositionSizer:
    @staticmethod
    def size(account_balance: float, position_sizer_config: PositionSizerConfig) -> PositionSizerResult:
        fixed_lot = position_sizer_config.fixed_lot
        valid_balance = (
            isinstance(account_balance, (int, float))
            and not isinstance(account_balance, bool)
            and math.isfinite(float(account_balance))
            and float(account_balance) > 0
        )
        valid_fixed_lot = (
            isinstance(fixed_lot, (int, float))
            and not isinstance(fixed_lot, bool)
            and math.isfinite(float(fixed_lot))
            and float(fixed_lot) > 0
        )

        if valid_balance and valid_fixed_lot:
            return PositionSizerResult(
                lot=float(fixed_lot),
                size_reason=f"{RISK_PLACEHOLDER_FIXED_LOT}: fixed_lot={fixed_lot}",
            )

        invalid_reasons: list[str] = [f"{RISK_INVALID_LOT}: fixed_lot={fixed_lot}"]
        if not valid_balance:
            invalid_reasons.append(f"{RISK_INVALID_ACCOUNT_BALANCE}: account_balance={account_balance}")

        return PositionSizerResult(
            lot=None,
            size_reason=" | ".join(invalid_reasons),
        )
