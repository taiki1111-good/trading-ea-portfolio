from src.evaluator import (
    FilterStatsResult,
    MetricsResult,
    ReportAssembler,
    SignalStatsResult,
    StructureStatsResult,
)


def test_report_assembler_returns_summary_report():
    metrics = MetricsResult(
        trade_count=3,
        win_rate=0.66,
        average_pnl=2.0,
        profit_factor=1.5,
        max_drawdown=1.0,
    )
    structure_stats = {"breakout": StructureStatsResult(structure_type="breakout", count=2, win_count=1, total_pnl=5.0, average_pnl=2.5)}
    filter_stats = {"spread_too_high": FilterStatsResult(filter_reason="spread_too_high", count=1)}
    signal_stats = {"long_entry": SignalStatsResult(signal_type="long_entry", count=2, win_count=1, total_pnl=3.0, average_pnl=1.5)}

    result = ReportAssembler.assemble(
        metrics_result=metrics,
        structure_stats=structure_stats,
        filter_stats=filter_stats,
        signal_stats=signal_stats,
        warnings=["sample warning"],
    )

    assert result.summary_report.metrics.trade_count == 3
    assert result.summary_report.structure_type_stats["breakout"].count == 2
    assert result.summary_report.filter_hit_stats["spread_too_high"].count == 1
    assert result.summary_report.signal_type_stats["long_entry"].count == 2
    assert result.evaluation_warnings == ["sample warning"]
