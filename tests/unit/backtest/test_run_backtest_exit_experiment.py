from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.run_backtest_exit_experiment import _parse_utc_bound
from scripts.run_backtest_exit_experiment import _slice_price_frame
from scripts.run_backtest_exit_experiment import main
from scripts.run_backtest_exit_experiment import parse_args
from scripts.run_backtest_exit_experiment import run_backtest_exit_experiment
from src.backtest.backtest_runner import EntryEvent
from src.backtest.types import BacktestConfig
from src.data.types import PriceBar


def _bars() -> list[PriceBar]:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    return [
        PriceBar(t0, 100.0, 100.2, 99.9, 100.0, 0.2, 1.0),
        PriceBar(t0 + timedelta(minutes=5), 100.0, 101.2, 99.7, 100.8, 0.2, 1.0),
        PriceBar(t0 + timedelta(minutes=10), 100.8, 100.9, 99.0, 99.4, 0.2, 1.0),
        PriceBar(t0 + timedelta(minutes=15), 99.4, 99.8, 98.8, 99.0, 0.2, 1.0),
    ]


def test_fixed_sl_tp_default_behavior_not_broken() -> None:
    bars = _bars()
    cfg = BacktestConfig(run_id='t1', max_holding_bars=10)

    def provider(i, _window):
        if i == 0:
            return EntryEvent(i, 'long', 1.0, 99.0, 101.0, 'entry')
        return None

    result = run_backtest_exit_experiment(bars, cfg, provider, exit_policy='fixed_sl_tp')
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == 'take_profit'


def test_trailing_used_only_when_specified() -> None:
    bars = _bars()
    cfg = BacktestConfig(run_id='t2', max_holding_bars=10)

    def provider(i, _window):
        if i == 0:
            return EntryEvent(i, 'long', 1.0, 99.0, 103.0, 'entry')
        return None

    fixed = run_backtest_exit_experiment(bars, cfg, provider, exit_policy='fixed_sl_tp')
    trailing = run_backtest_exit_experiment(bars, cfg, provider, exit_policy='simple_trailing_after_1R')
    assert fixed.trades[0].exit_reason != 'trailing_stop'
    assert trailing.trades[0].exit_reason == 'trailing_stop'


def test_entry_logic_same_between_policies() -> None:
    bars = _bars()
    cfg = BacktestConfig(run_id='t3', max_holding_bars=10)

    def provider(i, _window):
        if i == 0:
            return EntryEvent(i, 'long', 1.0, 99.0, 102.0, 'entry')
        return None

    fixed = run_backtest_exit_experiment(bars, cfg, provider, exit_policy='fixed_sl_tp')
    trailing = run_backtest_exit_experiment(bars, cfg, provider, exit_policy='simple_trailing_after_1R')
    assert fixed.trades[0].entry_time == trailing.trades[0].entry_time


def test_no_exit_on_entry_bar() -> None:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    bars = [
        PriceBar(t0, 100.0, 101.5, 98.5, 100.0, 0.2, 1.0),
        PriceBar(t0 + timedelta(minutes=5), 100.0, 100.1, 99.0, 99.5, 0.2, 1.0),
    ]
    cfg = BacktestConfig(run_id='t4', max_holding_bars=10)

    def provider(i, _window):
        if i == 0:
            return EntryEvent(i, 'long', 1.0, 99.0, 101.0, 'entry')
        return None

    result = run_backtest_exit_experiment(bars, cfg, provider, exit_policy='simple_trailing_after_1R')
    assert result.trades[0].exit_time == bars[1].timestamp


def test_long_short_pnl_signs() -> None:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    bars = [
        PriceBar(t0, 100.0, 100.0, 100.0, 100.0, 0.2, 1.0),
        PriceBar(t0 + timedelta(minutes=5), 100.0, 101.1, 99.8, 101.0, 0.2, 1.0),
        PriceBar(t0 + timedelta(minutes=10), 101.0, 101.2, 100.8, 101.1, 0.2, 1.0),
        PriceBar(t0 + timedelta(minutes=15), 101.1, 101.3, 99.0, 99.1, 0.2, 1.0),
    ]
    cfg = BacktestConfig(run_id='t5', max_holding_bars=10)

    def provider(i, _window):
        if i == 0:
            return EntryEvent(i, 'long', 1.0, 99.0, 101.0, 'long')
        if i == 2:
            return EntryEvent(i, 'short', 1.0, 102.0, 100.0, 'short')
        return None

    result = run_backtest_exit_experiment(bars, cfg, provider, exit_policy='fixed_sl_tp')
    assert len(result.trades) == 2
    assert result.trades[0].pnl > 0
    assert result.trades[1].pnl > 0


