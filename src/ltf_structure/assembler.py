from .types import (
    STRUCTURE_NONE,
    STRUCTURE_THIRD_WAVE_BREAK,
    StructureResult,
    WaveDirection,
    WavePhase,
)


class StructureAssembler:
    @staticmethod
    def assemble(
        wave_phase: WavePhase,
        wave_direction: WaveDirection,
        breakout_flag: bool,
        breakout_direction: WaveDirection,
        triangle_flag: bool,
        sub_reasons: list[str] | None = None,
    ) -> StructureResult:
        reasons = [reason.strip() for reason in (sub_reasons or []) if reason and reason.strip()]

        if triangle_flag:
            reason = (
                "triangle_break is reserved for experiments in initial main; "
                "conflict handled as none for safety"
            )
            if reasons:
                reason = f"{reason} | {' | '.join(reasons)}"
            return StructureResult(
                structure_type=STRUCTURE_NONE,
                structure_direction="neutral",
                structure_candidate=False,
                pattern_reason=reason,
                sub_reasons=reasons,
            )

        candidate = (
            wave_phase == "third"
            and breakout_flag
            and wave_direction in {"long", "short"}
            and wave_direction == breakout_direction
        )

        if candidate:
            base = f"third_wave_break candidate confirmed ({wave_direction})"
            details = " | ".join(reasons) if reasons else "wave/breakout reasons provided"
            return StructureResult(
                structure_type=STRUCTURE_THIRD_WAVE_BREAK,
                structure_direction=wave_direction,
                structure_candidate=True,
                pattern_reason=f"{base} | {details}",
                sub_reasons=reasons,
            )

        failed_checks = []
        if wave_phase != "third":
            failed_checks.append(f"wave_phase={wave_phase}")
        if not breakout_flag:
            failed_checks.append("breakout_flag=false")
        if wave_direction != breakout_direction:
            failed_checks.append(f"direction_mismatch={wave_direction}/{breakout_direction}")
        if wave_direction not in {"long", "short"}:
            failed_checks.append(f"wave_direction={wave_direction}")

        base_reason = "no valid third_wave_break structure in initial main"
        detail_reason = ", ".join(failed_checks) if failed_checks else "conditions not met"
        extra = f" | {' | '.join(reasons)}" if reasons else ""
        return StructureResult(
            structure_type=STRUCTURE_NONE,
            structure_direction="neutral",
            structure_candidate=False,
            pattern_reason=f"{base_reason} ({detail_reason}){extra}",
            sub_reasons=reasons,
        )
