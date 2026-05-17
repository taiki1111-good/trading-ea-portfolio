import pytest

from src.evaluator import (
    FilterAnalyzer,
    MetricsCalculator,
    ReportAssembler,
    SignalAnalyzer,
    StructureAnalyzer,
)
from src.logger import DecisionLogger, EventLogger, TradeLogger


def test_logger_to_evaluator_integration_aggregates_logs():
    trade_logs = [
        TradeLogger.log(order_result="filled", signal_type="long_entry", pnl=10.0),
        TradeLogger.log(order_result="filled", signal_type="long_entry", pnl=-5.0),
        TradeLogger.log(order_result="filled", signal_type="short_entry", pnl=3.0),
    ]
    decision_logs = [
        DecisionLogger.log(structure_type="breakout", signal_type="long_entry"),
        DecisionLogger.log(structure_type="breakout", signal_type="long_entry"),
        DecisionLogger.log(structure_type="reversal", signal_type="short_entry"),
    ]
    event_logs = [
        EventLogger.log(filter_reason="spread_too_high"),
        EventLogger.log(filter_reason="risk_limit"),
        EventLogger.log(filter_reason="spread_too_high"),
    ]

    metrics_result = MetricsCalculator.calculate(trade_logs)
    structure_stats, structure_warnings = StructureAnalyzer.analyze(
        [
            {"structure_type": log.structure_type, "pnl": 0.0}
            for log in decision_logs
        ]
    )
    filter_stats, filter_warnings = FilterAnalyzer.analyze(event_logs)
    signal_stats, signal_warnings = SignalAnalyzer.analyze(trade_logs)
    evaluator_result = ReportAssembler.assemble(
        metrics_result=metrics_result,
        structure_stats=structure_stats,
        filter_stats=filter_stats,
        signal_stats=signal_stats,
        warnings=[*structure_warnings, *filter_warnings, *signal_warnings],
    )

    assert metrics_result.trade_count == 3
    assert metrics_result.win_rate == pytest.approx(2.0 / 3.0)
    assert metrics_result.average_pnl == pytest.approx((10.0 - 5.0 + 3.0) / 3)
    assert evaluator_result.summary_report.structure_type_stats["breakout"].count == 2
    assert evaluator_result.summary_report.filter_hit_stats["spread_too_high"].count == 2
    assert evaluator_result.summary_report.signal_type_stats["long_entry"].count == 2
    assert "unknown" not in evaluator_result.summary_report.filter_hit_stats