def test_period_slice_keeps_requested_range() -> None:
    bars = _bars()
    start = _parse_utc_bound("2024-01-01T00:05:00Z")
    end = _parse_utc_bound("2024-01-01T00:15:00Z")
    sliced = _slice_price_frame(bars, start, end)
    assert len(sliced) == 2
    assert sliced[0].timestamp == bars[1].timestamp
    assert sliced[-1].timestamp == bars[2].timestamp


def test_progress_output_runs_without_trades(capsys) -> None:
    bars = _bars()
    cfg = BacktestConfig(run_id='t6', max_holding_bars=10)

    def provider(_i, _window):
        return None

    _ = run_backtest_exit_experiment(
        bars,
        cfg,
        provider,
        exit_policy='fixed_sl_tp',
        progress_every_bars=1,
    )
    out = capsys.readouterr().out
    assert '[progress]' in out


def test_decision_logs_keep_htf_trace_columns_from_provider() -> None:
    bars = _bars()
    cfg = BacktestConfig(run_id='t7', max_holding_bars=10)

    class Provider:
        def __call__(self, _i, _window):
            return None

        def get_last_decision_trace(self):
            return {
                "htf_filter_enabled": True,
                "htf_timeframe_policy": "H1_only",
                "htf_neutral_policy": "strict",
                "htf_bias": "neutral",
                "htf_trend_dir": "up",
                "htf_direction_aligned": False,
                "htf_filter_reason": "test",
                "htf_context_reason": "ctx",
            }

    result = run_backtest_exit_experiment(bars, cfg, Provider(), exit_policy='fixed_sl_tp')
    assert result.decision_logs
    row = result.decision_logs[0]
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
        assert key in row


def test_parse_args_accepts_htf_v2_flags(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_backtest_exit_experiment.py",
            "--input-csv",
            "dummy.csv",
            "--run-id",
            "r1",
            "--output-dir",
            "out",
            "--max-holding-bars",
            "10",
            "--htf-v2-enabled",
            "--htf-v2-policy",
            "diagnostic_only",
            "--htf-v2-h4-ma-fast",
            "21",
            "--htf-v2-h4-ma-slow",
            "55",
            "--htf-v2-h1-ma-fast",
            "22",
            "--htf-v2-slope-window",
            "4",
        ],
    )
    args = parse_args()
    assert args.htf_v2_enabled is True
    assert args.htf_v2_policy == "diagnostic_only"
    assert args.htf_v2_h4_ma_fast == 21
    assert args.htf_v2_h4_ma_slow == 55
    assert args.htf_v2_h1_ma_fast == 22
    assert args.htf_v2_slope_window == 4


def test_parse_args_htf_v2_defaults(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_backtest_exit_experiment.py",
            "--input-csv",
            "dummy.csv",
            "--run-id",
            "r2",
            "--output-dir",
            "out",
            "--max-holding-bars",
            "10",
        ],
    )
    args = parse_args()
    assert args.htf_v2_enabled is False
    assert args.htf_v2_policy == "diagnostic_only"
    assert args.htf_v2_h4_ma_fast == 20
    assert args.htf_v2_h4_ma_slow == 50
    assert args.htf_v2_h1_ma_fast == 20
    assert args.htf_v2_slope_window == 3
    assert args.sr_v2_enabled is False
    assert args.sr_v2_policy == "diagnostic_only"
    assert args.sr_v2_window_bars == 48
    assert args.sr_v2_near_threshold_pips == 10.0
    assert args.sr_v2_pip_size == 0.01
    assert args.sr_v2_use_atr_normalized is False
    assert args.session_v2_enabled is False
    assert args.session_v2_policy == "diagnostic_only"
    assert args.session_v2_timezone == "UTC"
    assert args.session_v2_use_day_of_week is True
    assert args.session_v2_use_hour_bucket is True
    assert args.session_v2_use_dst_adjustment is False
    assert args.warmup_start == ""


