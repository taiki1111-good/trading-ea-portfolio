from .types import ExitRuleResult


class ExitRuleEngine:
    @staticmethod
    def evaluate() -> ExitRuleResult:
        # TODO(TBD): implement exit conditions after initial Signal skeleton is accepted.
        return ExitRuleResult(
            exit_signal=False,
            exit_reason="exit logic is not implemented in initial Signal skeleton",
        )
