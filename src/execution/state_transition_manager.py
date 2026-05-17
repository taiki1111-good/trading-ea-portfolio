from __future__ import annotations

from src.execution.types import (
    ExecutionConfig,
    OrderResultType,
    PositionState,
    StateTransitionResult,
)


class StateTransitionManager:
    @staticmethod
    def transition_by_event(
        previous_state: PositionState,
        event: str,
    ) -> StateTransitionResult:
        if previous_state == "IDLE":
            if event == "entry_order_submitted":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="ENTRY_PENDING",
                    transition_reason="IDLE with entry_order_submitted -> ENTRY_PENDING",
                )
            if event == "suspend_requested":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="SUSPENDED",
                    transition_reason="IDLE with suspend_requested -> SUSPENDED",
                )
            if event == "fatal_error_detected":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="ERROR",
                    transition_reason="IDLE with fatal_error_detected -> ERROR",
                )
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="ERROR",
                transition_reason=f"IDLE with unsupported event={event} -> ERROR",
            )

        if previous_state == "ENTRY_PENDING":
            if event == "entry_filled":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="POSITION_OPEN",
                    transition_reason="ENTRY_PENDING with entry_filled -> POSITION_OPEN",
                )
            if event in {"entry_rejected", "entry_cancelled", "entry_timeout"}:
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="IDLE",
                    transition_reason=f"ENTRY_PENDING with {event} -> IDLE",
                )
            if event == "fatal_error_detected":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="ERROR",
                    transition_reason="ENTRY_PENDING with fatal_error_detected -> ERROR",
                )
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="ERROR",
                transition_reason=f"ENTRY_PENDING with unsupported event={event} -> ERROR",
            )

        if previous_state == "POSITION_OPEN":
            if event == "exit_order_submitted":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="EXIT_PENDING",
                    transition_reason="POSITION_OPEN with exit_order_submitted -> EXIT_PENDING",
                )
            if event == "fatal_error_detected":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="ERROR",
                    transition_reason="POSITION_OPEN with fatal_error_detected -> ERROR",
                )
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="ERROR",
                transition_reason=f"POSITION_OPEN with unsupported event={event} -> ERROR",
            )

        if previous_state == "EXIT_PENDING":
            if event == "exit_filled":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="IDLE",
                    transition_reason="EXIT_PENDING with exit_filled -> IDLE",
                )
            if event in {"exit_rejected", "exit_cancelled"}:
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="EXIT_PENDING",
                    transition_reason=f"EXIT_PENDING with {event} -> remain EXIT_PENDING",
                )
            if event == "exit_timeout":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="ERROR",
                    transition_reason="EXIT_PENDING with exit_timeout -> ERROR",
                )
            if event == "fatal_error_detected":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="ERROR",
                    transition_reason="EXIT_PENDING with fatal_error_detected -> ERROR",
                )
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="ERROR",
                transition_reason=f"EXIT_PENDING with unsupported event={event} -> ERROR",
            )

        if previous_state == "SUSPENDED":
            if event == "suspend_released":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="IDLE",
                    transition_reason="SUSPENDED with suspend_released -> IDLE",
                )
            if event == "fatal_error_detected":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="ERROR",
                    transition_reason="SUSPENDED with fatal_error_detected -> ERROR",
                )
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="SUSPENDED",
                transition_reason=f"SUSPENDED with unsupported event={event} -> remain SUSPENDED",
            )

        if previous_state == "ERROR":
            if event == "safe_fallback_completed":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="SUSPENDED",
                    transition_reason="ERROR with safe_fallback_completed -> SUSPENDED",
                )
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="ERROR",
                transition_reason=f"ERROR with event={event} -> remain ERROR",
            )

        return StateTransitionResult(
            previous_state=previous_state,
            next_state="ERROR",
            transition_reason=f"unsupported previous_state={previous_state} -> ERROR",
        )

    @staticmethod
    def transition(
        previous_state: PositionState,
        trade_ok: bool,
        order_result: OrderResultType,
        execution_config: ExecutionConfig,
    ) -> StateTransitionResult:
        # Backward-compatible wrapper for the initial skeleton call sites.
        if previous_state == "IDLE":
            if trade_ok and order_result == "filled":
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="POSITION_OPEN",
                    transition_reason=(
                        "IDLE with trade_ok=true and filled order -> POSITION_OPEN"
                    ),
                )

            if order_result in {"rejected", "cancelled", "failed"}:
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="IDLE",
                    transition_reason=(
                        f"IDLE with order_result={order_result} -> remain IDLE"
                    ),
                )

            if not trade_ok:
                return StateTransitionResult(
                    previous_state=previous_state,
                    next_state="IDLE",
                    transition_reason=(
                        "IDLE with trade_ok=false -> remain IDLE for safety"
                    ),
                )

            return StateTransitionResult(
                previous_state=previous_state,
                next_state="ERROR",
                transition_reason=(
                    "IDLE state encountered unexpected order_result and trade_ok combination"
                ),
            )

        if order_result in {"rejected", "cancelled", "failed"}:
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="IDLE",
                transition_reason=(
                    f"{previous_state} with order_result={order_result} -> IDLE for safety"
                ),
            )

        if previous_state == "SUSPENDED":
            return StateTransitionResult(
                previous_state=previous_state,
                next_state="SUSPENDED",
                transition_reason=(
                    "SUSPENDED state preserves suspension until explicit release"
                ),
            )

        return StateTransitionResult(
            previous_state=previous_state,
            next_state="ERROR",
            transition_reason=(
                "order result and previous state combination is unexpected for the initial execution skeleton"
            ),
        )
