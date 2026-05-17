from .types import HTF_TREND_DOWN, HTF_TREND_NEUTRAL, HTF_TREND_UP, PriceFrame, TrendConfig, TrendResult


class TrendDetector:
    @staticmethod
    def detect(htf_price_frame: PriceFrame, trend_config: TrendConfig | None = None) -> TrendResult:
        config = trend_config or TrendConfig()
        if not isinstance(htf_price_frame, list) or len(htf_price_frame) < 2:
            return TrendResult(
                htf_trend_dir=HTF_TREND_NEUTRAL,
                htf_trend_strength=0.0,
                trend_reason="insufficient htf_price_frame length for trend detection",
            )

        lookback = min(config.lookback, len(htf_price_frame))
        recent_bars = htf_price_frame[-lookback:]
        first_close = recent_bars[0].close
        last_close = recent_bars[-1].close
        high = max(bar.high for bar in recent_bars)
        low = min(bar.low for bar in recent_bars)
        price_range = high - low

        if price_range <= 0:
            return TrendResult(
                htf_trend_dir=HTF_TREND_NEUTRAL,
                htf_trend_strength=0.0,
                trend_reason="price_range is zero or negative; cannot determine trend",
            )

        strength = abs(last_close - first_close) / price_range
        strength = max(0.0, min(strength, 1.0))

        if strength < config.min_strength:
            return TrendResult(
                htf_trend_dir=HTF_TREND_NEUTRAL,
                htf_trend_strength=strength,
                trend_reason=(
                    f"trend strength {strength:.3f} below min_strength {config.min_strength:.3f}"
                ),
            )

        if last_close > first_close:
            direction = HTF_TREND_UP
            reason = (
                f"close rose from {first_close:.6f} to {last_close:.6f}; strength {strength:.3f}"
            )
        elif last_close < first_close:
            direction = HTF_TREND_DOWN
            reason = (
                f"close fell from {first_close:.6f} to {last_close:.6f}; strength {strength:.3f}"
            )
        else:
            direction = HTF_TREND_NEUTRAL
            reason = "no close change over lookback period"

        return TrendResult(
            htf_trend_dir=direction,
            htf_trend_strength=strength,
            trend_reason=reason,
        )
