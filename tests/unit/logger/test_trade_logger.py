from src.logger import TradeLogger


def test_trade_logger_records_execution_details():
    record = TradeLogger.log(
        order_result="filled",
        lot=0.25,
        fill_price=1234.5,
        execution_price=1235.0,
        stop_loss=1220.0,
        take_profit=1250.0,
        signal_type="short_entry",
        trade_ok=True,
        risk_reason="position size allowed",
        execution_reason="order accepted",
    )

    assert record.order_result == "filled"
    assert record.lot == 0.25
    assert record.fill_price == 1234.5
    assert record.execution_price == 1235.0
    assert record.trade_ok is True
    assert record.risk_reason == "position size allowed"
    assert record.to_dict()["signal_type"] == "short_entry"
