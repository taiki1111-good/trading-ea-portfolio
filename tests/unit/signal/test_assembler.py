from src.signal.assembler import SignalAssembler
from src.signal.types import EntryRuleResult, ExitRuleResult


def test_signal_assembler_returns_long_entry():
    result = SignalAssembler.assemble(
        direction_aligned=True,
        pattern_allowed=True,
        entry_result=EntryRuleResult(True, "long_entry", "entry long"),
        exit_result=ExitRuleResult(False, "exit skeleton"),
        sub_reasons=["htf_context_reason=uptrend", "pattern_reason=third wave break", "direction alignment reason=aligned", "pattern gate reason=allowed", "entry rule reason=entry long"],
    )
    assert result.entry_signal is True
    assert result.exit_signal is False
    assert result.signal_type == "long_entry"
    assert result.signal_reason


def test_signal_assembler_returns_short_entry():
    result = SignalAssembler.assemble(
        direction_aligned=True,
        pattern_allowed=True,
        entry_result=EntryRuleResult(True, "short_entry", "entry short"),
        exit_result=ExitRuleResult(False, "exit skeleton"),
        sub_reasons=["htf_context_reason=downtrend", "pattern_reason=third wave break", "direction alignment reason=aligned", "pattern gate reason=allowed", "entry rule reason=entry short"],
    )
    assert result.entry_signal is True
    assert result.signal_type == "short_entry"


def test_signal_assembler_returns_none_when_entry_is_false():
    result = SignalAssembler.assemble(
        direction_aligned=False,
        pattern_allowed=False,
        entry_result=EntryRuleResult(False, "none", "entry rejected"),
        exit_result=ExitRuleResult(False, "exit skeleton"),
        sub_reasons=["htf_context_reason=neutral", "pattern_reason=none", "direction alignment reason=mismatch", "pattern gate reason=rejected", "entry rule reason=entry rejected"],
    )
    assert result.entry_signal is False
    assert result.signal_type == "none"
    assert result.signal_reason


def test_signal_assembler_entry_signal_true_has_entry_type_only():
    result = SignalAssembler.assemble(
        direction_aligned=True,
        pattern_allowed=True,
        entry_result=EntryRuleResult(True, "long_entry", "entry long"),
        exit_result=ExitRuleResult(False, "exit skeleton"),
        sub_reasons=["reason"],
    )
    assert result.entry_signal is True
    assert result.signal_type in {"long_entry", "short_entry"}


def test_signal_assembler_entry_signal_false_forces_none_type():
    result = SignalAssembler.assemble(
        direction_aligned=True,
        pattern_allowed=True,
        entry_result=EntryRuleResult(False, "none", "entry false"),
        exit_result=ExitRuleResult(False, "exit skeleton"),
        sub_reasons=["reason"],
    )
    assert result.entry_signal is False
    assert result.signal_type == "none"
