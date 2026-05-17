from src.ltf_structure.types import StructureDirection

from .types import EntryRuleResult, SIGNAL_LONG_ENTRY, SIGNAL_NONE, SIGNAL_SHORT_ENTRY


class EntryRuleEngine:
    @staticmethod
    def evaluate(
        direction_aligned: bool,
        pattern_allowed: bool,
        structure_direction: StructureDirection,
        sub_reasons: list[str] | None = None,
    ) -> EntryRuleResult:
        reasons = [reason.strip() for reason in (sub_reasons or []) if reason and reason.strip()]

        if direction_aligned and pattern_allowed and structure_direction in {"long", "short"}:
            signal_type = SIGNAL_LONG_ENTRY if structure_direction == "long" else SIGNAL_SHORT_ENTRY
            detail = " | ".join(reasons) if reasons else "entry conditions satisfied"
            return EntryRuleResult(
                entry_signal=True,
                signal_type=signal_type,
                entry_reason=f"entry rule passed: {signal_type} | {detail}",
            )

        failed = []
        if not direction_aligned:
            failed.append("direction_aligned=false")
        if not pattern_allowed:
            failed.append("pattern_allowed=false")
        if structure_direction not in {"long", "short"}:
            failed.append(f"structure_direction={structure_direction}")

        detail = " | ".join(reasons) if reasons else "entry conditions failed"
        return EntryRuleResult(
            entry_signal=False,
            signal_type=SIGNAL_NONE,
            entry_reason=f"entry rule rejected ({', '.join(failed)}) | {detail}",
        )
