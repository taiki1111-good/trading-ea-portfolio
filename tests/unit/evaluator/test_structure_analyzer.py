import pytest

from src.evaluator import StructureAnalyzer


def test_structure_analyzer_groups_by_structure_type():
    decision_logs = [
        {"structure_type": "breakout", "pnl": 10.0},
        {"structure_type": "breakout", "pnl": -2.0},
        {"structure_type": "triangle", "pnl": 4.0},
        {"structure_type": None, "pnl": 1.0},
    ]

    stats, warnings = StructureAnalyzer.analyze(decision_logs)

    assert stats["breakout"].count == 2
    assert stats["breakout"].win_count == 1
    assert stats["breakout"].average_pnl == pytest.approx((10.0 + -2.0) / 2)
    assert stats["triangle"].count == 1
    assert stats["unknown"].count == 1
    assert any("structure_type missing" in warning for warning in warnings)
