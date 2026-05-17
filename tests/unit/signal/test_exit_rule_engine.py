from src.signal.exit_rule_engine import ExitRuleEngine


def test_exit_rule_engine_returns_false_in_initial_skeleton():
    result = ExitRuleEngine.evaluate()
    assert result.exit_signal is False
    assert "not implemented" in result.exit_reason
