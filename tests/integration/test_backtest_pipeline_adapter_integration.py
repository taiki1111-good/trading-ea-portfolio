from src.backtest.backtest_runner import BacktestRunner
from src.backtest.pipeline_adapter import PipelineAdapter, PipelineAdapterConfig
from src.backtest.types import BacktestConfig
from src.data.types import PriceBar
from src.persistence.csv_schema_validator import CsvSchemaValidator
from datetime import datetime, timedelta, timezone


def test_backtest_pipeline_adapter_integration_generates_trade_without_future_leak():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = [
        PriceBar(timestamp=t0, open=1.00, high=1.02, low=0.99, close=1.00, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=1.00, high=1.03, low=0.995, close=1.01, spread=0.2, volume=110.0),
        PriceBar(timestamp=t0 + timedelta(hours=2), open=1.01, high=1.05, low=1.00, close=1.04, spread=0.2, volume=120.0),
        PriceBar(timestamp=t0 + timedelta(hours=3), open=1.04, high=1.06, low=1.02, close=1.03, spread=0.2, volume=130.0),
    ]
    price_frame = bars
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            max_spread=1.0,
            fixed_lot=0.1,
            stop_loss_distance=0.01,
            take_profit_distance=0.02,
            min_distance=0.0001,
            trend_min_strength=0.0,
        )
    )

    config = BacktestConfig(run_id="integration_backtest_pipeline_adapter", max_holding_bars=10)

    def provider(i, window):
        assert len(window) == i + 1
        assert window[-1].timestamp == bars[i].timestamp
        return adapter(current_index=i, window=window)
    provider.get_last_decision_trace = adapter.get_last_decision_trace  # type: ignore[attr-defined]
    provider.reset_run_state = adapter.reset_run_state  # type: ignore[attr-defined]

    result = BacktestRunner.run(price_frame=price_frame, config=config, entry_event_provider=provider)

    assert result.trades
    assert result.trade_logs
    assert result.decision_logs
    assert result.summary is not None
    assert result.summary.trade_count >= 1
    first_trade_log = result.trade_logs[0]
    assert first_trade_log["entry_reason"].strip()
    assert first_trade_log["signal_reason"].strip()
    assert first_trade_log["risk_reason"].strip()
    assert first_trade_log["filter_reason"].strip()
    assert "fallback_used" in first_trade_log
    assert first_trade_log["structure_source"] in {"detector_chain", "detector_chain_temporal", "heuristic_fallback"}
    assert "recent_third_timestamp" in first_trade_log
    assert "recent_third_direction" in first_trade_log
    assert "temporal_lag_bars" in first_trade_log
    assert "temporal_lookback_bars" in first_trade_log
    assert "breakout_direction" in first_trade_log
    assert first_trade_log["entry_time"]
    assert first_trade_log["exit_time"]
    first_decision_log = result.decision_logs[0]
    assert first_decision_log["bar_index"] == 0
    assert first_decision_log["timestamp"]
    assert first_decision_log["fail_stage"]
    assert first_decision_log["decision_reason"]
    schema_result = CsvSchemaValidator.validate_records("decision_logs", result.decision_logs)
    assert schema_result.valid
    consistency_result = CsvSchemaValidator.validate_backtest_log_consistency(
        trade_logs=result.trade_logs,
        decision_logs=result.decision_logs,
    )
    assert consistency_result.valid


def test_backtest_pipeline_adapter_resets_recent_third_entry_state_per_run(monkeypatch):
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = [
        PriceBar(timestamp=t0, open=1.00, high=1.02, low=0.99, close=1.00, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=1.00, high=1.03, low=0.995, close=1.01, spread=0.2, volume=110.0),
        PriceBar(timestamp=t0 + timedelta(hours=2), open=1.01, high=1.05, low=1.00, close=1.04, spread=0.2, volume=120.0),
        PriceBar(timestamp=t0 + timedelta(hours=3), open=1.04, high=1.06, low=1.02, close=1.03, spread=0.2, volume=130.0),
    ]
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=False,
            max_entries_per_recent_third_candidate=1,
            max_spread=1.0,
            trend_min_strength=0.0,
            min_distance=0.0001,
        )
    )
    fixed_ts = bars[2].timestamp.isoformat()

    def fake_build_structure(_window, _context_reason):
        from src.ltf_structure.types import STRUCTURE_THIRD_WAVE_BREAK, StructureResult

        structure = StructureResult(
            structure_type=STRUCTURE_THIRD_WAVE_BREAK,
            structure_direction="long",
            structure_candidate=True,
            pattern_reason="temporal third_wave_break candidate confirmed",
            sub_reasons=["fake"],
        )
        return structure, "third", True, False, "detector_chain_temporal", {"recent_third_timestamp": fixed_ts}

    monkeypatch.setattr(adapter, "_build_structure", fake_build_structure)

    config1 = BacktestConfig(run_id="integration_run_1", max_holding_bars=1)
    result1 = BacktestRunner.run(price_frame=bars, config=config1, entry_event_provider=adapter)
    assert result1.summary is not None
    assert result1.summary.trade_count >= 1

    config2 = BacktestConfig(run_id="integration_run_2", max_holding_bars=1)
    result2 = BacktestRunner.run(price_frame=bars, config=config2, entry_event_provider=adapter)
    assert result2.summary is not None
    assert result2.summary.trade_count >= 1


def test_backtest_pipeline_adapter_trade_ok_true_matches_trade_count():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = [
        PriceBar(timestamp=t0, open=1.00, high=1.02, low=0.99, close=1.00, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=1.00, high=1.03, low=0.995, close=1.01, spread=0.2, volume=110.0),
        PriceBar(timestamp=t0 + timedelta(hours=2), open=1.01, high=1.05, low=1.00, close=1.04, spread=0.2, volume=120.0),
        PriceBar(timestamp=t0 + timedelta(hours=3), open=1.04, high=1.06, low=1.02, close=1.03, spread=0.2, volume=130.0),
    ]
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            max_spread=1.0,
            fixed_lot=0.1,
            stop_loss_distance=0.01,
            take_profit_distance=0.02,
            min_distance=0.0001,
            trend_min_strength=0.0,
        )
    )
    config = BacktestConfig(run_id="integration_trade_ok_match", max_holding_bars=2)
    result = BacktestRunner.run(price_frame=bars, config=config, entry_event_provider=adapter)
    assert result.summary is not None
    trade_ok_true_count = sum(1 for row in result.decision_logs if row.get("trade_ok") is True)
    assert trade_ok_true_count == result.summary.trade_count
