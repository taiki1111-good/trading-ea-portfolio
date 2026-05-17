from src.execution.state_transition_manager import StateTransitionManager
from src.execution.types import ExecutionConfig


def test_state_transition_manager_moves_idle_to_position_open_on_filled():
    result = StateTransitionManager.transition(
        previous_state="IDLE",
        trade_ok=True,
        order_result="filled",
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.next_state == "POSITION_OPEN"
    assert "POSITION_OPEN" in result.transition_reason


def test_state_transition_manager_moves_to_idle_on_rejected():
    result = StateTransitionManager.transition(
        previous_state="ENTRY_PENDING",
        trade_ok=True,
        order_result="rejected",
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.next_state == "IDLE"
    assert "rejected" in result.transition_reason


def test_state_transition_manager_moves_to_error_on_unexpected_combination():
    result = StateTransitionManager.transition(
        previous_state="POSITION_OPEN",
        trade_ok=True,
        order_result="none",
        execution_config=ExecutionConfig(dry_run=True),
    )

    assert result.next_state == "ERROR"
    assert "unexpected" in result.transition_reason


def test_state_transition_manager_event_driven_idle_to_entry_pending():
    result = StateTransitionManager.transition_by_event(
        previous_state="IDLE",
        event="entry_order_submitted",
    )

    assert result.next_state == "ENTRY_PENDING"
    assert "ENTRY_PENDING" in result.transition_reason


def test_state_transition_manager_event_driven_entry_pending_to_position_open():
    result = StateTransitionManager.transition_by_event(
        previous_state="ENTRY_PENDING",
        event="entry_filled",
    )

    assert result.next_state == "POSITION_OPEN"
    assert "POSITION_OPEN" in result.transition_reason


def test_state_transition_manager_event_driven_error_to_suspended():
    result = StateTransitionManager.transition_by_event(
        previous_state="ERROR",
        event="safe_fallback_completed",
    )

    assert result.next_state == "SUSPENDED"
    assert "SUSPENDED" in result.transition_reason
