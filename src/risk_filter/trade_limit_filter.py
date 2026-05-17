from src.risk_filter.types import TradeLimitConfig, TradeLimitFilterResult


class TradeLimitFilter:
    @staticmethod
    def check(daily_trade_count: int, losing_streak: int, trade_limit_config: TradeLimitConfig) -> TradeLimitFilterResult:
        max_trade_reached_flag = daily_trade_count >= trade_limit_config.max_daily_trades
        if max_trade_reached_flag:
            return TradeLimitFilterResult(
                limit_ok=False,
                limit_filter_reason=(
                    f"daily trade count {daily_trade_count} reached limit {trade_limit_config.max_daily_trades}"
                ),
                max_trade_reached_flag=True,
            )

        if losing_streak >= trade_limit_config.max_losing_streak:
            return TradeLimitFilterResult(
                limit_ok=False,
                limit_filter_reason=(
                    f"losing streak {losing_streak} reached limit {trade_limit_config.max_losing_streak}"
                ),
                max_trade_reached_flag=False,
            )

        return TradeLimitFilterResult(
            limit_ok=True,
            limit_filter_reason=(
                f"trade limits within allowed thresholds: daily_trade_count={daily_trade_count}, losing_streak={losing_streak}"
            ),
            max_trade_reached_flag=False,
        )
