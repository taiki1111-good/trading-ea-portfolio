from src.risk_filter.types import StopLossConfig, StopLossPlannerResult
from src.risk_filter.reason_catalog import RISK_FIXED_SL_TP, RISK_INVALID_STOP_LOSS
from src.signal.types import SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY


class StopLossPlanner:
    @staticmethod
    def plan(signal_type: str, entry_price_candidate: float, stop_loss_config: StopLossConfig) -> StopLossPlannerResult:
        if stop_loss_config.fixed_stop_distance <= 0:
            return StopLossPlannerResult(
                stop_loss=None,
                stop_loss_reason=(
                    f"{RISK_INVALID_STOP_LOSS}: fixed_stop_distance={stop_loss_config.fixed_stop_distance}"
                ),
            )

        if signal_type == SIGNAL_LONG_ENTRY:
            return StopLossPlannerResult(
                stop_loss=entry_price_candidate - stop_loss_config.fixed_stop_distance,
                stop_loss_reason=(
                    f"{RISK_FIXED_SL_TP} long stop_loss: fixed_stop_distance={stop_loss_config.fixed_stop_distance}"
                ),
            )

        if signal_type == SIGNAL_SHORT_ENTRY:
            return StopLossPlannerResult(
                stop_loss=entry_price_candidate + stop_loss_config.fixed_stop_distance,
                stop_loss_reason=(
                    f"{RISK_FIXED_SL_TP} short stop_loss: fixed_stop_distance={stop_loss_config.fixed_stop_distance}"
                ),
            )

        return StopLossPlannerResult(
            stop_loss=None,
            stop_loss_reason=(
                f"{RISK_INVALID_STOP_LOSS}: non_entry_signal_type={signal_type}"
            ),
        )
