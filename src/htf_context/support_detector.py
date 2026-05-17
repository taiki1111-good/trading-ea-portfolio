from .types import PriceFrame, SupportConfig, SupportResult


class SupportDetector:
    @staticmethod
    def detect(htf_price_frame: PriceFrame, support_config: SupportConfig | None = None) -> SupportResult:
        config = support_config or SupportConfig()
        if not isinstance(htf_price_frame, list) or not htf_price_frame:
            return SupportResult(
                htf_support_ok=False,
                support_reason="insufficient htf_price_frame length for support detection",
            )

        lookback = min(config.lookback, len(htf_price_frame))
        recent_bars = htf_price_frame[-lookback:]
        recent_low = min(bar.low for bar in recent_bars)
        current_close = recent_bars[-1].close
        distance = current_close - recent_low
        ok = distance >= config.min_distance
        reason = (
            f"recent_low {recent_low:.6f}, current_close {current_close:.6f}, "
            f"distance {distance:.6f}, min_distance {config.min_distance:.6f}"
        )
        return SupportResult(htf_support_ok=ok, support_reason=reason)
