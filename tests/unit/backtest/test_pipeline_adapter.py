from datetime import datetime, timedelta, timezone

import pytest

from src.backtest.pipeline_adapter import PipelineAdapter, PipelineAdapterConfig
from src.htf_context.types import HTFContextResult, TrendResult
from src.ltf_structure.types import STRUCTURE_THIRD_WAVE_BREAK, StructureResult
from src.data.types import PriceBar


def _make_bars_for_long_breakout() -> list[PriceBar]:
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        PriceBar(timestamp=t0, open=1.00, high=1.02, low=0.99, close=1.00, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=1.00, high=1.03, low=0.995, close=1.01, spread=0.2, volume=110.0),
        PriceBar(timestamp=t0 + timedelta(hours=2), open=1.01, high=1.05, low=1.00, close=1.04, spread=0.2, volume=120.0),
    ]


def _make_bars_for_short_breakout() -> list[PriceBar]:
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        PriceBar(timestamp=t0, open=1.10, high=1.11, low=1.08, close=1.10, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=1.10, high=1.105, low=1.07, close=1.09, spread=0.2, volume=110.0),
        PriceBar(timestamp=t0 + timedelta(hours=2), open=1.09, high=1.095, low=1.05, close=1.06, spread=0.2, volume=120.0),
    ]


def _make_bars_for_temporal_long_breakout() -> list[PriceBar]:
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        PriceBar(timestamp=t0, open=0.95, high=1.00, low=0.90, close=0.95, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=0.95, high=0.98, low=0.85, close=0.90, spread=0.2, volume=110.0),
        PriceBar(timestamp=t0 + timedelta(hours=2), open=0.90, high=1.10, low=0.90, close=1.00, spread=0.2, volume=120.0),
        PriceBar(timestamp=t0 + timedelta(hours=3), open=1.00, high=1.05, low=0.88, close=1.00, spread=0.2, volume=130.0),
        PriceBar(timestamp=t0 + timedelta(hours=4), open=1.00, high=1.13, low=0.89, close=1.11, spread=0.2, volume=140.0),
    ]


def test_pipeline_adapter_returns_none_when_trade_not_ok():
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            max_spread=0.1,  # lower than bar spread -> spread filter fail
            fixed_lot=0.1,
            stop_loss_distance=0.01,
            take_profit_distance=0.02,
            min_distance=0.0001,
            trend_min_strength=0.0,
        )
    )

    entry_event = adapter(current_index=2, window=bars[:3])
    assert entry_event is None
    trace = adapter.get_last_decision_trace()
    assert trace
    assert trace.get("fail_stage") == "risk_filter"
    assert trace.get("trade_ok") is False


def test_pipeline_adapter_returns_none_when_placeholder_account_balance_invalid():
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            max_spread=1.0,
            fixed_lot=0.1,
            placeholder_account_balance=0.0,
            stop_loss_distance=0.01,
            take_profit_distance=0.02,
            min_distance=0.0001,
            trend_min_strength=0.0,
        )
    )

    entry_event = adapter(current_index=2, window=bars[:3])
    assert entry_event is None
    trace = adapter.get_last_decision_trace()
    assert trace
    assert trace.get("fail_stage") == "risk_filter"
    assert trace.get("trade_ok") is False


def test_pipeline_adapter_returns_entry_event_for_long_and_uses_risk_outputs():
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            max_spread=1.0,
            fixed_lot=0.2,
            stop_loss_distance=0.01,
            take_profit_distance=0.02,
            min_distance=0.0001,
            trend_min_strength=0.0,
        )
    )

    entry_event = adapter(current_index=2, window=bars[:3])
    assert entry_event is not None
    assert entry_event.direction == "long"
    assert entry_event.lot == 0.2
    assert entry_event.stop_loss == pytest.approx(bars[2].close - 0.01)
    assert entry_event.take_profit == pytest.approx(bars[2].close + 0.02)
    assert entry_event.entry_reason.strip()
    assert "all risk filters passed" in entry_event.entry_reason
    assert "fixed_sl_tp" in entry_event.entry_reason
    assert "placeholder_fixed_lot" in entry_event.entry_reason
    assert entry_event.signal_reason.strip()
    assert entry_event.risk_reason.strip()
    assert entry_event.filter_reason.strip()
    assert entry_event.structure_source in {"detector_chain", "detector_chain_temporal", "heuristic_fallback"}
    trace = adapter.get_last_decision_trace()
    assert trace
    assert trace.get("fail_stage") == "none"
    assert trace.get("trade_ok") is True


def test_pipeline_adapter_returns_entry_event_for_short_direction():
    bars = _make_bars_for_short_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            max_spread=1.0,
            fixed_lot=0.15,
            stop_loss_distance=0.01,
            take_profit_distance=0.02,
            min_distance=0.0001,
            trend_min_strength=0.0,
        )
    )

    entry_event = adapter(current_index=2, window=bars[:3])
    assert entry_event is not None
    assert entry_event.direction == "short"
    assert entry_event.lot == 0.15
    assert entry_event.stop_loss == pytest.approx(bars[2].close + 0.01)
    assert entry_event.take_profit == pytest.approx(bars[2].close - 0.02)
    assert entry_event.entry_reason.strip()
    assert entry_event.signal_reason.strip()
    assert entry_event.risk_reason.strip()
    assert entry_event.filter_reason.strip()
    assert entry_event.structure_source in {"detector_chain", "detector_chain_temporal", "heuristic_fallback"}


