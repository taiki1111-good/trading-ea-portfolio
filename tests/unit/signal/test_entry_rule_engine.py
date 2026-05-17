from src.signal.entry_rule_engine import EntryRuleEngine


def test_entry_rule_engine_returns_long_entry():
    result = EntryRuleEngine.evaluate(
        direction_aligned=True,
        pattern_allowed=True,
        structure_direction="long",
        sub_reasons=["direction ok", "pattern ok"],
    )
    assert result.entry_signal is True
    assert result.signal_type == "long_entry"
    assert result.entry_reason


def test_entry_rule_engine_returns_short_entry():
    result = EntryRuleEngine.evaluate(
        direction_aligned=True,
        pattern_allowed=True,
        structure_direction="short",
    )
    assert result.entry_signal is True
    assert result.signal_type == "short_entry"
    assert result.entry_reason


def test_entry_rule_engine_returns_none_when_conditions_fail():
    result = EntryRuleEngine.evaluate(
        direction_aligned=False,
        pattern_allowed=True,
        structure_direction="long",
        sub_reasons=["direction mismatch"],
    )
    assert result.entry_signal is False
    assert result.signal_type == "none"
    assert result.entry_reason
