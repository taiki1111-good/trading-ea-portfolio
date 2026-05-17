from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .types import StructureStatsResult


def _get_value(record: Any, key: str) -> Any:
    if isinstance(record, dict):
        return record.get(key)
    return getattr(record, key, None)


def _extract_pnl(record: Any) -> Optional[float]:
    for field_name in ("realized_pnl", "pnl"):
        value = _get_value(record, field_name)
        if isinstance(value, (int, float)):
            return float(value)
    return None


class StructureAnalyzer:
    @staticmethod
    def analyze(logs: Iterable[Any]) -> tuple[Dict[str, StructureStatsResult], List[str]]:
        stats: Dict[str, StructureStatsResult] = {}
        warnings: List[str] = []

        valid_pnl_by_structure: Dict[str, int] = {}

        for record in logs:
            structure_type = _get_value(record, "structure_type")
            if not structure_type:
                structure_type = "unknown"
                warnings.append("structure_type missing or empty, counted as unknown")

            pnl = _extract_pnl(record)
            bucket = stats.setdefault(
                structure_type,
                StructureStatsResult(structure_type=structure_type),
            )
            bucket.count += 1
            if pnl is not None:
                bucket.total_pnl += pnl
                valid_pnl_by_structure[structure_type] = (
                    valid_pnl_by_structure.get(structure_type, 0) + 1
                )
                if pnl > 0:
                    bucket.win_count += 1

        for bucket in stats.values():
            valid_count = valid_pnl_by_structure.get(bucket.structure_type, 0)
            if valid_count > 0:
                bucket.average_pnl = bucket.total_pnl / valid_count
            else:
                bucket.average_pnl = None

        return stats, warnings
