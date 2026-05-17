from __future__ import annotations

from typing import Optional

from .types import DecisionLogRecord, utc_now, _normalize_reason


class DecisionLogger:
    @staticmethod
    def log(
        htf_context_reason: Optional[str] = None,
        pattern_reason: Optional[str] = None,
        signal_reason: Optional[str] = None,
        risk_reason: Optional[str] = None,
        filter_reason: Optional[str] = None,
        execution_reason: Optional[str] = None,
        structure_type: Optional[str] = None,
        signal_type: Optional[str] = None,
    ) -> DecisionLogRecord:
        return DecisionLogRecord(
            log_time=utc_now(),
            htf_context_reason=_normalize_reason(htf_context_reason or "", "htf context reason unavailable"),
            pattern_reason=_normalize_reason(pattern_reason or "", "pattern reason unavailable"),
            signal_reason=_normalize_reason(signal_reason or "", "signal reason unavailable"),
            risk_reason=_normalize_reason(risk_reason or "", "risk reason unavailable"),
            filter_reason=_normalize_reason(filter_reason or "", "filter reason unavailable"),
            execution_reason=_normalize_reason(execution_reason or "", "execution reason unavailable"),
            structure_type=_normalize_reason(structure_type or "", "unknown"),
            signal_type=_normalize_reason(signal_type or "", "none"),
        )
