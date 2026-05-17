from .types import WaveConfig, WaveResult, WAVE_DIRECTION_NEUTRAL, WAVE_PHASE_UNKNOWN
from .types import SwingPoint


class WaveClassifier:
    @staticmethod
    def classify(swing_points: list[SwingPoint], wave_config: WaveConfig | None = None) -> WaveResult:
        config = wave_config or WaveConfig()

        if not isinstance(swing_points, list):
            return WaveResult(
                wave_phase=WAVE_PHASE_UNKNOWN,
                wave_direction=WAVE_DIRECTION_NEUTRAL,
                wave_reason="swing_points must be a list",
            )

        if len(swing_points) < max(3, config.min_swing_points):
            return WaveResult(
                wave_phase=WAVE_PHASE_UNKNOWN,
                wave_direction=WAVE_DIRECTION_NEUTRAL,
                wave_reason=(
                    f"insufficient swing points for wave classification: {len(swing_points)} found"
                ),
            )

        first, second, third = swing_points[-3], swing_points[-2], swing_points[-1]

        if (
            first.swing_type == "low"
            and second.swing_type == "high"
            and third.swing_type == "low"
            and third.price > first.price
        ):
            return WaveResult(
                wave_phase="third",
                wave_direction="long",
                wave_reason=(
                    "third-wave long candidate detected: "
                    f"low({first.price:.6f}) -> high({second.price:.6f}) -> higher low({third.price:.6f})"
                ),
            )

        if (
            first.swing_type == "high"
            and second.swing_type == "low"
            and third.swing_type == "high"
            and third.price < first.price
        ):
            return WaveResult(
                wave_phase="third",
                wave_direction="short",
                wave_reason=(
                    "third-wave short candidate detected: "
                    f"high({first.price:.6f}) -> low({second.price:.6f}) -> lower high({third.price:.6f})"
                ),
            )

        return WaveResult(
            wave_phase=WAVE_PHASE_UNKNOWN,
            wave_direction=WAVE_DIRECTION_NEUTRAL,
            wave_reason="no third-wave candidate pattern found in latest three swing points",
        )
