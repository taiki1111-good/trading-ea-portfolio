from pathlib import Path

from src.data.price_loader import PriceDataLoader
from src.evaluator import (
    FilterAnalyzer,
    MetricsCalculator,
    ReportAssembler,
    SignalAnalyzer,
    StructureAnalyzer,
)
from src.execution import ExecutionConfig, OrderBuilder, OrderSender, StateTransitionManager
from src.htf_context.assembler import ContextAssembler
from src.htf_context.resistance_detector import ResistanceDetector
from src.htf_context.support_detector import SupportDetector
from src.htf_context.trend_detector import TrendDetector
from src.htf_context.types import ResistanceConfig, SupportConfig, TrendConfig
from src.logger import DecisionLogger, EventLogger, LogAssembler, StateLogger, TradeLogger
from src.ltf_structure.assembler import StructureAssembler
from src.ltf_structure.types import WaveDirection, WavePhase
from src.risk_filter.assembler import RiskAssembler
from src.signal.assembler import SignalAssembler
from src.signal.entry_rule_engine import EntryRuleEngine
from src.signal.exit_rule_engine import ExitRuleEngine

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
PRICE_FIXTURE = FIXTURE_DIR / "price_e2e_minimal.csv"


def test_end_to_end_minimal_pipeline():
    price_frame = PriceDataLoader.load_from_csv(str(PRICE_FIXTURE), timeframe="H1")

    assert price_frame
    first_bar = price_frame[0]
    assert hasattr(first_bar, "timestamp")
    assert hasattr(first_bar, "open")
    assert hasattr(first_bar, "high")
    assert hasattr(first_bar, "low")
    assert hasattr(first_bar, "close")
    assert hasattr(first_bar, "spread")
    assert hasattr(first_bar, "volume")

    trend_result = TrendDetector.detect(
        price_frame,
        TrendConfig(lookback=3, min_strength=0.0),
    )
    resistance_result = ResistanceDetector.detect(
        price_frame,
        ResistanceConfig(lookback=3, min_distance=0.01),
    )
    support_result = SupportDetector.detect(
        price_frame,
        SupportConfig(lookback=3, min_distance=0.01),
    )

    htf_context_result = ContextAssembler.assemble(
        trend_result,
        resistance_result,
        support_result,
    )

    assert htf_context_result.htf_context_reason
    assert htf_context_result.htf_bias in {"long_bias", "short_bias", "neutral"}

    structure_result = StructureAssembler.assemble(
        wave_phase="third",
        wave_direction="long",
        breakout_flag=True,
        breakout_direction="long",
        triangle_flag=False,
        sub_reasons=[htf_context_result.htf_context_reason],
    )

    assert structure_result.structure_type == "third_wave_break"
    assert structure_result.structure_direction == "long"
    assert structure_result.pattern_reason

    direction_aligned = htf_context_result.htf_bias == "long_bias" and structure_result.structure_direction == "long"
    pattern_allowed = structure_result.structure_candidate
    entry_result = EntryRuleEngine.evaluate(
        direction_aligned=direction_aligned,
        pattern_allowed=pattern_allowed,
        structure_direction=structure_result.structure_direction,
        sub_reasons=[structure_result.pattern_reason],
    )
    exit_result = ExitRuleEngine.evaluate()

    signal_result = SignalAssembler.assemble(
        direction_aligned=direction_aligned,
        pattern_allowed=pattern_allowed,
        entry_result=entry_result,
        exit_result=exit_result,
        sub_reasons=[htf_context_result.htf_context_reason],
    )

    assert signal_result.signal_type in {"long_entry", "short_entry", "none"}
    assert signal_result.signal_reason
    assert signal_result.entry_signal is True

    risk_result = RiskAssembler.assemble(
        entry_signal=signal_result.entry_signal,
        exit_signal=signal_result.exit_signal,
        signal_type=signal_result.signal_type,
        signal_reason=signal_result.signal_reason,
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.1,
        stop_loss=1.0990,
        take_profit=1.1100,
        sub_reasons=[signal_result.signal_reason],
    )

    assert isinstance(risk_result.trade_ok, bool)
    assert risk_result.filter_reason
    assert risk_result.risk_reason

    execution_config = ExecutionConfig(dry_run=True)
    order_request_result = OrderBuilder.build(
        trade_ok=risk_result.trade_ok,
        signal_type=signal_result.signal_type,
        lot=risk_result.lot or 0.0,
        stop_loss=risk_result.stop_loss,
        take_profit=risk_result.take_profit,
        entry_price_candidate=price_frame[-1].close,
        execution_config=execution_config,
    )

    assert order_request_result.order_request is not None
    assert order_request_result.request_reason

    order_send_result = OrderSender.send(order_request_result.order_request, execution_config)
    submitted_transition = StateTransitionManager.transition_by_event(
        previous_state="IDLE",
        event="entry_order_submitted",
    )
    transition_result = StateTransitionManager.transition_by_event(
        previous_state=submitted_transition.next_state,
        event="entry_filled",
    )

    assert order_send_result.execution_reason
    assert order_send_result.order_result == "filled"
    assert submitted_transition.next_state == "ENTRY_PENDING"
    assert transition_result.next_state == "POSITION_OPEN"

    decision_log = DecisionLogger.log(
        htf_context_reason=htf_context_result.htf_context_reason,
        pattern_reason=structure_result.pattern_reason,
        signal_reason=signal_result.signal_reason,
        risk_reason=risk_result.risk_reason,
        filter_reason=risk_result.filter_reason,
        execution_reason=order_send_result.execution_reason,
        structure_type=structure_result.structure_type,
        signal_type=signal_result.signal_type,
    )
    trade_log = TradeLogger.log(
        order_result=order_send_result.order_result,
        lot=risk_result.lot,
        fill_price=price_frame[-1].close,
        execution_price=price_frame[-1].close,
        stop_loss=risk_result.stop_loss,
        take_profit=risk_result.take_profit,
        signal_type=signal_result.signal_type,
        trade_ok=risk_result.trade_ok,
        risk_reason=risk_result.risk_reason,
        execution_reason=order_send_result.execution_reason,
    )
    state_log = StateLogger.log(
        previous_state=transition_result.previous_state,
        next_state=transition_result.next_state,
        position_state=transition_result.next_state,
        transition_reason=transition_result.transition_reason,
        order_result=order_send_result.order_result,
        execution_reason=order_send_result.execution_reason,
    )
    event_log = EventLogger.log(
        timestamp=price_frame[-1].timestamp,
        event_flag=False,
        event_type="price_signal",
        event_risk_flag=False,
        filter_reason="no event risk",
    )

    bundle = LogAssembler.assemble(
        decision_log=decision_log,
        trade_log=trade_log,
        state_log=state_log,
        event_log=event_log,
    )

    assert bundle.decision_log.signal_type == signal_result.signal_type
    assert bundle.trade_log.order_result == order_send_result.order_result
    assert bundle.state_log.next_state == transition_result.next_state
    assert bundle.event_log.filter_reason == "no event risk"

    metrics_result = MetricsCalculator.calculate([trade_log])
    structure_stats, structure_warnings = StructureAnalyzer.analyze([decision_log])
    filter_stats, filter_warnings = FilterAnalyzer.analyze([event_log])
    signal_stats, signal_warnings = SignalAnalyzer.analyze([trade_log])
    evaluator_result = ReportAssembler.assemble(
        metrics_result=metrics_result,
        structure_stats=structure_stats,
        filter_stats=filter_stats,
        signal_stats=signal_stats,
        warnings=[*structure_warnings, *filter_warnings, *signal_warnings],
    )

    assert evaluator_result.summary_report.metrics.trade_count == 1
    assert evaluator_result.summary_report.structure_type_stats
    assert evaluator_result.summary_report.filter_hit_stats
    assert evaluator_result.summary_report.signal_type_stats
    assert evaluator_result.summary_report.evaluation_warnings is not None
    assert metrics_result.evaluation_reason
