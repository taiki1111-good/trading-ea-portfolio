from src.logger import StateLogger


def test_state_logger_records_transition_only():
    record = StateLogger.log(
        previous_state="IDLE",
        next_state="ENTRY_PENDING",
        position_state="ENTRY_PENDING",
        transition_reason="order queued",
        order_result="filled",
        execution_reason="filled by exchange",
    )

    assert record.previous_state == "IDLE"
    assert record.next_state == "ENTRY_PENDING"
    assert record.position_state == "ENTRY_PENDING"
    assert record.transition_reason == "order queued"
    assert record.order_result == "filled"
    assert record.execution_reason == "filled by exchange"
    assert "event_flag" not in record.to_dict()
