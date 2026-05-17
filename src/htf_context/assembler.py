from .types import (
    HTF_BIAS_LONG,
    HTF_BIAS_NEUTRAL,
    HTF_BIAS_SHORT,
    HTFContextResult,
    ResistanceResult,
    SupportResult,
    TrendResult,
)


class ContextAssembler:
    @staticmethod
    def assemble(
        trend_result: TrendResult,
        resistance_result: ResistanceResult,
        support_result: SupportResult,
        sub_reasons: list[str] | None = None,
    ) -> HTFContextResult:
        bias = HTF_BIAS_NEUTRAL
        if trend_result.htf_trend_dir == "up" and resistance_result.htf_resistance_ok:
            bias = HTF_BIAS_LONG
        elif trend_result.htf_trend_dir == "down" and support_result.htf_support_ok:
            bias = HTF_BIAS_SHORT

        reasons: list[str] = [
            trend_result.trend_reason.strip(),
            resistance_result.resistance_reason.strip(),
            support_result.support_reason.strip(),
        ]
        if sub_reasons:
            reasons.extend(r.strip() for r in sub_reasons if r and r.strip())

        context_reason = " | ".join([reason for reason in reasons if reason])
        if not context_reason:
            context_reason = "htf context assembled without detailed reasons"

        return HTFContextResult(
            htf_trend_dir=trend_result.htf_trend_dir,
            htf_trend_strength=trend_result.htf_trend_strength,
            htf_resistance_ok=resistance_result.htf_resistance_ok,
            htf_support_ok=support_result.htf_support_ok,
            htf_bias=bias,
            htf_context_reason=context_reason,
            sub_reasons=sub_reasons or [],
        )
