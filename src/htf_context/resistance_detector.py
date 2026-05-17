from .types import HTF_TREND_UP, PriceFrame, ResistanceConfig, ResistanceResult


class ResistanceDetector:
    @staticmethod
    def detect(htf_price_frame: PriceFrame, resistance_config: ResistanceConfig | None = None) -> ResistanceResult:
        config = resistance_config or ResistanceConfig()
        if not isinstance(htf_price_frame, list) or not htf_price_frame:
            return ResistanceResult(
                htf_resistance_ok=False,
                resistance_reason="insufficient htf_price_frame length for resistance detection",
            )

        lookback = min(config.lookback, len(htf_price_frame))
        recent_bars = htf_price_frame[-lookback:]
        recent_high = max(bar.high for bar in recent_bars)
        current_close = recent_bars[-1].close
        distance = recent_high - current_close
        ok = distance >= config.min_distance
        reason = (
            f"recent_high {recent_high:.6f}, current_close {current_close:.6f}, "
            f"distance {distance:.6f}, min_distance {config.min_distance:.6f}"
        )
        return ResistanceResult(htf_resistance_ok=ok, resistance_reason=reason)
