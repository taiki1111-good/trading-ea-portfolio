from src.risk_filter.types import TakeProfitConfig, TakeProfitPlannerResult
from src.risk_filter.reason_catalog import RISK_FIXED_SL_TP, RISK_INVALID_TAKE_PROFIT
from src.signal.types import SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY


class TakeProfitPlanner:
    @staticmethod
    def plan(signal_type: str, entry_price_candidate: float, take_profit_config: TakeProfitConfig) -> TakeProfitPlannerResult:
        if take_profit_config.fixed_take_profit_distance <= 0:
            return TakeProfitPlannerResult(
                take_profit=None,
                take_profit_reason=(
                    f"{RISK_INVALID_TAKE_PROFIT}: fixed_take_profit_distance={take_profit_config.fixed_take_profit_distance}"
                ),
            )

        if signal_type == SIGNAL_LONG_ENTRY:
            return TakeProfitPlannerResult(
                take_profit=entry_price_candidate + take_profit_config.fixed_take_profit_distance,
                take_profit_reason=(
                    f"{RISK_FIXED_SL_TP} long take_profit: fixed_take_profit_distance={take_profit_config.fixed_take_profit_distance}"
                ),
            )

        if signal_type == SIGNAL_SHORT_ENTRY:
            return TakeProfitPlannerResult(
                take_profit=entry_price_candidate - take_profit_config.fixed_take_profit_distance,
                take_profit_reason=(
                    f"{RISK_FIXED_SL_TP} short take_profit: fixed_take_profit_distance={take_profit_config.fixed_take_profit_distance}"
                ),
            )

        return TakeProfitPlannerResult(
            take_profit=None,
            take_profit_reason=(
                f"{RISK_INVALID_TAKE_PROFIT}: non_entry_signal_type={signal_type}"
            ),
        )
