import pytest

from src.evaluator import SignalAnalyzer


def test_signal_analyzer_groups_by_signal_type():
    trade_logs = [
        {"signal_type": "long_entry", "pnl": 5.0},
        {"signal_type": "long_entry", "pnl": -3.0},
        {"signal_type": "short_entry", "pnl": 2.0},
        {"signal_type": None, "pnl": 1.0},
    ]

    stats, warnings = SignalAnalyzer.analyze(trade_logs)

    assert stats["long_entry"].count == 2
    assert stats["long_entry"].win_count == 1
    assert stats["short_entry"].count == 1
    assert stats["unknown"].count == 1
    assert any("signal_type missing" in warning for warning in warnings)
