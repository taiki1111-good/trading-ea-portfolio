from datetime import datetime, timezone

from src.logger import EventLogger


def test_event_logger_records_market_event_without_state_details():
    event_timestamp = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    record = EventLogger.log(
        timestamp=event_timestamp,
        event_flag=True,
        event_type="trade_signal",
        event_risk_flag=True,
        filter_reason="event passed risk filter",
    )

    assert record.timestamp == event_timestamp
    assert record.log_time.tzinfo is not None
    assert record.event_flag is True
    assert record.event_type == "trade_signal"
    assert record.event_risk_flag is True
    assert record.filter_reason == "event passed risk filter"
    assert record.to_dict()["timestamp"] == event_timestamp.isoformat()
    assert "transition_reason" not in record.to_dict()
