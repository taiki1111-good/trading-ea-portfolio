from src.signal.assembler import SignalAssembler
from src.signal.direction_align_checker import DirectionAlignChecker
from src.signal.entry_rule_engine import EntryRuleEngine
from src.signal.exit_rule_engine import ExitRuleEngine
from src.signal.pattern_gate import PatternGate


def _run_signal(htf_bias: str, structure_type: str, structure_direction: str, structure_candidate: bool, breakout_flag: bool, wave_phase: str):
    htf_context_reason = f"htf_bias={htf_bias}"
    pattern_reason = f"structure_type={structure_type}"

    direction_result = DirectionAlignChecker.check(
        htf_bias=htf_bias,
        structure_direction=structure_direction,
        htf_context_reason=htf_context_reason,
        pattern_reason=pattern_reason,
    )
    gate_result = PatternGate.check(
        structure_type=structure_type,
        structure_candidate=structure_candidate,
        breakout_flag=breakout_flag,
        wave_phase=wave_phase,
        pattern_reason=pattern_reason,
    )
    entry_result = EntryRuleEngine.evaluate(
        direction_aligned=direction_result.direction_aligned,
        pattern_allowed=gate_result.pattern_allowed,
        structure_direction=structure_direction,
        sub_reasons=[direction_result.direction_reason, gate_result.gate_reason],
    )
    exit_result = ExitRuleEngine.evaluate()

    return SignalAssembler.assemble(
        direction_aligned=direction_result.direction_aligned,
        pattern_allowed=gate_result.pattern_allowed,
        entry_result=entry_result,
        exit_result=exit_result,
        sub_reasons=[
            f"htf_context_reason={htf_context_reason}",
            f"pattern_reason={pattern_reason}",
            f"direction alignment reason={direction_result.direction_reason}",
            f"pattern gate reason={gate_result.gate_reason}",
            f"entry rule reason={entry_result.entry_reason}",
            f"exit rule reason={exit_result.exit_reason}",
        ],
    )


def test_htf_ltf_to_signal_long_entry():
    result = _run_signal("long_bias", "third_wave_break", "long", True, True, "third")
    assert result.entry_signal is True
    assert result.signal_type == "long_entry"
    assert result.signal_reason


def test_htf_ltf_to_signal_short_entry():
    result = _run_signal("short_bias", "third_wave_break", "short", True, True, "third")
    assert result.entry_signal is True
    assert result.signal_type == "short_entry"


def test_htf_ltf_to_signal_direction_mismatch_returns_none():
    result = _run_signal("long_bias", "third_wave_break", "short", True, True, "third")
    assert result.entry_signal is False
    assert result.signal_type == "none"


def test_htf_ltf_to_signal_structure_none_returns_none():
    result = _run_signal("long_bias", "none", "long", False, False, "unknown")
    assert result.entry_signal is False
    assert result.signal_type == "none"


def test_htf_ltf_to_signal_triangle_break_returns_none():
    result = _run_signal("long_bias", "triangle_break", "long", True, True, "third")
    assert result.entry_signal is False
    assert result.signal_type == "none"
