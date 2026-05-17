from src.execution.state_transition_manager import StateTransitionManager
from src.execution.types import ExecutionConfig

ALLOWED_POSITION_STATES = {
    "IDLE",
    "ENTRY_PENDING",
    "POSITION_OPEN",
    "EXIT_PENDING",
    "SUSPENDED",
    "ERROR",
}

TRANSITION_CASES = [
    ("IDLE", "entry_order_submitted", "ENTRY_PENDING"),
    ("ENTRY_PENDING", "entry_filled", "POSITION_OPEN"),
    ("ENTRY_PENDING", "entry_rejected", "IDLE"),
    ("ENTRY_PENDING", "entry_cancelled", "IDLE"),
    ("ENTRY_PENDING", "entry_timeout", "IDLE"),
    ("POSITION_OPEN", "exit_order_submitted", "EXIT_PENDING"),
    ("EXIT_PENDING", "exit_filled", "IDLE"),
    ("EXIT_PENDING", "exit_rejected", "EXIT_PENDING"),
    ("EXIT_PENDING", "exit_cancelled", "EXIT_PENDING"),
    ("EXIT_PENDING", "exit_timeout", "ERROR"),
    ("IDLE", "suspend_requested", "SUSPENDED"),
    ("SUSPENDED", "suspend_released", "IDLE"),
    ("SUSPENDED", "entry_order_submitted", "SUSPENDED"),
    ("IDLE", "fatal_error_detected", "ERROR"),
    ("ENTRY_PENDING", "fatal_error_detected", "ERROR"),
    ("POSITION_OPEN", "fatal_error_detected", "ERROR"),
    ("EXIT_PENDING", "fatal_error_detected", "ERROR"),
    ("SUSPENDED", "fatal_error_detected", "ERROR"),
    ("ERROR", "safe_fallback_completed", "SUSPENDED"),
    ("ERROR", "entry_order_submitted", "ERROR"),
]


def test_transition_by_event_matches_docs_06_state_spec():
    for previous_state, event, expected_next_state in TRANSITION_CASES:
        result = StateTransitionManager.transition_by_event(
            previous_state=previous_state,
            event=event,
        )

        assert result.previous_state in ALLOWED_POSITION_STATES
        assert result.next_state == expected_next_state
        assert result.next_state in ALLOWED_POSITION_STATES
        assert isinstance(result.transition_reason, str)
        assert result.transition_reason.strip(), "transition_reason must not be empty"


def test_transition_by_event_transition_reason_is_descriptive():
    result = StateTransitionManager.transition_by_event(
        previous_state="ENTRY_PENDING",
        event="entry_timeout",
    )

    assert result.next_state == "IDLE"
    assert "entry_timeout" in result.transition_reason
    assert "ENTRY_PENDING" in result.transition_reason
    assert "IDLE" in result.transition_reason


def test_transition_compatibility_wrapper_preserves_initial_skeleton():
    result = StateTransitionManager.transition(
        previous_state="IDLE",
        trade_ok=True,
        order_result="filled",
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.previous_state == "IDLE"
    assert result.next_state == "POSITION_OPEN"
    assert isinstance(result.transition_reason, str)
    assert result.transition_reason.strip()
