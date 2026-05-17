from src.risk_filter.event_filter import EventFilter
from src.risk_filter.types import EventFilterConfig


def test_event_filter_sets_true_when_flag_true():
    result = EventFilter.check(True, "cpi", EventFilterConfig())

    assert result.event_risk_flag is True
    assert "event risk detected" in result.event_filter_reason


def test_event_filter_sets_false_when_flag_false():
    result = EventFilter.check(False, "cpi", EventFilterConfig())

    assert result.event_risk_flag is False
    assert result.event_filter_reason == "no event risk detected"
