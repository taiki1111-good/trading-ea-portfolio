from __future__ import annotations

from typing import Dict, Iterable, List

from .types import (
    EvaluatorResult,
    FilterStatsResult,
    MetricsResult,
    SignalStatsResult,
    StructureStatsResult,
    SummaryReport,
)


class ReportAssembler:
    @staticmethod
    def assemble(
        metrics_result: MetricsResult,
        structure_stats: Dict[str, StructureStatsResult],
        filter_stats: Dict[str, FilterStatsResult],
        signal_stats: Dict[str, SignalStatsResult],
        warnings: Iterable[str] | None = None,
    ) -> EvaluatorResult:
        evaluation_warnings = list(warnings) if warnings is not None else []
        summary_report = SummaryReport(
            metrics=metrics_result,
            structure_type_stats=structure_stats,
            filter_hit_stats=filter_stats,
            signal_type_stats=signal_stats,
            evaluation_warnings=evaluation_warnings,
        )
        return EvaluatorResult(
            summary_report=summary_report,
            metrics_result=metrics_result,
            structure_stats=structure_stats,
            filter_stats=filter_stats,
            signal_stats=signal_stats,
            evaluation_warnings=evaluation_warnings,
        )
