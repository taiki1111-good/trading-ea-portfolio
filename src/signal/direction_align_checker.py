from src.htf_context.types import HTF_BIAS_LONG, HTF_BIAS_SHORT, HTFBias
from src.ltf_structure.types import StructureDirection

from .types import DirectionAlignResult


class DirectionAlignChecker:
    @staticmethod
    def check(
        htf_bias: HTFBias,
        structure_direction: StructureDirection,
        htf_context_reason: str = "",
        pattern_reason: str = "",
    ) -> DirectionAlignResult:
        reasons: list[str] = []
        if htf_context_reason:
            reasons.append(f"htf_context_reason={htf_context_reason}")
        if pattern_reason:
            reasons.append(f"pattern_reason={pattern_reason}")

        aligned = (
            (htf_bias == HTF_BIAS_LONG and structure_direction == "long")
            or (htf_bias == HTF_BIAS_SHORT and structure_direction == "short")
        )

        if aligned:
            base = f"direction aligned: htf_bias={htf_bias}, structure_direction={structure_direction}"
            detail = " | ".join(reasons) if reasons else "alignment confirmed"
            return DirectionAlignResult(direction_aligned=True, direction_reason=f"{base} | {detail}")

        if htf_bias == "neutral" or structure_direction == "neutral":
            mismatch = f"neutral direction is not tradable: htf_bias={htf_bias}, structure_direction={structure_direction}"
        else:
            mismatch = f"direction mismatch: htf_bias={htf_bias}, structure_direction={structure_direction}"

        detail = " | ".join(reasons) if reasons else "alignment check failed"
        return DirectionAlignResult(direction_aligned=False, direction_reason=f"{mismatch} | {detail}")