def test_pipeline_adapter_rejects_window_that_includes_future_bars():
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter()

    with pytest.raises(ValueError, match="window\\[-1\\]"):
        adapter(current_index=1, window=bars[:3])


def test_pipeline_adapter_disable_fallback_returns_none_when_detector_has_no_candidate():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = [
        PriceBar(timestamp=t0, open=1.00, high=1.01, low=0.99, close=1.00, spread=0.2, volume=100.0),
        PriceBar(timestamp=t0 + timedelta(hours=1), open=1.00, high=1.01, low=0.99, close=1.00, spread=0.2, volume=100.0),
    ]
    adapter = PipelineAdapter(PipelineAdapterConfig(allow_heuristic_fallback=False))
    assert adapter(current_index=1, window=bars) is None
    trace = adapter.get_last_decision_trace()
    assert trace.get("temporal_candidate") is False
    assert trace.get("recent_third_timestamp") == ""


def test_pipeline_adapter_temporal_third_break_uses_detector_chain_temporal_without_fallback():
    bars = _make_bars_for_temporal_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=False,
            allow_temporal_third_break=True,
            third_candidate_lookback_bars=5,
            swing_window=1,
            max_spread=1.0,
            trend_min_strength=0.0,
            min_distance=0.0001,
        )
    )

    entry_event = adapter(current_index=4, window=bars[:5])
    assert entry_event is not None
    assert entry_event.structure_source == "detector_chain_temporal"
    assert entry_event.fallback_used is False
    assert "temporal third_wave_break" in entry_event.entry_reason
    assert entry_event.recent_third_timestamp
    assert entry_event.recent_third_direction == "long"
    assert entry_event.temporal_lag_bars is not None
    assert entry_event.temporal_lag_bars >= 1
    assert entry_event.temporal_lookback_bars == 5
    assert entry_event.breakout_direction == "long"
    trace = adapter.get_last_decision_trace()
    assert trace.get("temporal_candidate") is True
    assert trace.get("recent_third_timestamp")


def test_pipeline_adapter_temporal_third_break_disabled_returns_none_without_fallback():
    bars = _make_bars_for_temporal_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=False,
            allow_temporal_third_break=False,
            third_candidate_lookback_bars=5,
            swing_window=1,
            max_spread=1.0,
            trend_min_strength=0.0,
            min_distance=0.0001,
        )
    )

    entry_event = adapter(current_index=4, window=bars[:5])
    assert entry_event is None


def test_pipeline_adapter_temporal_third_break_lookback_out_of_range_returns_none():
    bars = _make_bars_for_temporal_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=False,
            allow_temporal_third_break=True,
            third_candidate_lookback_bars=1,
            swing_window=1,
            max_spread=1.0,
            trend_min_strength=0.0,
            min_distance=0.0001,
        )
    )

    entry_event = adapter(current_index=4, window=bars[:5])
    assert entry_event is None


def test_pipeline_adapter_default_max_entries_none_keeps_existing_behavior(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=False,
            max_entries_per_recent_third_candidate=None,
            max_spread=1.0,
            trend_min_strength=0.0,
            min_distance=0.0001,
        )
    )
    ts = bars[2].timestamp.isoformat()

    def fake_build_structure(_window, _context_reason):
        structure = StructureResult(
            structure_type=STRUCTURE_THIRD_WAVE_BREAK,
            structure_direction="long",
            structure_candidate=True,
            pattern_reason="temporal third_wave_break candidate confirmed",
            sub_reasons=["fake"],
        )
        return structure, "third", True, False, "detector_chain_temporal", {"recent_third_timestamp": ts}

    monkeypatch.setattr(adapter, "_build_structure", fake_build_structure)
    first = adapter(current_index=2, window=bars[:3])
    second = adapter(current_index=2, window=bars[:3])
    assert first is not None
    assert second is not None
    assert first.recent_third_timestamp == ts
    assert second.recent_third_timestamp == ts


def test_pipeline_adapter_max_entries_1_blocks_second_entry_for_same_recent_third(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=False,
            max_entries_per_recent_third_candidate=1,
            max_spread=1.0,
            trend_min_strength=0.0,
            min_distance=0.0001,
        )
    )
    ts = bars[2].timestamp.isoformat()

    def fake_build_structure(_window, _context_reason):
        structure = StructureResult(
            structure_type=STRUCTURE_THIRD_WAVE_BREAK,
            structure_direction="long",
            structure_candidate=True,
            pattern_reason="temporal third_wave_break candidate confirmed",
            sub_reasons=["fake"],
        )
        return structure, "third", True, False, "detector_chain_temporal", {"recent_third_timestamp": ts}

    monkeypatch.setattr(adapter, "_build_structure", fake_build_structure)
    first = adapter(current_index=2, window=bars[:3])
    second = adapter(current_index=2, window=bars[:3])
    assert first is not None
    assert first.fallback_used is False
    assert first.structure_source == "detector_chain_temporal"
    assert second is None
    trace = adapter.get_last_decision_trace()
    assert trace.get("fail_stage") == "dedup"


