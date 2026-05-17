from src.logger.trade_logger import TradeLogger
from src.persistence.csv_log_writer import CsvLogWriter


def test_csv_log_writer_creates_csv(tmp_path):
    path = tmp_path / "logs.csv"
    trade_log = TradeLogger.log(
        order_result="filled",
        lot=0.1,
        fill_price=1.1,
        execution_price=1.1,
        stop_loss=1.09,
        take_profit=1.11,
        signal_type="long_entry",
        trade_ok=True,
        risk_reason="risk ok",
        execution_reason="exec ok",
        pnl=10.0,
    )

    result = CsvLogWriter.write(str(path), [trade_log], append=False)

    assert result.success
    assert result.record_count == 1
    assert result.persistence_reason

    text = path.read_text(encoding="utf-8")
    assert "order_result" in text
    assert "filled" in text


def test_csv_log_writer_appends_csv(tmp_path):
    path = tmp_path / "logs.csv"
    trade_log = TradeLogger.log(order_result="filled")
    CsvLogWriter.write(str(path), [trade_log], append=False)
    second_log = TradeLogger.log(order_result="rejected")

    result = CsvLogWriter.write(str(path), [second_log], append=True)

    assert result.success
    assert result.record_count == 1
    assert result.persistence_reason

    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 3
    assert "rejected" in lines[-1]


def test_csv_log_writer_overwrites_csv_when_append_false(tmp_path):
    path = tmp_path / "logs.csv"
    first_log = TradeLogger.log(order_result="filled")
    CsvLogWriter.write(str(path), [first_log], append=False)
    second_log = TradeLogger.log(order_result="cancelled")

    CsvLogWriter.write(str(path), [second_log], append=False)

    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    assert "cancelled" in lines[-1]
