from src.logger.trade_logger import TradeLogger
from src.persistence.csv_log_reader import CsvLogReader
from src.persistence.csv_log_writer import CsvLogWriter


def test_csv_log_reader_reads_csv(tmp_path):
    path = tmp_path / "logs.csv"
    trade_log = TradeLogger.log(order_result="filled", pnl=10.0)
    CsvLogWriter.write(str(path), [trade_log], append=False)

    result = CsvLogReader.read(str(path))

    assert result.success
    assert result.record_count == 1
    assert result.persistence_reason
    assert result.data[0]["order_result"] == "filled"
    assert result.data[0]["pnl"] == 10.0


def test_csv_log_reader_reports_missing_file(tmp_path):
    path = tmp_path / "missing.csv"

    result = CsvLogReader.read(str(path))

    assert not result.success
    assert result.record_count == 0
    assert result.warnings
    assert result.persistence_reason
