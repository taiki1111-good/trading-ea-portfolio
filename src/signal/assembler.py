from .types import EntryRuleResult, ExitRuleResult, SignalResult, SIGNAL_NONE


class SignalAssembler:
    @staticmethod
    def assemble(
        direction_aligned: bool,
        pattern_allowed: bool,
        entry_result: EntryRuleResult,
        exit_result: ExitRuleResult,
        sub_reasons: list[str] | None = None,
    ) -> SignalResult:
        reasons = [reason.strip() for reason in (sub_reasons or []) if reason and reason.strip()]

        entry_signal = entry_result.entry_signal
        exit_signal = exit_result.exit_signal

        if entry_signal and exit_signal:
            entry_signal = False
            exit_signal = False
            signal_type = SIGNAL_NONE
            conflict_reason = "entry and exit were both true; forced to none for safety"
            reasons.append(conflict_reason)
        elif entry_signal:
            signal_type = entry_result.signal_type
        else:
            signal_type = SIGNAL_NONE

        if not reasons:
            reasons = [
                "signal assembled from direction/pattern/entry/exit results",
                entry_result.entry_reason,
                exit_result.exit_reason,
            ]

        signal_reason = " | ".join(reasons)
        return SignalResult(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            signal_type=signal_type,
            signal_reason=signal_reason,
            direction_aligned=direction_aligned,
            pattern_allowed=pattern_allowed,
            sub_reasons=reasons,
        )
