from src.risk_filter.types import EventFilterConfig, EventFilterResult


class EventFilter:
    @staticmethod
    def check(event_flag: bool, event_type: str | None, event_filter_config: EventFilterConfig) -> EventFilterResult:
        if not event_filter_config.enabled:
            return EventFilterResult(
                event_risk_flag=False,
                event_filter_reason="event filter disabled",
            )

        if event_flag:
            reason = "event risk detected: event_flag=true"
            if event_type:
                reason = f"{reason} | event_type={event_type}"
            return EventFilterResult(event_risk_flag=True, event_filter_reason=reason)

        return EventFilterResult(event_risk_flag=False, event_filter_reason="no event risk detected")
