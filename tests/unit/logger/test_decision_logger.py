from datetime import timezone

from src.logger import DecisionLogger


def test_decision_logger_creates_timezone_aware_record():
    record = DecisionLogger.log(
        htf_context_reason="HTF context matched",
        pattern_reason="pattern accepted",
        signal_reason="signal emitted",
        risk_reason="risk approved",
        filter_reason="spread acceptable",
        execution_reason="execution scheduled",
        structure_type="breakout",
        signal_type="long_entry",
    )

    assert record.log_time.tzinfo is not None
    assert record.log_time.utcoffset() == timezone.utc.utcoffset(record.log_time)
    assert record.structure_type == "breakout"
    assert record.signal_type == "long_entry"
    assert record.execution_reason == "execution scheduled"
    assert isinstance(record.to_dict()["log_time"], str)
