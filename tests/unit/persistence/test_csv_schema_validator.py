from src.persistence.csv_schema_validator import CsvSchemaValidator


def test_csv_schema_validator_valid_trade_logs_schema():
    records = [
        {
            "log_time": "2026-05-01T00:00:00+00:00",
            "order_result": "filled",
            "lot": 0.1,
            "fill_price": 1.1,
            "execution_price": 1.1,
            "stop_loss": 1.09,
            "take_profit": 1.11,
            "entry_time": "2026-05-01T00:00:00+00:00",
            "exit_time": "2026-05-01T01:00:00+00:00",
            "signal_type": "long_entry",
            "pnl": 0.001,
            "realized_pnl": 0.001,
            "exit_reason": "take_profit",
            "entry_reason": "ok",
            "signal_reason": "ok",
            "risk_reason": "ok",
            "filter_reason": "ok",
            "fallback_used": False,
            "structure_source": "detector_chain_temporal",
            "recent_third_timestamp": "2026-05-01T00:00:00+00:00",
            "recent_third_direction": "long",
            "temporal_lag_bars": 2,
            "temporal_lookback_bars": 5,
            "breakout_direction": "long",
        }
    ]

    result = CsvSchemaValidator.validate_records("trade_logs", records)

    assert result.valid
    assert result.schema_name == "trade_logs"
    assert result.missing_columns == []
    assert result.validation_reason
    assert result.warnings == []


def test_csv_schema_validator_trade_logs_unknown_extra_column_warns():
    records = [
        {
            "log_time": "2026-05-01T00:00:00+00:00",
            "order_result": "filled",
            "lot": 0.1,
            "fill_price": 1.1,
            "execution_price": 1.1,
            "stop_loss": 1.09,
            "take_profit": 1.11,
            "unexpected_col": "x",
        }
    ]
    result = CsvSchemaValidator.validate_records("trade_logs", records)
    assert result.valid
    assert result.warnings
    assert "unknown extra columns" in result.warnings[0]


def test_csv_schema_validator_trade_logs_experimental_columns_are_known():
    records = [
        {
            "log_time": "2026-05-01T00:00:00+00:00",
            "order_result": "filled",
            "lot": 0.1,
            "fill_price": 1.1,
            "execution_price": 1.1,
            "stop_loss": 1.09,
            "take_profit": 1.11,
            "entry_time_mode": "m5_close",
            "exit_policy": "fixed_sl_tp",
            "holding_bars": 3,
            "trailing_activation_R": 1.0,
        }
    ]
    result = CsvSchemaValidator.validate_records("trade_logs", records)
    assert result.valid
    assert not any("unknown extra columns" in w for w in result.warnings)


def test_csv_schema_validator_returns_missing_columns_when_invalid():
    records = [
        {
            "log_time": "2026-05-01T00:00:00+00:00",
            "order_result": "filled",
            "lot": 0.1,
            "fill_price": 1.1,
            "execution_price": 1.1,
        }
    ]

    result = CsvSchemaValidator.validate_records("trade_logs", records)

    assert not result.valid
    assert "stop_loss" in result.missing_columns
    assert "take_profit" in result.missing_columns
    assert result.validation_reason


def test_csv_schema_validator_warns_on_invalid_position_state_enum():
    records = [
        {
            "log_time": "2026-05-01T00:00:00+00:00",
            "previous_state": "IDLE",
            "next_state": "ERROR",
            "position_state": "BROKEN",
            "transition_reason": "invalid enum test",
            "order_result": "filled",
            "execution_reason": "test",
        }
    ]

    result = CsvSchemaValidator.validate_records("state_logs", records)

    assert result.valid
    assert result.warnings
    assert "position_state" in result.warnings[0]


def _valid_decision_row() -> dict[str, object]:
    return {
        "log_time": "2026-05-01T00:00:00+00:00",
        "bar_index": 10,
        "timestamp": "2026-05-01T00:00:00+00:00",
        "close": 150.0,
        "htf_bias": "long",
        "wave_phase": "third",
        "wave_direction": "long",
        "breakout_flag": True,
        "breakout_direction": "long",
        "structure_candidate": True,
        "structure_source": "detector_chain_temporal",
        "temporal_candidate": True,
        "recent_third_timestamp": "2026-05-01T00:00:00+00:00",
        "recent_third_direction": "long",
        "temporal_lag_bars": 2,
        "temporal_lookback_bars": 5,
        "direction_aligned": True,
        "pattern_allowed": True,
        "entry_signal": True,
        "trade_ok": True,
        "fail_stage": "none",
        "decision_reason": "ok",
    }


