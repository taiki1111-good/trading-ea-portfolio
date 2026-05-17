from src.execution.fill_handler import FillHandler
from src.execution.order_builder import OrderBuilder
from src.execution.order_sender import OrderSender
from src.execution.state_transition_manager import StateTransitionManager
from src.execution.types import ExecutionConfig
from src.risk_filter.assembler import RiskAssembler


def _build_valid_risk_result(signal_type: str):
    return RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type=signal_type,
        signal_reason="signal valid",
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        sub_reasons=["valid risk"],
    )


def test_risk_filter_to_execution_long_entry_dry_run_filled():
    signal_type = "long_entry"
    risk_result = _build_valid_risk_result(signal_type)
    order_request_result = OrderBuilder.build(
        trade_ok=risk_result.trade_ok,
        signal_type=signal_type,
        lot=risk_result.lot,
        stop_loss=risk_result.stop_loss,
        take_profit=risk_result.take_profit,
        entry_price_candidate=1.1,
        execution_config=ExecutionConfig(dry_run=True),
    )
    order_send_result = OrderSender.send(order_request_result.order_request, ExecutionConfig(dry_run=True))
    fill_result = FillHandler.process(order_send_result.order_result, order_request_result.order_request, order_send_result.broker_response_raw)
    submitted = StateTransitionManager.transition_by_event(
        previous_state="IDLE",
        event="entry_order_submitted",
    )
    transition = StateTransitionManager.transition_by_event(
        previous_state=submitted.next_state,
        event="entry_filled",
    )

    assert order_request_result.order_request is not None
    assert order_send_result.order_result == "filled"
    assert fill_result.fill_price == 1.1
    assert transition.next_state == "POSITION_OPEN"
    assert order_send_result.execution_reason
    assert transition.transition_reason


def test_risk_filter_to_execution_short_entry_dry_run_filled():
    signal_type = "short_entry"
    risk_result = _build_valid_risk_result(signal_type)
    order_request_result = OrderBuilder.build(
        trade_ok=risk_result.trade_ok,
        signal_type=signal_type,
        lot=risk_result.lot,
        stop_loss=risk_result.stop_loss,
        take_profit=risk_result.take_profit,
        entry_price_candidate=1.1,
        execution_config=ExecutionConfig(dry_run=True),
    )
    order_send_result = OrderSender.send(order_request_result.order_request, ExecutionConfig(dry_run=True))
    fill_result = FillHandler.process(order_send_result.order_result, order_request_result.order_request, order_send_result.broker_response_raw)
    submitted = StateTransitionManager.transition_by_event(
        previous_state="IDLE",
        event="entry_order_submitted",
    )
    transition = StateTransitionManager.transition_by_event(
        previous_state=submitted.next_state,
        event="entry_filled",
    )

    assert order_request_result.order_request is not None
    assert order_send_result.order_result == "filled"
    assert fill_result.fill_price == 1.1
    assert transition.next_state == "POSITION_OPEN"


def test_risk_filter_to_execution_trade_not_ok_safely_no_order():
    signal_type = "long_entry"
    risk_result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type=signal_type,
        signal_reason="signal valid",
        event_risk_flag=True,
        spread_ok=False,
        limit_ok=False,
        max_trade_reached_flag=False,
        lot=None,
        stop_loss=None,
        take_profit=None,
        sub_reasons=["risk blocked"],
    )
    order_request_result = OrderBuilder.build(
        trade_ok=risk_result.trade_ok,
        signal_type=signal_type,
        lot=risk_result.lot,
        stop_loss=risk_result.stop_loss,
        take_profit=risk_result.take_profit,
        entry_price_candidate=1.1,
        execution_config=ExecutionConfig(dry_run=True),
    )
    order_send_result = OrderSender.send(order_request_result.order_request, ExecutionConfig(dry_run=True))
    transition = StateTransitionManager.transition_by_event(
        previous_state="IDLE",
        event="suspend_requested",
    )

    assert order_request_result.order_request is None
    assert order_send_result.order_result == "none"
    assert transition.next_state == "SUSPENDED"


def test_risk_filter_to_execution_dry_run_false_returns_failed():
    signal_type = "long_entry"
    risk_result = _build_valid_risk_result(signal_type)
    order_request_result = OrderBuilder.build(
        trade_ok=risk_result.trade_ok,
        signal_type=signal_type,
        lot=risk_result.lot,
        stop_loss=risk_result.stop_loss,
        take_profit=risk_result.take_profit,
        entry_price_candidate=1.1,
        execution_config=ExecutionConfig(dry_run=False),
    )
    order_send_result = OrderSender.send(order_request_result.order_request, ExecutionConfig(dry_run=False))
    submitted = StateTransitionManager.transition_by_event(
        previous_state="IDLE",
        event="entry_order_submitted",
    )
    transition = StateTransitionManager.transition_by_event(
        previous_state=submitted.next_state,
        event="entry_rejected",
    )

    assert order_send_result.order_result == "failed"
    assert "not implemented" in order_send_result.execution_reason
    assert transition.next_state == "IDLE"
    assert transition.transition_reason
