from src.ltf_structure.types import STRUCTURE_NONE, STRUCTURE_THIRD_WAVE_BREAK, STRUCTURE_TRIANGLE_BREAK, StructureType, WavePhase

from .types import PatternGateResult


class PatternGate:
    @staticmethod
    def check(
        structure_type: StructureType,
        structure_candidate: bool,
        breakout_flag: bool,
        wave_phase: WavePhase,
        pattern_reason: str = "",
    ) -> PatternGateResult:
        reasons = [f"input_structure_type={structure_type}"]
        if pattern_reason:
            reasons.append(f"pattern_reason={pattern_reason}")

        if structure_type == STRUCTURE_TRIANGLE_BREAK:
            return PatternGateResult(
                pattern_allowed=False,
                gate_reason=(
                    "triangle_break is reserved for experiments and not allowed in initial main"
                    f" | {' | '.join(reasons)}"
                ),
            )

        if structure_type == STRUCTURE_NONE:
            return PatternGateResult(
                pattern_allowed=False,
                gate_reason=f"structure_type is none; skip entry | {' | '.join(reasons)}",
            )

        allowed = (
            structure_candidate
            and structure_type == STRUCTURE_THIRD_WAVE_BREAK
            and breakout_flag
            and wave_phase == "third"
        )

        if allowed:
            return PatternGateResult(
                pattern_allowed=True,
                gate_reason=(
                    "pattern gate passed for initial main third_wave_break"
                    f" | {' | '.join(reasons)}"
                ),
            )

        return PatternGateResult(
            pattern_allowed=False,
            gate_reason=(
                "pattern gate rejected: require structure_candidate=true, structure_type=third_wave_break, "
                f"breakout_flag=true, wave_phase=third | {' | '.join(reasons)}"
            ),
        )
