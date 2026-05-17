from datetime import datetime, timezone

from src.evaluator import FilterAnalyzer, MetricsCalculator, StructureAnalyzer
from src.logger import DecisionLogger, EventLogger, LogAssembler, StateLogger, TradeLogger
from src.persistence.csv_log_reader import CsvLogReader
from src.persistence.csv_schema_validator import CsvSchemaValidator
from src.persistence.csv_log_writer import CsvLogWriter
from src.persistence.jsonl_log_reader import JsonlLogReader
from src.persistence.jsonl_log_writer import JsonlLogWriter


def test_logger_to_persistence_to_evaluator_roundtrip(tmp_path):
    decision_log = DecisionLogger.log(
        htf_context_reason="htf reason",
        pattern_reason="pattern reason",
        signal_reason="signal reason",
        risk_reason="risk reason",
        filter_reason="filter reason",
        execution_reason="execution reason",
        structure_type="third_wave_break",
        signal_type="long_entry",
    )

    trade_log = TradeLogger.log(
        order_result="filled",
        lot=0.1,
        fill_price=1.1000,
        execution_price=1.1000,
        stop_loss=1.0900,
        take_profit=1.1100,
        signal_type="long_entry",
        trade_ok=True,
        risk_reason="risk reason",
        execution_reason="execution reason",
        pnl=10.0,
        realized_pnl=10.0,
    )

    state_log = StateLogger.log(
        previous_state="IDLE",
        next_state="ENTRY_PENDING",
        position_state="ENTRY_PENDING",
        transition_reason="IDLE -> ENTRY_PENDING",
        order_result="filled",
        execution_reason="execution reason",
    )

    event_log = EventLogger.log(
        timestamp=datetime.now(timezone.utc),
        event_flag=True,
        event_type="price_signal",
        event_risk_flag=False,
        filter_reason="filter reason",
    )

    bundle = LogAssembler.assemble(
        decision_log=decision_log,
        trade_log=trade_log,
        state_log=state_log,
        event_log=event_log,
    )

    path = tmp_path / "logger_bundle.jsonl"
    write_result = JsonlLogWriter.write(str(path), [bundle], append=False)

    assert write_result.success
    assert write_result.record_count == 1
    assert write_result.persistence_reason

    read_result = JsonlLogReader.read(str(path), skip_invalid=False)

    assert read_result.success
    assert read_result.record_count == 1
    assert read_result.persistence_reason
    assert len(read_result.data) == 1

    bundle_dict = read_result.data[0]
    trade_dict = bundle_dict["trade_log"]
    event_dict = bundle_dict["event_log"]
    decision_dict = bundle_dict["decision_log"]

    metrics_result = MetricsCalculator.calculate([trade_dict])
    filter_stats, filter_warnings = FilterAnalyzer.analyze([event_dict])
    structure_stats, structure_warnings = StructureAnalyzer.analyze([decision_dict])

    assert metrics_result.trade_count == 1
    assert metrics_result.average_pnl == 10.0
    assert filter_stats["filter reason"].count == 1
    assert structure_stats["third_wave_break"].count == 1
    assert not filter_warnings
    assert not structure_warnings


def test_logger_to_csv_persistence_to_evaluator_roundtrip(tmp_path):
    trade_log = TradeLogger.log(
        order_result="filled",
        lot=0.1,
        fill_price=1.1000,
        execution_price=1.1000,
        stop_loss=1.0900,
        take_profit=1.1100,
        signal_type="long_entry",
        trade_ok=True,
        risk_reason="risk reason",
        execution_reason="execution reason",
        pnl=10.0,
        realized_pnl=10.0,
    )

    path = tmp_path / "logger_trade.csv"
    write_result = CsvLogWriter.write(str(path), [trade_log], append=False)

    assert write_result.success
    assert write_result.record_count == 1
    assert write_result.persistence_reason

    read_result = CsvLogReader.read(str(path))

    assert read_result.success
    assert read_result.record_count == 1
    assert read_result.persistence_reason
    assert read_result.data[0]["order_result"] == "filled"
    assert read_result.data[0]["pnl"] == 10.0

    schema_result = CsvSchemaValidator.validate_records("trade_logs", read_result.data)
    assert schema_result.valid
    assert schema_result.validation_reason

    metrics_result = MetricsCalculator.calculate([read_result.data[0]])

    assert metrics_result.trade_count == 1
    assert metrics_result.average_pnl == 10.0
    assert metrics_result.evaluation_reason


def test_csv_schema_validation_returns_missing_columns_for_invalid_trade_logs():
    invalid_records = [
        {
            "log_time": "2026-05-01T00:00:00+00:00",
            "order_result": "filled",
            "lot": 0.1,
            "fill_price": 1.1,
            "execution_price": 1.1,
        }
    ]

    schema_result = CsvSchemaValidator.validate_records("trade_logs", invalid_records)

    assert not schema_result.valid
    assert "stop_loss" in schema_result.missing_columns
    assert "take_profit" in schema_result.missing_columns
    assert schema_result.validation_reason
