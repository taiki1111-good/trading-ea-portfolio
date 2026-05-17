from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .types import EventLogRecord, _normalize_reason, utc_now


class EventLogger:
    @staticmethod
    def log(
        timestamp: Optional[datetime] = None,
        event_flag: bool = False,
        event_type: Optional[str] = None,
        event_risk_flag: bool = False,
        filter_reason: Optional[str] = None,
    ) -> EventLogRecord:
        normalized_timestamp = timestamp if timestamp is not None else utc_now()
        if normalized_timestamp.tzinfo is None:
            normalized_timestamp = normalized_timestamp.replace(tzinfo=timezone.utc)

        return EventLogRecord(
            log_time=utc_now(),
            timestamp=normalized_timestamp,
            event_flag=event_flag,
            event_type=_normalize_reason(event_type or "", "unknown"),
            event_risk_flag=event_risk_flag,
            filter_reason=_normalize_reason(filter_reason or "", "filter reason unavailable"),
        )