def test_pipeline_adapter_max_entries_1_allows_entry_for_different_recent_third(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            allow_heuristic_fallback=False,
            max_entries_per_recent_third_candidate=1,
            max_spread=1.0,
            trend_min_strength=0.0,
            min_distance=0.0001,
        )
    )
    ts1 = bars[1].timestamp.isoformat()
    ts2 = bars[2].timestamp.isoformat()
    call_count = {"n": 0}

    def fake_build_structure(_window, _context_reason):
        call_count["n"] += 1
        structure = StructureResult(
            structure_type=STRUCTURE_THIRD_WAVE_BREAK,
            structure_direction="long",
            structure_candidate=True,
            pattern_reason="temporal third_wave_break candidate confirmed",
            sub_reasons=["fake"],
        )
        timestamp = ts1 if call_count["n"] == 1 else ts2
        return structure, "third", True, False, "detector_chain_temporal", {"recent_third_timestamp": timestamp}

    monkeypatch.setattr(adapter, "_build_structure", fake_build_structure)
    first = adapter(current_index=2, window=bars[:3])
    second = adapter(current_index=2, window=bars[:3])
    assert first is not None
    assert second is not None
    assert first.recent_third_timestamp == ts1
    assert second.recent_third_timestamp == ts2


def _force_structure(monkeypatch, adapter: PipelineAdapter, direction: str = "long") -> None:
    def fake_build_structure(_window, _context_reason):
        structure = StructureResult(
            structure_type=STRUCTURE_THIRD_WAVE_BREAK,
            structure_direction=direction,
            structure_candidate=True,
            pattern_reason="forced structure",
            sub_reasons=["forced"],
        )
        return structure, "third", True, False, "detector_chain", {"breakout_direction": direction}

    monkeypatch.setattr(adapter, "_build_structure", fake_build_structure)


def _force_htf(monkeypatch, bias: str, trend_dir: str) -> None:
    def fake_trend_detect(_bars, _cfg):
        return TrendResult(htf_trend_dir=trend_dir, htf_trend_strength=0.5, trend_reason="forced trend")

    def fake_assemble(**_kwargs):
        return HTFContextResult(
            htf_trend_dir=trend_dir,
            htf_trend_strength=0.5,
            htf_resistance_ok=True,
            htf_support_ok=True,
            htf_bias=bias,  # type: ignore[arg-type]
            htf_context_reason="forced context",
            sub_reasons=[],
        )

    monkeypatch.setattr("src.backtest.pipeline_adapter.TrendDetector.detect", fake_trend_detect)
    monkeypatch.setattr("src.backtest.pipeline_adapter.ContextAssembler.assemble", fake_assemble)


def _make_m5_bars(count: int, start: datetime | None = None, drift: float = 0.001) -> list[PriceBar]:
    t0 = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars: list[PriceBar] = []
    price = 100.0
    for i in range(count):
        open_price = price
        close_price = price + drift
        high = max(open_price, close_price) + 0.002
        low = min(open_price, close_price) - 0.002
        bars.append(
            PriceBar(
                timestamp=t0 + timedelta(minutes=5 * i),
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                spread=0.2,
                volume=100.0 + i,
            )
        )
        price = close_price
    return bars


def test_session_v2_disabled_keeps_existing_entry_behavior(monkeypatch):
    bars = _make_m5_bars(80, drift=0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(session_v2_enabled=False, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    event = adapter(current_index=len(bars) - 1, window=bars)
    assert event is not None
    trace = adapter.get_last_decision_trace()
    assert trace["session_v2_enabled"] is False
    assert trace["session_reason"] == "session_v2 disabled"


def test_session_v2_diagnostic_only_does_not_block_entry(monkeypatch):
    bars = _make_m5_bars(80, drift=0.01)
    disabled = PipelineAdapter(PipelineAdapterConfig(session_v2_enabled=False, max_spread=1.0, trend_min_strength=0.0))
    diagnostic = PipelineAdapter(
        PipelineAdapterConfig(
            session_v2_enabled=True,
            session_v2_policy="diagnostic_only",
            max_spread=1.0,
            trend_min_strength=0.0,
        )
    )
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    _force_structure(monkeypatch, disabled, direction="long")
    _force_structure(monkeypatch, diagnostic, direction="long")
    ev_disabled = disabled(current_index=len(bars) - 1, window=bars)
    ev_diag = diagnostic(current_index=len(bars) - 1, window=bars)
    assert (ev_disabled is None) == (ev_diag is None)
    if ev_disabled is not None and ev_diag is not None:
        assert ev_disabled.direction == ev_diag.direction
    trace = diagnostic.get_last_decision_trace()
    assert "diagnostic_only:no_entry_filter" in str(trace["session_reason"])


def test_session_v2_trace_contains_hour_and_day_of_week():
    ts = datetime(2026, 1, 1, 13, 30, tzinfo=timezone.utc)
    bar = PriceBar(timestamp=ts, open=100.0, high=100.1, low=99.9, close=100.0, spread=0.2, volume=1.0)
    adapter = PipelineAdapter(PipelineAdapterConfig(session_v2_enabled=True))
    trace = adapter._compute_session_v2_trace(current_bar=bar)  # noqa: SLF001
    assert trace["hour_utc"] == 13
    assert trace["day_of_week"] == "thursday"


def test_session_v2_classification_labels_by_utc_boundaries():
    adapter = PipelineAdapter(PipelineAdapterConfig(session_v2_enabled=True))
    label_tokyo = adapter._compute_session_v2_trace(  # noqa: SLF001
        PriceBar(datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc), 1, 1, 1, 1, 0.2, 1.0)
    )["session_label"]
    label_london = adapter._compute_session_v2_trace(  # noqa: SLF001
        PriceBar(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc), 1, 1, 1, 1, 0.2, 1.0)
    )["session_label"]
    label_overlap = adapter._compute_session_v2_trace(  # noqa: SLF001
        PriceBar(datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc), 1, 1, 1, 1, 0.2, 1.0)
    )["session_label"]
    label_new_york = adapter._compute_session_v2_trace(  # noqa: SLF001
        PriceBar(datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc), 1, 1, 1, 1, 0.2, 1.0)
    )["session_label"]
    label_low = adapter._compute_session_v2_trace(  # noqa: SLF001
        PriceBar(datetime(2026, 1, 1, 23, 0, tzinfo=timezone.utc), 1, 1, 1, 1, 0.2, 1.0)
    )["session_label"]
    assert label_tokyo == "tokyo"
    assert label_london == "london"
    assert label_overlap == "london_ny_overlap"
    assert label_new_york == "new_york"
    assert label_low == "low_liquidity"


