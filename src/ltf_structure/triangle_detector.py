from .types import TriangleConfig, TriangleResult


class TriangleDetector:
    @staticmethod
    def detect(
        ltf_price_frame=None,
        swing_points=None,
        triangle_config: TriangleConfig | None = None,
    ) -> TriangleResult:
        _ = triangle_config or TriangleConfig()
        # TODO(TBD): move real triangle detection to experiments flow before any main adoption.
        return TriangleResult(
            triangle_flag=False,
            triangle_direction_hint="neutral",
            triangle_reason="triangle_break is reserved for experiments in initial main",
        )
