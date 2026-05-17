from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .types import SignalStatsResult


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


class SignalAnalyzer:
    @staticmethod
    def analyze(logs: Iterable[Any]) -> tuple[Dict[str, SignalStatsResult], List[str]]:
        stats: Dict[str, SignalStatsResult] = {}
        warnings: List[str] = []

        valid_pnl_by_signal: Dict[str, int] = {}

        for record in logs:
            signal_type = _get_value(record, "signal_type")
            if not signal_type:
                signal_type = "unknown"
                warnings.append("signal_type missing or empty, counted as unknown")

            pnl = _extract_pnl(record)
            bucket = stats.setdefault(
                signal_type,
                SignalStatsResult(signal_type=signal_type),
            )
            bucket.count += 1
            if pnl is not None:
                bucket.total_pnl += pnl
                valid_pnl_by_signal[signal_type] = (
                    valid_pnl_by_signal.get(signal_type, 0) + 1
                )
                if pnl > 0:
                    bucket.win_count += 1

        for bucket in stats.values():
            valid_count = valid_pnl_by_signal.get(bucket.signal_type, 0)
            bucket.average_pnl = (
                bucket.total_pnl / valid_count if valid_count > 0 else None
            )

        return stats, warnings
