from __future__ import annotations

from datetime import datetime, timezone

from scripts.analyze_counterfactual_exits import PriceBar
from scripts.analyze_counterfactual_exits import TradeRecord
from scripts.replay_counterfactual_exits_position_aware import run_replay


def _bars_for_overlap() -> tuple[list[PriceBar], dict[datetime, int]]:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100, 101.6, 99.9, 100.8),
        PriceBar(datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), 100.8, 101.4, 99.8, 100.7),
        PriceBar(datetime(2024, 1, 1, 0, 15, tzinfo=timezone.utc), 100.7, 100.8, 99.7, 99.8),
        PriceBar(datetime(2024, 1, 1, 0, 20, tzinfo=timezone.utc), 99.8, 100.2, 99.2, 99.4),
    ]
    return bars, {b.timestamp: i for i, b in enumerate(bars)}


def _trades_for_overlap() -> list[TradeRecord]:
    return [
        TradeRecord(0, "long_entry", "long", datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 99, 101, datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), "take_profit", 1),
        TradeRecord(1, "short_entry", "short", datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100.8, 101.8, 99.8, datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), "take_profit", 1),
        TradeRecord(2, "short_entry", "short", datetime(2024, 1, 1, 0, 15, tzinfo=timezone.utc), 99.8, 100.8, 98.8, datetime(2024, 1, 1, 0, 20, tzinfo=timezone.utc), "take_profit", 1),
    ]


def test_skip_entry_when_open_position_exists_for_trailing() -> None:
    bars, idx = _bars_for_overlap()
    rows, summary = run_replay(_trades_for_overlap(), bars, idx, "simple_trailing_after_1R", 3)
    skipped = [r for r in rows if r["skipped_reason"] == "skipped_due_to_open_position"]
    assert len(skipped) >= 1
    assert summary["skipped_due_to_open_position_count"] >= 1


def test_accept_next_entry_after_exit() -> None:
    bars, idx = _bars_for_overlap()
    rows, _ = run_replay(_trades_for_overlap(), bars, idx, "simple_trailing_after_1R", 3)
    accepted = [r for r in rows if r["accepted_entry"]]
    assert len(accepted) >= 2


def test_accepted_plus_skipped_equals_original() -> None:
    bars, idx = _bars_for_overlap()
    _, summary = run_replay(_trades_for_overlap(), bars, idx, "simple_trailing_after_1R", 3)
    assert summary["accepted_plus_skipped_match"] is True


def test_no_position_overlap_in_replay() -> None:
    bars, idx = _bars_for_overlap()
    _, summary = run_replay(_trades_for_overlap(), bars, idx, "simple_trailing_after_1R", 3)
    assert summary["position_overlap_detected"] is False


def test_baseline_rule_keeps_trade_count_alignment() -> None:
    bars, idx = _bars_for_overlap()
    _, summary = run_replay(_trades_for_overlap(), bars, idx, "baseline_fixed_exit", 3)
    assert summary["original_trade_count"] == 3
    assert summary["accepted_trade_count"] + summary["skipped_entry_count"] == 3


def test_trailing_can_cause_more_skips_than_baseline() -> None:
    bars, idx = _bars_for_overlap()
    _, trailing = run_replay(_trades_for_overlap(), bars, idx, "simple_trailing_after_1R", 3)
    _, baseline = run_replay(_trades_for_overlap(), bars, idx, "baseline_fixed_exit", 3)
    assert trailing["skipped_due_to_open_position_count"] >= baseline["skipped_due_to_open_position_count"]


def test_long_same_bar_activation_and_stop_is_ambiguous() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100, 101.2, 99.0, 100.4),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    trades = [TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100, 99, 103, bars[1].timestamp, "stop_loss", -1)]
    rows, summary = run_replay(trades, bars, idx, "simple_trailing_after_1R_conservative", 6)
    assert rows[0]["intrabar_ambiguous"] is True
    assert rows[0]["activation_and_stop_same_bar"] is True
    assert summary["intrabar_ambiguous_count"] == 1


def test_short_same_bar_activation_and_stop_is_ambiguous() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100, 101.0, 98.8, 99.5),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    trades = [TradeRecord(0, "short_entry", "short", bars[0].timestamp, 100, 101, 97, bars[1].timestamp, "stop_loss", -1)]
    rows, summary = run_replay(trades, bars, idx, "simple_trailing_after_1R_conservative", 6)
    assert rows[0]["intrabar_ambiguous"] is True
    assert rows[0]["activation_and_stop_same_bar"] is True
    assert summary["intrabar_ambiguous_count"] == 1


def test_next_bar_activation_does_not_trigger_trailing_on_activation_bar() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100, 101.2, 100.05, 100.8),
        PriceBar(datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), 100.8, 100.9, 98.9, 99.2),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    trades = [TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100, 99, 103, bars[2].timestamp, "stop_loss", -1)]
    rows, _ = run_replay(trades, bars, idx, "simple_trailing_after_1R_next_bar_activation", 6)
    assert rows[0]["replay_exit_time"] == bars[2].timestamp.isoformat()


def test_conservative_rule_does_not_process_ambiguous_case_optimistically() -> None:
    bars = [
        PriceBar(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 100, 100, 100, 100),
        PriceBar(datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 100, 101.2, 99.0, 100.4),
    ]
    idx = {b.timestamp: i for i, b in enumerate(bars)}
    trades = [TradeRecord(0, "long_entry", "long", bars[0].timestamp, 100, 99, 103, bars[1].timestamp, "stop_loss", -1)]
    rows, summary = run_replay(trades, bars, idx, "simple_trailing_after_1R_conservative", 6)
    assert rows[0]["conservative_exit_applied"] is True
    assert rows[0]["replay_exit_reason"] == "stop_loss"
    assert summary["conservative_exit_applied_count"] == 1


def test_max_holding_bars_10_runs() -> None:
    bars, idx = _bars_for_overlap()
    _, summary = run_replay(_trades_for_overlap(), bars, idx, "simple_trailing_after_1R_next_bar_activation", 10)
    assert summary["max_holding_bars"] <= 10