def test_session_v2_dst_adjustment_flag_is_not_used_in_initial_impl():
    bar = PriceBar(datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc), 1, 1, 1, 1, 0.2, 1.0)
    off = PipelineAdapter(PipelineAdapterConfig(session_v2_enabled=True, session_v2_use_dst_adjustment=False))
    on = PipelineAdapter(PipelineAdapterConfig(session_v2_enabled=True, session_v2_use_dst_adjustment=True))
    trace_off = off._compute_session_v2_trace(bar)  # noqa: SLF001
    trace_on = on._compute_session_v2_trace(bar)  # noqa: SLF001
    assert trace_off["session_label"] == trace_on["session_label"]
    assert trace_off["hour_utc"] == trace_on["hour_utc"]


def test_session_v2_risk_flag_true_on_low_liquidity():
    bar = PriceBar(datetime(2026, 1, 1, 22, 0, tzinfo=timezone.utc), 1, 1, 1, 1, 0.2, 1.0)
    adapter = PipelineAdapter(PipelineAdapterConfig(session_v2_enabled=True))
    trace = adapter._compute_session_v2_trace(bar)  # noqa: SLF001
    assert trace["is_low_liquidity_hour"] is True
    assert trace["session_risk_flag"] is True


def test_session_v2_decision_trace_contains_expected_columns(monkeypatch):
    bars = _make_m5_bars(100, drift=0.01)
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            session_v2_enabled=True,
            session_v2_policy="diagnostic_only",
            max_spread=1.0,
            trend_min_strength=0.0,
        )
    )
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    _ = adapter(current_index=len(bars) - 1, window=bars)
    trace = adapter.get_last_decision_trace()
    for key in [
        "session_v2_enabled",
        "session_policy",
        "hour_utc",
        "day_of_week",
        "session_label",
        "is_tokyo_session",
        "is_london_session",
        "is_new_york_session",
        "is_london_ny_overlap",
        "is_low_liquidity_hour",
        "session_risk_flag",
        "session_reason",
        "session_data_valid_flag",
    ]:
        assert key in trace


def test_sr_v2_disabled_keeps_existing_entry_behavior(monkeypatch):
    bars = _make_m5_bars(80, drift=0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=False, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    event = adapter(current_index=len(bars) - 1, window=bars)
    assert event is not None
    trace = adapter.get_last_decision_trace()
    assert trace["sr_v2_enabled"] is False
    assert trace["sr_reason"] == "sr_v2 disabled"


def test_sr_v2_diagnostic_only_does_not_block_entry(monkeypatch):
    bars = _make_m5_bars(80, drift=0.01)
    disabled = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=False, max_spread=1.0, trend_min_strength=0.0))
    diagnostic = PipelineAdapter(
        PipelineAdapterConfig(
            sr_v2_enabled=True,
            sr_v2_policy="diagnostic_only",
            sr_v2_window_bars=20,
            max_spread=1.0,
            trend_min_strength=0.0,
        )
    )
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    _force_structure(monkeypatch, disabled, direction="long")
    _force_structure(monkeypatch, diagnostic, direction="long")

    ev_disabled = disabled(current_index=len(bars) - 1, window=bars)
    ev_diag = diagnostic(current_index=len(bars) - 1, window=bars)
    assert (ev_disabled is None) == (ev_diag is None)
    if ev_disabled is not None and ev_diag is not None:
        assert ev_disabled.direction == ev_diag.direction
    trace = diagnostic.get_last_decision_trace()
    assert "diagnostic_only:no_entry_filter" in str(trace["sr_reason"])


