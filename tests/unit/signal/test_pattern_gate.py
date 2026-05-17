from src.signal.pattern_gate import PatternGate


def test_pattern_gate_allows_third_wave_break_in_initial_main():
    result = PatternGate.check(
        structure_type="third_wave_break",
        structure_candidate=True,
        breakout_flag=True,
        wave_phase="third",
        pattern_reason="third wave and breakout confirmed",
    )
    assert result.pattern_allowed is True
    assert result.gate_reason


def test_pattern_gate_rejects_triangle_break_for_main():
    result = PatternGate.check(
        structure_type="triangle_break",
        structure_candidate=True,
        breakout_flag=True,
        wave_phase="third",
        pattern_reason="triangle candidate",
    )
    assert result.pattern_allowed is False
    assert "experiments" in result.gate_reason


def test_pattern_gate_rejects_none_structure_type():
    result = PatternGate.check(
        structure_type="none",
        structure_candidate=False,
        breakout_flag=False,
        wave_phase="unknown",
        pattern_reason="no structure",
    )
    assert result.pattern_allowed is False
    assert "none" in result.gate_reason
