from src.data.types import PriceFrame

from .types import SwingConfig, SwingPoint, SwingResult


class SwingExtractor:
    @staticmethod
    def extract(ltf_price_frame: PriceFrame, swing_config: SwingConfig | None = None) -> SwingResult:
        config = swing_config or SwingConfig()
        window = max(1, int(config.window))

        if not isinstance(ltf_price_frame, list) or len(ltf_price_frame) < (window + 1):
            return SwingResult(
                swing_points=[],
                swing_reason=(
                    f"insufficient bars for swing extraction: require at least {window + 1}, "
                    f"got {len(ltf_price_frame) if isinstance(ltf_price_frame, list) else 0}"
                ),
            )

        swing_points: list[SwingPoint] = []

        if config.causal:
            # Causal mode uses only confirmed bars up to current index (no future reference).
            for idx in range(window, len(ltf_price_frame)):
                current = ltf_price_frame[idx]
                history = ltf_price_frame[idx - window:idx]

                if all(current.high > bar.high for bar in history):
                    swing_points.append(
                        SwingPoint(timestamp=current.timestamp, price=current.high, swing_type="high")
                    )
                if all(current.low < bar.low for bar in history):
                    swing_points.append(
                        SwingPoint(timestamp=current.timestamp, price=current.low, swing_type="low")
                    )
        else:
            if len(ltf_price_frame) < (window * 2 + 1):
                return SwingResult(
                    swing_points=[],
                    swing_reason=(
                        f"insufficient bars for non-causal swing extraction: require at least {window * 2 + 1}, "
                        f"got {len(ltf_price_frame)}"
                    ),
                )
            for idx in range(window, len(ltf_price_frame) - window):
                current = ltf_price_frame[idx]
                left = ltf_price_frame[idx - window:idx]
                right = ltf_price_frame[idx + 1:idx + window + 1]

                if all(current.high > bar.high for bar in left + right):
                    swing_points.append(
                        SwingPoint(timestamp=current.timestamp, price=current.high, swing_type="high")
                    )
                if all(current.low < bar.low for bar in left + right):
                    swing_points.append(
                        SwingPoint(timestamp=current.timestamp, price=current.low, swing_type="low")
                    )

        if not swing_points:
            return SwingResult(
                swing_points=[],
                swing_reason=(
                    f"no swing points detected (window={window}, causal={config.causal})"
                ),
            )

        return SwingResult(
            swing_points=swing_points,
            swing_reason=(
                f"extracted {len(swing_points)} swing points (window={window}, causal={config.causal})"
            ),
        )