def test_sr_v2_long_proximity_uses_resistance_threshold():
    bars = [
        PriceBar(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), 100.00, 100.08, 99.90, 100.00, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc), 100.00, 100.07, 99.92, 100.01, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc), 100.01, 100.06, 99.93, 100.02, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc), 100.02, 100.04, 99.94, 100.03, 0.2, 1.0),
    ]
    adapter = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=True, sr_v2_window_bars=3, sr_v2_near_threshold_pips=10.0))
    trace = adapter._compute_sr_v2_trace(window=bars, current_bar=bars[-1], candidate_direction="long")  # noqa: SLF001
    assert trace["sr_data_valid_flag"] is True
    assert trace["sr_proximity_flag"] is True
    assert trace["sr_block_side"] == "resistance"


def test_sr_v2_short_proximity_uses_support_threshold():
    bars = [
        PriceBar(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), 100.10, 100.20, 99.98, 100.10, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc), 100.10, 100.18, 99.99, 100.09, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc), 100.09, 100.16, 100.00, 100.08, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc), 100.08, 100.15, 99.97, 99.99, 0.2, 1.0),
    ]
    adapter = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=True, sr_v2_window_bars=3, sr_v2_near_threshold_pips=10.0))
    trace = adapter._compute_sr_v2_trace(window=bars, current_bar=bars[-1], candidate_direction="short")  # noqa: SLF001
    assert trace["sr_data_valid_flag"] is True
    assert trace["sr_proximity_flag"] is True
    assert trace["sr_block_side"] == "support"


def test_sr_v2_long_does_not_block_support_side():
    bars = [
        PriceBar(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), 100.20, 100.80, 100.00, 100.20, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc), 100.20, 100.70, 100.01, 100.18, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc), 100.18, 100.60, 100.02, 100.16, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc), 100.16, 100.50, 100.03, 100.02, 0.2, 1.0),
    ]
    adapter = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=True, sr_v2_window_bars=3, sr_v2_near_threshold_pips=3.0))
    trace = adapter._compute_sr_v2_trace(window=bars, current_bar=bars[-1], candidate_direction="long")  # noqa: SLF001
    assert trace["nearest_support_distance_pips"] <= 3.0
    assert trace["nearest_resistance_distance_pips"] > 3.0
    assert trace["sr_proximity_flag"] is False


def test_sr_v2_short_does_not_block_resistance_side():
    bars = [
        PriceBar(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), 99.90, 100.05, 99.30, 99.90, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc), 99.90, 100.04, 99.40, 99.91, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc), 99.91, 100.03, 99.50, 99.92, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc), 99.92, 100.02, 99.60, 100.03, 0.2, 1.0),
    ]
    adapter = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=True, sr_v2_window_bars=3, sr_v2_near_threshold_pips=3.0))
    trace = adapter._compute_sr_v2_trace(window=bars, current_bar=bars[-1], candidate_direction="short")  # noqa: SLF001
    assert trace["nearest_resistance_distance_pips"] <= 3.0
    assert trace["nearest_support_distance_pips"] > 3.0
    assert trace["sr_proximity_flag"] is False


def test_sr_v2_uses_only_past_bars_not_current_or_future():
    bars = [
        PriceBar(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), 100.0, 100.20, 99.80, 100.0, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc), 100.0, 100.30, 99.70, 100.0, 0.2, 1.0),
        PriceBar(datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc), 100.0, 999.0, 1.0, 100.0, 0.2, 1.0),
    ]
    adapter = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=True, sr_v2_window_bars=2))
    trace = adapter._compute_sr_v2_trace(window=bars, current_bar=bars[-1], candidate_direction="long")  # noqa: SLF001
    assert trace["nearest_resistance"] == pytest.approx(100.30)
    assert trace["nearest_support"] == pytest.approx(99.70)


def test_sr_v2_insufficient_history_sets_data_valid_false():
    bars = _make_m5_bars(5)
    adapter = PipelineAdapter(PipelineAdapterConfig(sr_v2_enabled=True, sr_v2_window_bars=10))
    trace = adapter._compute_sr_v2_trace(window=bars, current_bar=bars[-1], candidate_direction="long")  # noqa: SLF001
    assert trace["sr_data_valid_flag"] is False
    assert "insufficient_history" in str(trace["sr_reason"])


def test_sr_v2_decision_trace_contains_expected_columns(monkeypatch):
    bars = _make_m5_bars(100, drift=0.01)
    adapter = PipelineAdapter(
        PipelineAdapterConfig(
            sr_v2_enabled=True,
            sr_v2_policy="diagnostic_only",
            sr_v2_window_bars=20,
            max_spread=1.0,
            trend_min_strength=0.0,
        )
    )
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    _ = adapter(current_index=len(bars) - 1, window=bars)
    trace = adapter.get_last_decision_trace()
    for key in [
        "sr_v2_enabled",
        "sr_policy",
        "sr_window_bars",
        "nearest_resistance",
        "nearest_support",
        "nearest_resistance_distance_pips",
        "nearest_support_distance_pips",
        "sr_proximity_flag",
        "sr_block_side",
        "sr_reason",
        "sr_data_valid_flag",
        "sr_counterfactual_group",
    ]:
        assert key in trace


