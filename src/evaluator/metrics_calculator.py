from __future__ import annotations

from typing import Any, Iterable, List, Optional

from .types import MetricsResult


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


def _calculate_max_drawdown(values: List[float]) -> float:
    peak = 0.0
    cumulative = 0.0
    max_dd = 0.0
    for value in values:
        cumulative += value
        peak = max(peak, cumulative)
        max_dd = max(max_dd, peak - cumulative)
    return max_dd


class MetricsCalculator:
    @staticmethod
    def calculate(trade_logs: Iterable[Any]) -> MetricsResult:
        trade_list = list(trade_logs)
        trade_count = len(trade_list)
        pnl_values: List[float] = []

        for record in trade_list:
            pnl = _extract_pnl(record)
            if pnl is not None:
                pnl_values.append(pnl)

        if not pnl_values:
            return MetricsResult(
                trade_count=trade_count,
                win_rate=None,
                average_pnl=None,
                profit_factor=None,
                max_drawdown=None,
                evaluation_reason="No pnl values available to compute metrics",
                evaluation_warnings=["pnl or realized_pnl missing in trade logs"],
            )

        gross_profit = sum(value for value in pnl_values if value > 0)
        gross_loss = sum(value for value in pnl_values if value < 0)
        win_count = sum(1 for value in pnl_values if value > 0)
        average_pnl = sum(pnl_values) / len(pnl_values)
        win_rate = win_count / len(pnl_values) if pnl_values else 0.0
        profit_factor = None
        if gross_loss < 0:
            profit_factor = gross_profit / abs(gross_loss)

        max_drawdown = _calculate_max_drawdown(pnl_values)

        return MetricsResult(
            trade_count=trade_count,
            win_rate=win_rate,
            average_pnl=average_pnl,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            evaluation_reason="Metrics computed from available pnl values",
            evaluation_warnings=[],
        )
