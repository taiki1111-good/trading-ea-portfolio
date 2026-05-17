from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def _to_dict(value: Any) -> Dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return value
    return asdict(value)


@dataclass
class MetricsResult:
    trade_count: int = 0
    win_rate: Optional[float] = None
    average_pnl: Optional[float] = None
    profit_factor: Optional[float] = None
    max_drawdown: Optional[float] = None
    evaluation_reason: str = ""
    evaluation_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructureStatsResult:
    structure_type: str = "unknown"
    count: int = 0
    win_count: int = 0
    total_pnl: float = 0.0
    average_pnl: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FilterStatsResult:
    filter_reason: str = "unknown"
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SignalStatsResult:
    signal_type: str = "unknown"
    count: int = 0
    win_count: int = 0
    total_pnl: float = 0.0
    average_pnl: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SummaryReport:
    metrics: MetricsResult
    structure_type_stats: Dict[str, StructureStatsResult]
    filter_hit_stats: Dict[str, FilterStatsResult]
    signal_type_stats: Dict[str, SignalStatsResult]
    evaluation_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics.to_dict(),
            "structure_type_stats": {k: v.to_dict() for k, v in self.structure_type_stats.items()},
            "filter_hit_stats": {k: v.to_dict() for k, v in self.filter_hit_stats.items()},
            "signal_type_stats": {k: v.to_dict() for k, v in self.signal_type_stats.items()},
            "evaluation_warnings": list(self.evaluation_warnings),
        }


@dataclass
class EvaluatorResult:
    summary_report: SummaryReport
    metrics_result: MetricsResult
    structure_stats: Dict[str, StructureStatsResult]
    filter_stats: Dict[str, FilterStatsResult]
    signal_stats: Dict[str, SignalStatsResult]
    evaluation_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_report": self.summary_report.to_dict(),
            "metrics_result": self.metrics_result.to_dict(),
            "structure_stats": {k: v.to_dict() for k, v in self.structure_stats.items()},
            "filter_stats": {k: v.to_dict() for k, v in self.filter_stats.items()},
            "signal_stats": {k: v.to_dict() for k, v in self.signal_stats.items()},
            "evaluation_warnings": list(self.evaluation_warnings),
        }
