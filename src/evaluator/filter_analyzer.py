from __future__ import annotations

from typing import Any, Dict, Iterable, List

from src.risk_filter.reason_catalog import normalize_reason_categories

from .types import FilterStatsResult


def _get_value(record: Any, key: str) -> Any:
    if isinstance(record, dict):
        return record.get(key)
    return getattr(record, key, None)


class FilterAnalyzer:
    @staticmethod
    def analyze(logs: Iterable[Any]) -> tuple[Dict[str, FilterStatsResult], List[str]]:
        stats: Dict[str, FilterStatsResult] = {}
        warnings: List[str] = []

        for record in logs:
            filter_reason = _get_value(record, "filter_reason")
            if not filter_reason:
                filter_reason = "unknown"
                warnings.append("filter_reason missing or empty, counted as unknown")

            bucket = stats.setdefault(
                filter_reason,
                FilterStatsResult(filter_reason=filter_reason),
            )
            bucket.count += 1

        return stats, warnings

    @staticmethod
    def analyze_by_category(logs: Iterable[Any]) -> tuple[Dict[str, FilterStatsResult], List[str]]:
        stats: Dict[str, FilterStatsResult] = {}
        warnings: List[str] = []

        for record in logs:
            raw_filter_reason = _get_value(record, "filter_reason")
            reason_text = ""
            if raw_filter_reason is not None:
                reason_text = str(raw_filter_reason).strip()
                if reason_text.lower() == "none":
                    reason_text = ""

            categories = normalize_reason_categories(reason_text)
            if not categories:
                categories = ["unknown"]
                warnings.append("filter_reason missing or empty, counted as unknown")

            for category in categories:
                bucket = stats.setdefault(
                    category,
                    FilterStatsResult(filter_reason=category),
                )
                bucket.count += 1

        return stats, warnings