def test_htf_filter_disabled_keeps_existing_behavior(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_filter_enabled=False, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="short_bias", trend_dir="up")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is None
    trace = adapter.get_last_decision_trace()
    assert trace["htf_filter_enabled"] is False


def test_htf_filter_v1_long_up_passes(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(htf_filter_enabled=True, htf_neutral_policy="permissive", max_spread=1.0, trend_min_strength=0.0)
    )
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="down")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is not None


def test_htf_filter_v1_long_down_rejected(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_filter_enabled=True, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="short_bias", trend_dir="up")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is None


def test_htf_filter_v1_short_down_passes(monkeypatch):
    bars = _make_bars_for_short_breakout()
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_filter_enabled=True, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="short")
    _force_htf(monkeypatch, bias="short_bias", trend_dir="up")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is not None


def test_htf_filter_v1_short_up_rejected(monkeypatch):
    bars = _make_bars_for_short_breakout()
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_filter_enabled=True, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="short")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="down")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is None


def test_htf_filter_v1_neutral_permissive_passes(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(htf_filter_enabled=True, htf_neutral_policy="permissive", max_spread=1.0, trend_min_strength=0.0)
    )
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="neutral", trend_dir="neutral")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is not None


def test_htf_filter_v1_neutral_strict_rejected(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(
        PipelineAdapterConfig(htf_filter_enabled=True, htf_neutral_policy="strict", max_spread=1.0, trend_min_strength=0.0)
    )
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="neutral", trend_dir="neutral")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is None


def test_htf_filter_v1_bias_missing_uses_trend_fallback_with_reason(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_filter_enabled=True, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="", trend_dir="up")
    ev = adapter(current_index=2, window=bars[:3])
    assert ev is not None
    trace = adapter.get_last_decision_trace()
    assert "source=htf_trend_dir_fallback" in str(trace.get("htf_filter_reason", ""))


def test_decision_trace_contains_minimal_htf_columns(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_filter_enabled=True, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    _ = adapter(current_index=2, window=bars[:3])
    trace = adapter.get_last_decision_trace()
    for key in [
        "htf_filter_enabled",
        "htf_timeframe_policy",
        "htf_neutral_policy",
        "htf_bias",
        "htf_trend_dir",
        "htf_direction_aligned",
        "htf_filter_reason",
        "htf_context_reason",
    ]:
        assert key in trace


def test_htf_v2_disabled_default_keeps_existing_entry_behavior(monkeypatch):
    bars = _make_bars_for_long_breakout()
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=False, max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    event = adapter(current_index=2, window=bars[:3])
    assert event is not None
    trace = adapter.get_last_decision_trace()
    assert trace["htf_v2_enabled"] is False
    assert trace["htf_v2_filter_reason"] == "htf_v2 disabled"


def test_htf_v2_diagnostic_only_does_not_block_entry(monkeypatch):
    bars = _make_m5_bars(300, drift=0.01)
    cfg = PipelineAdapterConfig(
        htf_v2_enabled=True,
        htf_v2_policy="diagnostic_only",
        max_spread=1.0,
        trend_min_strength=0.0,
    )
    adapter = PipelineAdapter(cfg)
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    event = adapter(current_index=len(bars) - 1, window=bars)
    assert event is not None
    trace = adapter.get_last_decision_trace()
    assert trace["trade_ok"] is True
    assert trace["htf_v2_enabled"] is True
    assert trace["htf_policy"] == "diagnostic_only"
    assert str(trace["htf_v2_filter_reason"]).startswith("diagnostic_only")


def test_htf_v2_h4_up_and_h1_aligned_up_classification():
    bars = _make_m5_bars(2600, drift=0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="diagnostic_only"))
    trace = adapter._compute_htf_v2_trace(window=bars, current_bar=bars[-1])  # noqa: SLF001
    assert trace["h4_bias"] == "up"
    assert trace["h1_context"] == "aligned_up"
    assert trace["htf_v2_data_valid_flag"] is True


def test_htf_v2_h4_down_and_h1_aligned_down_classification():
    bars = _make_m5_bars(2600, drift=-0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="diagnostic_only"))
    trace = adapter._compute_htf_v2_trace(window=bars, current_bar=bars[-1])  # noqa: SLF001
    assert trace["h4_bias"] == "down"
    assert trace["h1_context"] == "aligned_down"
    assert trace["htf_v2_data_valid_flag"] is True


def test_htf_v2_pullback_against_h4_classification(monkeypatch):
    bars = _make_m5_bars(30, drift=0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="diagnostic_only"))

    h4_closes = [100 + i for i in range(70)]  # clear up bias on H4
    h1_closes = [200 - i for i in range(30)]  # clear down trend on H1
    fake_h4 = [
        {"start_time": bars[0].timestamp, "close_time": bars[0].timestamp, "open": c, "high": c, "low": c, "close": c}
        for c in h4_closes
    ]
    fake_h1 = [
        {"start_time": bars[0].timestamp, "close_time": bars[0].timestamp, "open": c, "high": c, "low": c, "close": c}
        for c in h1_closes
    ]

    def fake_aggregate(window, timeframe_minutes, decision_time):  # noqa: ARG001
        if timeframe_minutes == 60:
            return fake_h1, True, "ok"
        if timeframe_minutes == 240:
            return fake_h4, True, "ok"
        raise AssertionError("unexpected timeframe")

    monkeypatch.setattr(adapter, "_aggregate_completed_htf_bars", fake_aggregate)
    trace = adapter._compute_htf_v2_trace(window=bars, current_bar=bars[-1])  # noqa: SLF001
    assert trace["h4_bias"] == "up"
    assert trace["h1_context"] == "pullback_against_h4"


