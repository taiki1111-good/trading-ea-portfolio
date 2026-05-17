from datetime import datetime, timezone

from src.logger import DecisionLogger, EventLogger, LogAssembler, StateLogger, TradeLogger


def test_log_assembler_builds_bundle():
    decision = DecisionLogger.log(
        htf_context_reason="HTF context matched",
        pattern_reason="pattern accepted",
        signal_reason="signal emitted",
        risk_reason="risk approved",
        filter_reason="spread acceptable",
        execution_reason="execution scheduled",
        structure_type="breakout",
        signal_type="long_entry",
    )
    trade = TradeLogger.log(
        order_result="filled",
        lot=0.1,
        fill_price=101.0,
        execution_price=101.2,
        stop_loss=99.0,
        take_profit=105.0,
        signal_type="long_entry",
        trade_ok=True,
        risk_reason="size justified",
        execution_reason="accepted",
    )
    state = StateLogger.log(
        previous_state="ENTRY_PENDING",
        next_state="POSITION_OPEN",
        position_state="POSITION_OPEN",
        transition_reason="filled and opened",
        order_result="filled",
        execution_reason="accepted",
    )
    event = EventLogger.log(
        timestamp=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        event_flag=True,
        event_type="breakout",
        event_risk_flag=False,
        filter_reason="passed filters",
    )

    bundle = LogAssembler.assemble(
        decision_log=decision,
        trade_log=trade,
        state_log=state,
        event_log=event,
    )

    result = bundle.to_dict()
    assert result["decision_log"]["signal_type"] == "long_entry"
    assert result["trade_log"]["lot"] == 0.1
    assert result["state_log"]["next_state"] == "POSITION_OPEN"
    assert result["event_log"]["event_type"] == "breakout"