def test_csv_schema_validator_valid_decision_logs_schema():
    result = CsvSchemaValidator.validate_records("decision_logs", [_valid_decision_row()])
    assert result.valid


def test_csv_schema_validator_decision_logs_htf_v1_columns_are_known():
    row = _valid_decision_row()
    row.update(
        {
            "htf_filter_enabled": True,
            "htf_timeframe_policy": "H1_only",
            "htf_neutral_policy": "permissive",
            "htf_trend_dir": "up",
            "htf_direction_aligned": True,
            "htf_filter_reason": "ok",
            "htf_context_reason": "ctx",
        }
    )
    result = CsvSchemaValidator.validate_records("decision_logs", [row])
    assert result.valid
    assert not any("unknown extra columns" in w for w in result.warnings)


def test_csv_schema_validator_decision_logs_still_warns_for_unknown_extra_column():
    row = _valid_decision_row()
    row["unknown_col"] = "x"
    result = CsvSchemaValidator.validate_records("decision_logs", [row])
    assert result.valid
    assert any("unknown extra columns" in w for w in result.warnings)


def test_csv_schema_validator_decision_logs_missing_required_column_is_invalid():
    row = _valid_decision_row()
    row.pop("decision_reason")
    result = CsvSchemaValidator.validate_records("decision_logs", [row])
    assert not result.valid
    assert "decision_reason" in result.missing_columns


def test_csv_schema_validator_decision_logs_invalid_fail_stage_is_invalid():
    row = _valid_decision_row()
    row["fail_stage"] = "bad_stage"
    result = CsvSchemaValidator.validate_records("decision_logs", [row])
    assert not result.valid
    assert any("fail_stage" in w for w in result.warnings)


def test_csv_schema_validator_temporal_true_requires_recent_third_timestamp():
    row = _valid_decision_row()
    row["recent_third_timestamp"] = ""
    result = CsvSchemaValidator.validate_records("decision_logs", [row])
    assert not result.valid
    assert any("temporal_candidate=true" in w for w in result.warnings)


def test_csv_schema_validator_temporal_false_requires_empty_recent_third_timestamp():
    row = _valid_decision_row()
    row["temporal_candidate"] = False
    row["recent_third_timestamp"] = "2026-05-01T00:00:00+00:00"
    row["recent_third_direction"] = "long"
    row["temporal_lag_bars"] = 1
    row["temporal_lookback_bars"] = 5
    result = CsvSchemaValidator.validate_records("decision_logs", [row])
    assert not result.valid
    assert any("temporal_candidate=false" in w for w in result.warnings)


def test_validate_backtest_log_consistency_invalid_when_trade_ok_count_mismatch():
    trade_logs = [{"structure_source": "detector_chain_temporal", "fallback_used": False}]
    decisions = [{**_valid_decision_row(), "trade_ok": False}]
    result = CsvSchemaValidator.validate_backtest_log_consistency(trade_logs, decisions)
    assert not result.valid
    assert "does not match" in result.consistency_reason


def test_validate_backtest_log_consistency_invalid_when_heuristic_fallback_mixed_in_fallback_off_run():
    trade_logs = [{"structure_source": "detector_chain_temporal", "fallback_used": False}]
    decision = _valid_decision_row()
    decision["structure_source"] = "heuristic_fallback"
    result = CsvSchemaValidator.validate_backtest_log_consistency(trade_logs, [decision])
    assert not result.valid
    assert "heuristic_fallback" in result.consistency_reason


def test_validate_backtest_log_consistency_valid_with_matching_trade_ok_count():
    trade_logs = [{"structure_source": "detector_chain_temporal", "fallback_used": False}]
    decisions = [_valid_decision_row()]
    result = CsvSchemaValidator.validate_backtest_log_consistency(trade_logs, decisions)
    assert result.valid


def test_csv_schema_validator_trade_logs_invalid_structure_source():
    records = [
        {
            "log_time": "2026-05-01T00:00:00+00:00",
            "order_result": "filled",
            "lot": 0.1,
            "fill_price": 1.1,
            "execution_price": 1.1,
            "stop_loss": 1.09,
            "take_profit": 1.11,
            "signal_type": "long_entry",
            "structure_source": "unknown_source",
            "fallback_used": False,
        }
    ]
    result = CsvSchemaValidator.validate_records("trade_logs", records)
    assert not result.valid
    assert any("structure_source" in w for w in result.warnings)
