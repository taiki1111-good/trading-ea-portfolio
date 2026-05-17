from pathlib import Path

from src.backtest.backtest_runner import BacktestRunner, EntryEvent
from src.backtest.types import BacktestConfig
from src.data.price_loader import PriceDataLoader
from src.evaluator.metrics_calculator import MetricsCalculator
from src.persistence.csv_log_reader import CsvLogReader
from src.persistence.csv_log_writer import CsvLogWriter
from src.persistence.csv_schema_validator import CsvSchemaValidator


FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
PRICE_FIXTURE = FIXTURE_DIR / "backtest_minimal_long_win.csv"


def test_backtest_to_logger_persistence_evaluator_roundtrip(tmp_path):
    price_frame = PriceDataLoader.load_from_csv(str(PRICE_FIXTURE), timeframe="H1")
    config = BacktestConfig(run_id="integration_backtest", max_holding_bars=10)

    def provider(i, window):
        _ = window
        if i == 0:
            return EntryEvent(
                entry_index=0,
                direction="long",
                lot=1.0,
                stop_loss=99.0,
                take_profit=101.0,
                entry_reason="integration_entry",
            )
        return None

    result = BacktestRunner.run(price_frame=price_frame, config=config, entry_event_provider=provider)
    assert result.trade_logs
    assert result.trade_logs[0]["entry_reason"] == "integration_entry"
    assert result.trade_logs[0]["signal_reason"] == ""
    assert result.trade_logs[0]["risk_reason"] == ""
    assert result.trade_logs[0]["filter_reason"] == ""

    path = tmp_path / "trade_logs.csv"
    write_result = CsvLogWriter.write(str(path), result.trade_logs, append=False)
    assert write_result.success
    assert write_result.record_count >= 1

    read_result = CsvLogReader.read(str(path))
    assert read_result.success
    assert read_result.record_count >= 1

    schema_result = CsvSchemaValidator.validate_records("trade_logs", read_result.data)
    assert schema_result.valid
    assert read_result.data[0]["entry_reason"] == "integration_entry"

    metrics_result = MetricsCalculator.calculate(read_result.data)
    assert metrics_result.trade_count >= 1
    assert metrics_result.average_pnl is not None
    assert metrics_result.evaluation_reason
