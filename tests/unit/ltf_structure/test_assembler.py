from src.ltf_structure.assembler import StructureAssembler


def test_assembler_returns_third_wave_break_when_conditions_match():
    result = StructureAssembler.assemble(
        wave_phase="third",
        wave_direction="long",
        breakout_flag=True,
        breakout_direction="long",
        triangle_flag=False,
        sub_reasons=["wave_reason: third-wave long candidate", "breakout_reason: close > swing high"],
    )

    assert result.structure_type == "third_wave_break"
    assert result.structure_direction == "long"
    assert result.structure_candidate is True
    assert result.pattern_reason
    assert "wave_reason" in result.pattern_reason
    assert "breakout_reason" in result.pattern_reason


def test_assembler_returns_none_when_conditions_do_not_match():
    result = StructureAssembler.assemble(
        wave_phase="unknown",
        wave_direction="neutral",
        breakout_flag=False,
        breakout_direction="neutral",
        triangle_flag=False,
        sub_reasons=["wave_reason: unknown", "breakout_reason: no breakout"],
    )

    assert result.structure_type == "none"
    assert result.structure_direction == "neutral"
    assert result.structure_candidate is False
    assert result.pattern_reason


def test_assembler_keeps_triangle_break_out_of_initial_main():
    result = StructureAssembler.assemble(
        wave_phase="third",
        wave_direction="long",
        breakout_flag=True,
        breakout_direction="long",
        triangle_flag=True,
        sub_reasons=["triangle_reason: reserved for experiments"],
    )

    assert result.structure_type == "none"
    assert result.structure_direction == "neutral"
    assert result.structure_candidate is False
    assert "reserved for experiments" in result.pattern_reason