def test_htf_v2_unknown_when_insufficient_history_and_data_invalid_flag_false():
    bars = _make_m5_bars(12, drift=0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=True))
    trace = adapter._compute_htf_v2_trace(window=bars, current_bar=bars[-1])  # noqa: SLF001
    assert trace["h4_bias"] == "unknown"
    assert trace["h1_context"] == "unknown"
    assert trace["htf_v2_data_valid_flag"] is False
    assert (trace["htf_v2_data_valid_flag"] is False) or (trace["htf_v2_context_uncertain_flag"] is True)


def test_htf_v2_diagnostic_only_keeps_entry_decision_equivalent_to_disabled(monkeypatch):
    bars = _make_m5_bars(300, drift=0.01)
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")

    disabled = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=False, max_spread=1.0, trend_min_strength=0.0))
    diagnostic = PipelineAdapter(
        PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="diagnostic_only", max_spread=1.0, trend_min_strength=0.0)
    )
    _force_structure(monkeypatch, disabled, direction="long")
    _force_structure(monkeypatch, diagnostic, direction="long")

    ev_disabled = disabled(current_index=len(bars) - 1, window=bars)
    ev_diag = diagnostic(current_index=len(bars) - 1, window=bars)

    assert (ev_disabled is None) == (ev_diag is None)
    if ev_disabled is not None and ev_diag is not None:
        assert ev_disabled.direction == ev_diag.direction


def test_htf_v2_does_not_use_unconfirmed_h1_h4_bar():
    bars = _make_m5_bars(13, drift=0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=True))
    # At bar index 12, decision time is 01:05 and only 00:00-01:00 H1 can be used.
    trace = adapter._compute_htf_v2_trace(window=bars, current_bar=bars[-1])  # noqa: SLF001
    assert trace["h1_context"] == "unknown"
    assert trace["htf_v2_data_valid_flag"] is False


def test_htf_v2_decision_trace_contains_expected_columns(monkeypatch):
    bars = _make_m5_bars(300, drift=0.01)
    adapter = PipelineAdapter(
        PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="diagnostic_only", max_spread=1.0, trend_min_strength=0.0)
    )
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    _ = adapter(current_index=len(bars) - 1, window=bars)
    trace = adapter.get_last_decision_trace()
    for key in [
        "htf_v2_enabled",
        "htf_policy",
        "h4_bias",
        "h4_bias_reason",
        "h4_ma20",
        "h4_ma50",
        "h4_ma20_slope",
        "h1_context",
        "h1_context_reason",
        "h1_ma20",
        "h1_ma20_slope",
        "htf_v2_direction_allowed",
        "htf_v2_candidate_direction",
        "htf_v2_aligned_only_allowed",
        "htf_v2_pullback_permissive_allowed",
        "htf_v2_context_uncertain_flag",
        "htf_v2_hard_conflict_flag",
        "htf_v2_filter_reason",
        "htf_v2_conflict_flag",
        "htf_v2_data_valid_flag",
    ]:
        assert key in trace


def test_htf_v2_neutral_h4_maps_to_range_or_neutral_context(monkeypatch):
    bars = _make_m5_bars(30, drift=0.001)
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="diagnostic_only"))
    h4_closes = [100.0 for _ in range(70)]
    h1_closes = [100.0 + (i * 0.5) for i in range(30)]
    fake_h4 = [
        {"start_time": bars[0].timestamp, "close_time": bars[0].timestamp, "open": c, "high": c, "low": c, "close": c}
        for c in h4_closes
    ]
    fake_h1 = [
        {"start_time": bars[0].timestamp, "close_time": bars[0].timestamp, "open": c, "high": c, "low": c, "close": c}
        for c in h1_closes
    ]

    def fake_aggregate(window, timeframe_minutes, decision_time):  # noqa: ARG001
        return (fake_h1, True, "ok") if timeframe_minutes == 60 else (fake_h4, True, "ok")

    monkeypatch.setattr(adapter, "_aggregate_completed_htf_bars", fake_aggregate)
    trace = adapter._compute_htf_v2_trace(window=bars, current_bar=bars[-1])  # noqa: SLF001
    assert trace["h4_bias"] == "neutral"
    assert trace["h1_context"] == "range_or_neutral"


