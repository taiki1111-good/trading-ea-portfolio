import math

from src.risk_filter.reason_catalog import (
    RISK_ALL_FILTERS_PASSED_LEGACY,
    RISK_CONTRACT_INVALID,
    RISK_EVENT,
    RISK_FIXED_SL_TP,
    RISK_MISSING_ENTRY_SIGNAL,
    RISK_INVALID_LOT,
    RISK_INVALID_STOP_LOSS,
    RISK_INVALID_TAKE_PROFIT,
    RISK_PLACEHOLDER_FIXED_LOT,
    RISK_SPREAD_TOO_WIDE,
    RISK_TRADE_LIMIT_REACHED,
    RISK_UNSUPPORTED_SIGNAL_TYPE,
)
from src.risk_filter.types import RiskFilterResult
from src.signal.types import SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY


def _is_valid_positive_number(value: float | None) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    return math.isfinite(float(value)) and float(value) > 0


class RiskAssembler:
    @staticmethod
    def assemble(
        entry_signal: bool,
        exit_signal: bool,
        signal_type: str,
        signal_reason: str,
        event_risk_flag: bool,
        spread_ok: bool,
        limit_ok: bool,
        max_trade_reached_flag: bool,
        lot: float | None,
        stop_loss: float | None,
        take_profit: float | None,
        sub_reasons: list[str] | None = None,
    ) -> RiskFilterResult:
        reasons: list[str] = [signal_reason.strip()] if signal_reason and signal_reason.strip() else []
        reasons.extend([reason.strip() for reason in (sub_reasons or []) if reason and reason.strip()])

        filter_reasons: list[str] = []
        risk_explanations: list[str] = []
        entry_signal_type = signal_type in {SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY}

        if not entry_signal:
            filter_reasons.append(f"{RISK_CONTRACT_INVALID}: {RISK_MISSING_ENTRY_SIGNAL}")

        if not entry_signal_type:
            filter_reasons.append(f"{RISK_CONTRACT_INVALID}: {RISK_UNSUPPORTED_SIGNAL_TYPE}={signal_type}")

        if event_risk_flag:
            filter_reasons.append(RISK_EVENT)

        if not spread_ok:
            filter_reasons.append(RISK_SPREAD_TOO_WIDE)

        if not limit_ok:
            filter_reasons.append(RISK_TRADE_LIMIT_REACHED)

        if not _is_valid_positive_number(lot):
            filter_reasons.append(RISK_CONTRACT_INVALID)
            risk_explanations.append(RISK_INVALID_LOT)

        if not _is_valid_positive_number(stop_loss):
            filter_reasons.append(RISK_CONTRACT_INVALID)
            risk_explanations.append(RISK_INVALID_STOP_LOSS)

        if not _is_valid_positive_number(take_profit):
            filter_reasons.append(RISK_CONTRACT_INVALID)
            risk_explanations.append(RISK_INVALID_TAKE_PROFIT)

        trade_ok = not filter_reasons
        if trade_ok:
            filter_reason = RISK_ALL_FILTERS_PASSED_LEGACY
            success_tokens: list[str] = [RISK_FIXED_SL_TP, RISK_PLACEHOLDER_FIXED_LOT]
            if any(RISK_FIXED_SL_TP in reason for reason in reasons):
                success_tokens[0] = RISK_FIXED_SL_TP
            if any(RISK_PLACEHOLDER_FIXED_LOT in reason for reason in reasons):
                success_tokens[1] = RISK_PLACEHOLDER_FIXED_LOT
            risk_reason = " | ".join(success_tokens)
        else:
            filter_reason = " | ".join(dict.fromkeys(filter_reasons))
            risk_reason = " | ".join(dict.fromkeys(risk_explanations)) or RISK_CONTRACT_INVALID

        return RiskFilterResult(
            trade_ok=trade_ok,
            lot=float(lot) if trade_ok else None,
            stop_loss=float(stop_loss) if trade_ok else None,
            take_profit=float(take_profit) if trade_ok else None,
            risk_reason=risk_reason,
            filter_reason=filter_reason,
            event_risk_flag=event_risk_flag,
            spread_ok=spread_ok,
            limit_ok=limit_ok,
            max_trade_reached_flag=max_trade_reached_flag,
            sub_reasons=reasons,
        )