def test_parse_args_accepts_sr_v2_flags(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_backtest_exit_experiment.py",
            "--input-csv",
            "dummy.csv",
            "--run-id",
            "r_sr",
            "--output-dir",
            "out",
            "--max-holding-bars",
            "10",
            "--sr-v2-enabled",
            "--sr-v2-policy",
            "diagnostic_only",
            "--sr-v2-window-bars",
            "60",
            "--sr-v2-near-threshold-pips",
            "8.5",
            "--sr-v2-pip-size",
            "0.01",
            "--sr-v2-use-atr-normalized",
        ],
    )
    args = parse_args()
    assert args.sr_v2_enabled is True
    assert args.sr_v2_policy == "diagnostic_only"
    assert args.sr_v2_window_bars == 60
    assert args.sr_v2_near_threshold_pips == 8.5
    assert args.sr_v2_pip_size == 0.01
    assert args.sr_v2_use_atr_normalized is True


def test_parse_args_accepts_session_v2_flags(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_backtest_exit_experiment.py",
            "--input-csv",
            "dummy.csv",
            "--run-id",
            "r_session",
            "--output-dir",
            "out",
            "--max-holding-bars",
            "10",
            "--session-v2-enabled",
            "--session-v2-policy",
            "diagnostic_only",
            "--session-v2-timezone",
            "UTC",
            "--session-v2-use-day-of-week",
            "--session-v2-use-hour-bucket",
            "--session-v2-use-dst-adjustment",
        ],
    )
    args = parse_args()
    assert args.session_v2_enabled is True
    assert args.session_v2_policy == "diagnostic_only"
    assert args.session_v2_timezone == "UTC"
    assert args.session_v2_use_day_of_week is True
    assert args.session_v2_use_hour_bucket is True
    assert args.session_v2_use_dst_adjustment is True


def test_parse_args_accepts_warmup_start(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_backtest_exit_experiment.py",
            "--input-csv",
            "dummy.csv",
            "--run-id",
            "r3",
            "--output-dir",
            "out",
            "--max-holding-bars",
            "10",
            "--warmup-start",
            "2024-10-01T00:00:00Z",
            "--start",
            "2024-11-01T00:00:00Z",
            "--end",
            "2024-12-01T00:00:00Z",
        ],
    )
    args = parse_args()
    assert args.warmup_start == "2024-10-01T00:00:00Z"


def test_warmup_start_unspecified_keeps_existing_bar_scope() -> None:
    bars = _bars()
    cfg = BacktestConfig(run_id='warmup_default', max_holding_bars=10)

    def provider(_i, _window):
        return None

    result = run_backtest_exit_experiment(
        bars,
        cfg,
        provider,
        exit_policy='fixed_sl_tp',
    )
    assert result.summary is not None
    assert result.summary.bar_count == len(bars)


def test_warmup_window_is_visible_but_trades_only_in_evaluation_period() -> None:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    bars = [
        PriceBar(t0, 100.0, 100.1, 99.9, 100.0, 0.2, 1.0),  # warmup
        PriceBar(t0 + timedelta(minutes=5), 100.0, 100.2, 99.9, 100.1, 0.2, 1.0),  # warmup
        PriceBar(t0 + timedelta(minutes=10), 100.1, 101.2, 100.0, 101.0, 0.2, 1.0),  # evaluation start
        PriceBar(t0 + timedelta(minutes=15), 101.0, 101.1, 99.8, 100.0, 0.2, 1.0),
    ]
    cfg = BacktestConfig(run_id='warmup_scope', max_holding_bars=10)
    windows: list[list[PriceBar]] = []

    class Provider:
        def __call__(self, i, window):
            windows.append(window)
            if i == 2:
                return EntryEvent(i, 'long', 1.0, 100.0, 101.0, 'entry')
            return None

        def get_last_decision_trace(self):
            return {"htf_v2_enabled": True}

    result = run_backtest_exit_experiment(
        bars,
        cfg,
        Provider(),
        exit_policy='fixed_sl_tp',
        evaluation_start=t0 + timedelta(minutes=10),
        evaluation_end=t0 + timedelta(minutes=20),
    )
    assert windows, "provider should be called on evaluation bars"
    assert windows[0][0].timestamp == t0  # warmup bar is included in first evaluation window
    assert result.summary is not None
    assert result.summary.bar_count == 2
    assert len(result.trades) == 1
    assert result.trades[0].entry_time >= t0 + timedelta(minutes=10)
    assert result.decision_logs
    assert all(
        datetime.fromisoformat(row["timestamp"]) >= t0 + timedelta(minutes=10)
        for row in result.decision_logs
    )


