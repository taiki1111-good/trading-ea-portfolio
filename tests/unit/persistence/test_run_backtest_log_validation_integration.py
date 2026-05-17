from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "run_backtest_on_m5_slice.py"
_spec = importlib.util.spec_from_file_location("run_backtest_on_m5_slice", SCRIPT_PATH)
_module = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(_module)


def _valid_trade_log() -> dict[str, object]:
    return {
        "log_time": "2026-05-01T00:00:00+00:00",
        "entry_time": "2026-05-01T00:00:00+00:00",
        "exit_time": "2026-05-01T00:05:00+00:00",
        "signal_type": "long_entry",
        "order_result": "filled",
        "lot": 0.1,
        "fill_price": 150.0,
        "execution_price": 150.0,
        "stop_loss": 149.99,
        "take_profit": 150.02,
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


def _valid_decision_log() -> dict[str, object]:
    return {
        "log_time": "2026-05-01T00:00:00+00:00",
        "bar_index": 1,
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


def test_evaluate_log_validation_valid_logs():
    validation = _module.evaluate_log_validation([_valid_trade_log()], [_valid_decision_log()])
    assert validation["trade_logs_schema_valid"] is True
    assert validation["decision_logs_schema_valid"] is True
    assert validation["log_consistency_valid"] is True


def test_evaluate_log_validation_invalid_decision_logs():
    bad = _valid_decision_log()
    bad.pop("decision_reason")
    validation = _module.evaluate_log_validation([_valid_trade_log()], [bad])
    assert validation["decision_logs_schema_valid"] is False


def test_evaluate_log_validation_detects_consistency_invalid():
    bad = _valid_decision_log()
    bad["trade_ok"] = False
    validation = _module.evaluate_log_validation([_valid_trade_log()], [bad])
    assert validation["trade_logs_schema_valid"] is True
    assert validation["decision_logs_schema_valid"] is True
    assert validation["log_consistency_valid"] is False
