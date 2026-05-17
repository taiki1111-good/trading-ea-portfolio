from src.data.types import PriceFrame

from .types import BreakoutConfig, BreakoutResult, BREAKOUT_DIRECTION_NEUTRAL, SwingPoint


class BreakoutDetector:
    @staticmethod
    def detect(
        ltf_price_frame: PriceFrame,
        swing_points: list[SwingPoint],
        breakout_config: BreakoutConfig | None = None,
    ) -> BreakoutResult:
        config = breakout_config or BreakoutConfig()

        if not isinstance(ltf_price_frame, list) or not ltf_price_frame:
            return BreakoutResult(
                breakout_flag=False,
                breakout_direction=BREAKOUT_DIRECTION_NEUTRAL,
                breakout_level=0.0,
                breakout_reason="missing ltf_price_frame for breakout detection",
            )

        if not isinstance(swing_points, list) or not swing_points:
            return BreakoutResult(
                breakout_flag=False,
                breakout_direction=BREAKOUT_DIRECTION_NEUTRAL,
                breakout_level=0.0,
                breakout_reason="missing swing_points for breakout detection",
            )

        current_bar = ltf_price_frame[-1]
        latest_close = current_bar.close

        prior_swing_points = [point for point in swing_points if point.timestamp < current_bar.timestamp]
        recent_swing_high = next(
            (point.price for point in reversed(prior_swing_points) if point.swing_type == "high"),
            None,
        )
        recent_swing_low = next(
            (point.price for point in reversed(prior_swing_points) if point.swing_type == "low"),
            None,
        )

        if recent_swing_high is None and recent_swing_low is None:
            return BreakoutResult(
                breakout_flag=False,
                breakout_direction=BREAKOUT_DIRECTION_NEUTRAL,
                breakout_level=0.0,
                breakout_reason=(
                    "no prior swing high/low before current bar timestamp; breakout unavailable"
                ),
            )

        long_breakout = recent_swing_high is not None and latest_close > recent_swing_high
        short_breakout = recent_swing_low is not None and latest_close < recent_swing_low

        if long_breakout and short_breakout:
            return BreakoutResult(
                breakout_flag=False,
                breakout_direction=BREAKOUT_DIRECTION_NEUTRAL,
                breakout_level=0.0,
                breakout_reason=(
                    "conflicting breakout signals detected against prior swing levels; fallback to neutral for safety"
                ),
            )

        if long_breakout:
            return BreakoutResult(
                breakout_flag=True,
                breakout_direction="long",
                breakout_level=float(recent_swing_high),
                breakout_reason=(
                    f"close-based long breakout: latest close {latest_close:.6f} > recent swing high {recent_swing_high:.6f}"
                ),
            )

        if short_breakout:
            return BreakoutResult(
                breakout_flag=True,
                breakout_direction="short",
                breakout_level=float(recent_swing_low),
                breakout_reason=(
                    f"close-based short breakout: latest close {latest_close:.6f} < recent swing low {recent_swing_low:.6f}"
                ),
            )

        mode = "close" if config.use_close else "close"
        return BreakoutResult(
            breakout_flag=False,
            breakout_direction=BREAKOUT_DIRECTION_NEUTRAL,
            breakout_level=0.0,
            breakout_reason=(
                f"no {mode}-based breakout detected against prior swing levels"
            ),
        )