def test_main_wires_htf_v2_config_and_writes_summary_metadata(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    class FakeAdapter:
        def __init__(self, config):
            captured["config"] = config

        def __call__(self, _i, _window):
            return None

        def reset_run_state(self):
            return None

        def get_last_decision_trace(self):
            return {
                "htf_filter_enabled": False,
                "htf_v2_enabled": True,
                "htf_policy": "diagnostic_only",
            }

    monkeypatch.setattr("scripts.run_backtest_exit_experiment.PipelineAdapter", FakeAdapter)
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "price_m5_valid_utc.csv"
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_backtest_exit_experiment.py",
            "--input-csv",
            str(fixture),
            "--run-id",
            "htf_v2_wire",
            "--output-dir",
            str(out_dir),
            "--max-holding-bars",
            "10",
            "--htf-v2-enabled",
            "--htf-v2-policy",
            "diagnostic_only",
            "--htf-v2-h4-ma-fast",
            "20",
            "--htf-v2-h4-ma-slow",
            "50",
            "--htf-v2-h1-ma-fast",
            "20",
            "--htf-v2-slope-window",
            "3",
            "--sr-v2-enabled",
            "--sr-v2-policy",
            "diagnostic_only",
            "--sr-v2-window-bars",
            "64",
            "--sr-v2-near-threshold-pips",
            "9.0",
            "--sr-v2-pip-size",
            "0.01",
            "--sr-v2-use-atr-normalized",
            "--session-v2-enabled",
            "--session-v2-policy",
            "diagnostic_only",
            "--session-v2-timezone",
            "UTC",
            "--session-v2-use-day-of-week",
            "--session-v2-use-hour-bucket",
            "--session-v2-use-dst-adjustment",
        ],
    )
    rc = main()
    assert rc == 0
    cfg = captured["config"]
    assert cfg.htf_v2_enabled is True
    assert cfg.htf_v2_policy == "diagnostic_only"
    assert cfg.htf_v2_h4_ma_fast == 20
    assert cfg.htf_v2_h4_ma_slow == 50
    assert cfg.htf_v2_h1_ma_fast == 20
    assert cfg.htf_v2_slope_window == 3
    assert cfg.sr_v2_enabled is True
    assert cfg.sr_v2_policy == "diagnostic_only"
    assert cfg.sr_v2_window_bars == 64
    assert cfg.sr_v2_near_threshold_pips == 9.0
    assert cfg.sr_v2_pip_size == 0.01
    assert cfg.sr_v2_use_atr_normalized is True
    assert cfg.session_v2_enabled is True
    assert cfg.session_v2_policy == "diagnostic_only"
    assert cfg.session_v2_timezone == "UTC"
    assert cfg.session_v2_use_day_of_week is True
    assert cfg.session_v2_use_hour_bucket is True
    assert cfg.session_v2_use_dst_adjustment is True

    summary_path = out_dir / "backtest_summary.csv"
    with summary_path.open("r", encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))
    assert row["htf_v2_enabled"] in {"True", "true", "1"}
    assert row["htf_v2_policy"] == "diagnostic_only"
    assert row["htf_v2_h4_ma_fast"] == "20"
    assert row["htf_v2_h4_ma_slow"] == "50"
    assert row["htf_v2_h1_ma_fast"] == "20"
    assert row["htf_v2_slope_window"] == "3"
    assert row["sr_v2_enabled"] in {"True", "true", "1"}
    assert row["sr_v2_policy"] == "diagnostic_only"
    assert row["sr_v2_window_bars"] == "64"
    assert row["sr_v2_near_threshold_pips"] == "9.0"
    assert row["sr_v2_pip_size"] == "0.01"
    assert row["sr_v2_use_atr_normalized"] in {"True", "true", "1"}
    assert row["session_v2_enabled"] in {"True", "true", "1"}
    assert row["session_v2_policy"] == "diagnostic_only"
    assert row["session_v2_timezone"] == "UTC"
    assert row["session_v2_use_day_of_week"] in {"True", "true", "1"}
    assert row["session_v2_use_hour_bucket"] in {"True", "true", "1"}
    assert row["session_v2_use_dst_adjustment"] in {"True", "true", "1"}

    metadata = json.loads((out_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["htf_v2_enabled"] is True
    assert metadata["htf_v2_policy"] == "diagnostic_only"
    assert metadata["htf_v2_h4_ma_fast"] == 20
    assert metadata["htf_v2_h4_ma_slow"] == 50
    assert metadata["htf_v2_h1_ma_fast"] == 20
    assert metadata["htf_v2_slope_window"] == 3
    assert metadata["sr_v2_enabled"] is True
    assert metadata["sr_v2_policy"] == "diagnostic_only"
    assert metadata["sr_v2_window_bars"] == 64
    assert metadata["sr_v2_near_threshold_pips"] == 9.0
    assert metadata["sr_v2_pip_size"] == 0.01
    assert metadata["sr_v2_use_atr_normalized"] is True
    assert metadata["session_v2_enabled"] is True
    assert metadata["session_v2_policy"] == "diagnostic_only"
    assert metadata["session_v2_timezone"] == "UTC"
    assert metadata["session_v2_use_day_of_week"] is True
    assert metadata["session_v2_use_hour_bucket"] is True
    assert metadata["session_v2_use_dst_adjustment"] is True


def test_main_writes_warmup_metadata_and_summary_fields(monkeypatch, tmp_path: Path) -> None:
    class FakeAdapter:
        def __init__(self, _config):
            return None

        def __call__(self, _i, _window):
            return None

        def reset_run_state(self):
            return None

        def get_last_decision_trace(self):
            return {
                "htf_v2_enabled": True,
                "htf_policy": "diagnostic_only",
            }

    monkeypatch.setattr("scripts.run_backtest_exit_experiment.PipelineAdapter", FakeAdapter)
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "price_m5_valid_utc.csv"
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_backtest_exit_experiment.py",
            "--input-csv",
            str(fixture),
            "--run-id",
            "warmup_meta",
            "--output-dir",
            str(out_dir),
            "--max-holding-bars",
            "10",
            "--htf-v2-enabled",
            "--htf-v2-policy",
            "diagnostic_only",
            "--warmup-start",
            "2024-01-01T00:00:00Z",
            "--start",
            "2024-01-01T00:10:00Z",
            "--end",
            "2024-01-01T00:20:00Z",
        ],
    )
    rc = main()
    assert rc == 0

    with (out_dir / "backtest_summary.csv").open("r", encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))
    assert row["warmup_start"] == "2024-01-01T00:00:00Z"
    assert row["evaluation_start"] == "2024-01-01T00:10:00Z"
    assert row["evaluation_end"] == "2024-01-01T00:20:00Z"
    assert row["evaluation_bar_count"] == "2"
    assert row["bar_count"] == "2"
    assert row["warmup_bar_count"] == "2"
    assert row["indicator_input_start"] == "2024-01-01T00:00:00+00:00"
    assert row["indicator_input_end"] == "2024-01-01T00:15:00+00:00"

    metadata = json.loads((out_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["warmup_start"] == "2024-01-01T00:00:00Z"
    assert metadata["evaluation_start"] == "2024-01-01T00:10:00Z"
    assert metadata["evaluation_end"] == "2024-01-01T00:20:00Z"
    assert metadata["evaluation_bar_count"] == 2
    assert metadata["warmup_bar_count"] == 2
    assert metadata["indicator_input_start"] == "2024-01-01T00:00:00+00:00"
    assert metadata["indicator_input_end"] == "2024-01-01T00:15:00+00:00"
