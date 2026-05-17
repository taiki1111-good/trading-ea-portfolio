from datetime import datetime, timezone

from src.execution import (
    ExecutionConfig,
    OrderBuilder,
    OrderSender,
    StateTransitionManager,
)
from src.logger import (
    DecisionLogger,
    EventLogger,
    LogAssembler,
    StateLogger,
    TradeLogger,
)
from src.signal.types import SIGNAL_LONG_ENTRY


def test_execution_to_logger_integration_creates_all_log_records():
    execution_config = ExecutionConfig(dry_run=True)
    order_creation = OrderBuilder.build(
        trade_ok=True,
        signal_type=SIGNAL_LONG_ENTRY,
        lot=0.1,
        stop_loss=99.0,
        take_profit=105.0,
        entry_price_candidate=100.0,
        execution_config=execution_config,
    )

    assert order_creation.order_request is not None
    assert order_creation.request_reason == "order request created successfully"

    order_send = OrderSender.send(order_creation.order_request, execution_config)
    assert order_send.order_result == "filled"

    submitted = StateTransitionManager.transition_by_event(
        previous_state="IDLE",
        event="entry_order_submitted",
    )
    transition = StateTransitionManager.transition_by_event(
        previous_state=submitted.next_state,
        event="entry_filled",
    )

    decision_log = DecisionLogger.log(
        htf_context_reason="HTF context approved",
        pattern_reason="pattern matched",
        signal_reason="entry signal generated",
        risk_reason="trade allowed",
        filter_reason="spread and slippage acceptable",
        execution_reason=order_send.execution_reason,
        structure_type="breakout",
        signal_type=SIGNAL_LONG_ENTRY,
    )
    trade_log = TradeLogger.log(
        order_result=order_send.order_result,
        lot=order_creation.order_request.lot,
        fill_price=order_creation.order_request.entry_price_candidate,
        execution_price=order_creation.order_request.entry_price_candidate,
        stop_loss=order_creation.order_request.stop_loss,
        take_profit=order_creation.order_request.take_profit,
        signal_type=SIGNAL_LONG_ENTRY,
        trade_ok=True,
        risk_reason="order passed risk checks",
        execution_reason=order_send.execution_reason,
    )
    state_log = StateLogger.log(
        previous_state=transition.previous_state,
        next_state=transition.next_state,
        position_state=transition.next_state,
        transition_reason=transition.transition_reason,
        order_result=order_send.order_result,
        execution_reason=order_send.execution_reason,
    )
    event_log = EventLogger.log(
        timestamp=datetime.now(timezone.utc),
        event_flag=True,
        event_type="breakout_event",
        event_risk_flag=False,
        filter_reason="event validated",
    )

    bundle = LogAssembler.assemble(
        decision_log=decision_log,
        trade_log=trade_log,
        state_log=state_log,
        event_log=event_log,
    )

    result = bundle.to_dict()
    assert result["decision_log"]["execution_reason"] == order_send.execution_reason
    assert result["trade_log"]["order_result"] == "filled"
    assert result["state_log"]["next_state"] == "POSITION_OPEN"
    assert result["event_log"]["event_type"] == "breakout_event"
    assert result["event_log"]["timestamp"] == event_log.timestamp.isoformat()