def test_htf_v2_aligned_only_policy_direction_allowed(monkeypatch):
    bars = _make_m5_bars(300, drift=0.01)
    adapter = PipelineAdapter(PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="aligned_only", max_spread=1.0, trend_min_strength=0.0))
    _force_structure(monkeypatch, adapter, direction="long")
    _force_htf(monkeypatch, bias="long_bias", trend_dir="up")
    monkeypatch.setattr(
        adapter,
        "_compute_htf_v2_trace",
        lambda window, current_bar: {  # noqa: ARG005
            "htf_v2_enabled": True,
            "htf_policy": "aligned_only",
            "h4_bias": "up",
            "h4_bias_reason": "forced",
            "h4_ma20": 1.0,
            "h4_ma50": 1.0,
            "h4_ma20_slope": 0.1,
            "h1_context": "aligned_up",
            "h1_context_reason": "forced",
            "h1_ma20": 1.0,
            "h1_ma20_slope": 0.1,
            "htf_v2_direction_allowed": False,
            "htf_v2_filter_reason": "aligned_only:direction_allowed_computed",
            "htf_v2_conflict_flag": False,
            "htf_v2_data_valid_flag": True,
            "htf_v2_candidate_direction": "unknown",
            "htf_v2_aligned_only_allowed": False,
            "htf_v2_pullback_permissive_allowed": False,
            "htf_v2_context_uncertain_flag": False,
            "htf_v2_hard_conflict_flag": False,
        },
    )
    event = adapter(current_index=len(bars) - 1, window=bars)
    assert event is not None
    trace = adapter.get_last_decision_trace()
    assert trace["htf_v2_candidate_direction"] == "long"
    assert trace["htf_v2_aligned_only_allowed"] is True
    assert trace["htf_v2_direction_allowed"] is True


def test_htf_v2_pullback_permissive_policy_direction_allowed_on_pullback(monkeypatch):
    bars = _make_m5_bars(300, drift=0.01)
    adapter = PipelineAdapter(
        PipelineAdapterConfig(htf_v2_enabled=True, htf_v2_policy="pullback_permissive", max_spread=1.0, trend_min_strength=0.0)
    )
    _force_structure(monkeypatch, adapter, direction="long")
    # Force H4 up + H1 down by patching htf_v2 trace calculation stage.
    monkeypatch.setattr(
        adapter,
        "_compute_htf_v2_trace",
        lambda window, current_bar: {  # noqa: ARG005
            "htf_v2_enabled": True,
            "htf_policy": "pullback_permissive",
            "h4_bias": "up",
            "h4_bias_reason": "forced",
            "h4_ma20": 1.0,
            "h4_ma50": 1.0,
            "h4_ma20_slope": 0.1,
            "h1_context": "pullback_against_h4",
            "h1_context_reason": "forced",
            "h1_ma20": 1.0,
            "h1_ma20_slope": -0.1,
            "htf_v2_direction_allowed": False,
            "htf_v2_filter_reason": "pullback_permissive:direction_allowed_computed",
            "htf_v2_conflict_flag": False,
            "htf_v2_data_valid_flag": True,
            "htf_v2_candidate_direction": "unknown",
            "htf_v2_aligned_only_allowed": False,
            "htf_v2_pullback_permissive_allowed": False,
            "htf_v2_context_uncertain_flag": False,
            "htf_v2_hard_conflict_flag": False,
        },
    )
    event = adapter(current_index=len(bars) - 1, window=bars)
    assert event is not None
    trace = adapter.get_last_decision_trace()
    assert trace["htf_v2_candidate_direction"] == "long"
    assert trace["htf_v2_pullback_permissive_allowed"] is True
    assert trace["htf_v2_direction_allowed"] is True


def test_htf_v2_semantics_long_up_aligned_sets_aligned_only_allowed_true():
    sem = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="long",
        h4_bias="up",
        h1_context="aligned_up",
    )
    assert sem["htf_v2_aligned_only_allowed"] is True


def test_htf_v2_semantics_short_down_aligned_sets_aligned_only_allowed_true():
    sem = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="short",
        h4_bias="down",
        h1_context="aligned_down",
    )
    assert sem["htf_v2_aligned_only_allowed"] is True


def test_htf_v2_semantics_long_up_pullback_sets_pullback_permissive_allowed_true():
    sem = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="long",
        h4_bias="up",
        h1_context="pullback_against_h4",
    )
    assert sem["htf_v2_pullback_permissive_allowed"] is True


def test_htf_v2_semantics_short_down_pullback_sets_pullback_permissive_allowed_true():
    sem = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="short",
        h4_bias="down",
        h1_context="pullback_against_h4",
    )
    assert sem["htf_v2_pullback_permissive_allowed"] is True


def test_htf_v2_semantics_neutral_or_range_marks_uncertain_true():
    sem1 = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="long",
        h4_bias="neutral",
        h1_context="aligned_up",
    )
    sem2 = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="long",
        h4_bias="up",
        h1_context="range_or_neutral",
    )
    assert sem1["htf_v2_context_uncertain_flag"] is True
    assert sem2["htf_v2_context_uncertain_flag"] is True


def test_htf_v2_semantics_long_down_is_hard_conflict_true():
    sem = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="long",
        h4_bias="down",
        h1_context="aligned_down",
    )
    assert sem["htf_v2_hard_conflict_flag"] is True


def test_htf_v2_semantics_short_up_is_hard_conflict_true():
    sem = PipelineAdapter._compute_htf_v2_policy_diagnostics(  # noqa: SLF001
        candidate_direction="short",
        h4_bias="up",
        h1_context="aligned_up",
    )
    assert sem["htf_v2_hard_conflict_flag"] is True
