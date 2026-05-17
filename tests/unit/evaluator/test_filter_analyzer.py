import pytest

from src.evaluator import FilterAnalyzer


def test_filter_analyzer_counts_filter_reasons():
    event_logs = [
        {"filter_reason": "spread_too_high"},
        {"filter_reason": "risk_limit"},
        {"filter_reason": "spread_too_high"},
        {"filter_reason": None},
    ]

    stats, warnings = FilterAnalyzer.analyze(event_logs)

    assert stats["spread_too_high"].count == 2
    assert stats["risk_limit"].count == 1
    assert stats["unknown"].count == 1
    assert any("filter_reason missing" in warning for warning in warnings)


def test_filter_analyzer_category_analysis_counts_canonical_categories() -> None:
    event_logs = [
        {"filter_reason": "all risk filters passed"},
        {"filter_reason": "risk_contract_invalid: entry_signal_false | invalid_lot: fixed_lot=0"},
    ]

    stats, warnings = FilterAnalyzer.analyze_by_category(event_logs)

    assert stats["all_risk_filters_passed"].count == 1
    assert stats["risk_contract_invalid"].count == 1
    assert stats["invalid_lot"].count == 1
    assert "none" not in stats
    assert not warnings


def test_filter_analyzer_category_analysis_treats_missing_as_unknown() -> None:
    event_logs = [
        {"filter_reason": None},
        {"filter_reason": " "},
        {},
    ]

    stats, warnings = FilterAnalyzer.analyze_by_category(event_logs)

    assert stats["unknown"].count == 3
    assert "none" not in stats
    assert len(warnings) == 3
