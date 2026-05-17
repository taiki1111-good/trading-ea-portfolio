from src.risk_filter.types import SpreadFilterConfig, SpreadFilterResult


class SpreadFilter:
    @staticmethod
    def check(spread: float, spread_filter_config: SpreadFilterConfig) -> SpreadFilterResult:
        if spread < 0:
            return SpreadFilterResult(
                spread_ok=False,
                spread_filter_reason=f"invalid spread: {spread} (must be non-negative)",
            )

        if spread <= spread_filter_config.max_spread_pips:
            return SpreadFilterResult(
                spread_ok=True,
                spread_filter_reason=f"spread is within allowed maximum {spread_filter_config.max_spread_pips} pips",
            )

        return SpreadFilterResult(
            spread_ok=False,
            spread_filter_reason=f"spread {spread} exceeds max allowed {spread_filter_config.max_spread_pips} pips",
        )
