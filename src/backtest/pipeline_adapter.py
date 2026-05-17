from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone
from typing import Any, List, Optional

from src.data.types import PriceBar
from src.htf_context.assembler import ContextAssembler
from src.htf_context.resistance_detector import ResistanceDetector
from src.htf_context.support_detector import SupportDetector
from src.htf_context.trend_detector import TrendDetector
from src.htf_context.types import ResistanceConfig, SupportConfig, TrendConfig
from src.ltf_structure.breakout_detector import BreakoutDetector
from src.ltf_structure.swing_extractor import SwingExtractor
from src.ltf_structure.triangle_detector import TriangleDetector
from src.ltf_structure.types import BreakoutConfig, SwingConfig, TriangleConfig, WaveConfig
from src.ltf_structure.assembler import StructureAssembler
from src.ltf_structure.types import STRUCTURE_THIRD_WAVE_BREAK, StructureResult
from src.ltf_structure.wave_classifier import WaveClassifier
from src.signal.assembler import SignalAssembler
from src.signal.direction_align_checker import DirectionAlignChecker
from src.signal.entry_rule_engine import EntryRuleEngine
from src.signal.exit_rule_engine import ExitRuleEngine
from src.signal.pattern_gate import PatternGate
from src.risk_filter.position_sizer import PositionSizer
from src.risk_filter.stop_loss_planner import StopLossPlanner
from src.risk_filter.take_profit_planner import TakeProfitPlanner
from src.risk_filter.types import PositionSizerConfig, StopLossConfig, TakeProfitConfig
from src.signal.types import DirectionAlignResult
from src.signal.types import SIGNAL_LONG_ENTRY, SIGNAL_SHORT_ENTRY
from src.risk_filter.assembler import RiskAssembler

from .backtest_runner import EntryEvent


@dataclass(frozen=True)
class PipelineAdapterConfig:
    # TODO(TBD): move to strategy/backtest shared config once interfaces are stabilized.
    fixed_lot: float = 0.1
    placeholder_account_balance: float = 1000.0
    stop_loss_distance: float = 0.01
    take_profit_distance: float = 0.02
    max_spread: float = 10.0
    trend_lookback: int = 3
    trend_min_strength: float = 0.0
    support_resistance_lookback: int = 3
    min_distance: float = 0.0001
    swing_window: int = 2
    swing_causal: bool = True
    min_swing_points: int = 3
    breakout_use_close: bool = True
    triangle_lookback: int = 5
    triangle_tolerance: float = 0.01
    third_candidate_lookback_bars: int = 5
    max_entries_per_recent_third_candidate: int | None = None
    allow_temporal_third_break: bool = True
    allow_heuristic_fallback: bool = True
    htf_filter_enabled: bool = False
    htf_timeframe_policy: str = "H1_only"
    htf_neutral_policy: str = "permissive"
    htf_v2_enabled: bool = False
    htf_v2_policy: str = "diagnostic_only"
    htf_v2_h4_ma_fast: int = 20
    htf_v2_h4_ma_slow: int = 50
    htf_v2_h1_ma_fast: int = 20
    htf_v2_slope_window: int = 3
    sr_v2_enabled: bool = False
    sr_v2_policy: str = "diagnostic_only"
    sr_v2_window_bars: int = 48
    sr_v2_near_threshold_pips: float = 10.0
    sr_v2_pip_size: float = 0.01
    sr_v2_use_atr_normalized: bool = False
    session_v2_enabled: bool = False
    session_v2_policy: str = "diagnostic_only"
    session_v2_timezone: str = "UTC"
    session_v2_use_day_of_week: bool = True
    session_v2_use_hour_bucket: bool = True
    session_v2_use_dst_adjustment: bool = False


class PipelineAdapter:
    """Minimal adapter from bars window to BacktestRunner EntryEvent.

    The adapter is intentionally small and uses existing HTF/LTF/Signal/RiskFilter modules
    with minimal transformations.
    """

    def __init__(self, config: PipelineAdapterConfig | None = None) -> None:
        self._config = config or PipelineAdapterConfig()
        self.reset_run_state()

    def reset_run_state(self) -> None:
        self._recent_third_entry_counts: dict[str, int] = {}
        self._last_decision_trace: dict[str, object] = {}
        self._trace_base: dict[str, object] = {}

    def get_last_decision_trace(self) -> dict[str, object]:
        return dict(self._last_decision_trace)

    def _set_trace(self, **kwargs: object) -> None:
        self._last_decision_trace = {**self._trace_base, **dict(kwargs)}

    @staticmethod
    def _normalize_htf_direction_from_bias(htf_bias: str) -> str:
        if htf_bias == "long_bias":
            return "up"
        if htf_bias == "short_bias":
            return "down"
        if htf_bias == "neutral":
            return "neutral"
        return "unknown"

    @staticmethod
    def _normalize_htf_direction_from_trend(htf_trend_dir: str) -> str:
        if htf_trend_dir in {"up", "down", "neutral"}:
            return htf_trend_dir
        return "unknown"

    def _check_htf_direction_alignment_v1(
        self,
        structure_direction: str,
        htf_bias: str,
        htf_trend_dir: str,
        htf_context_reason: str,
        pattern_reason: str,
    ) -> DirectionAlignResult:
        bias_dir = self._normalize_htf_direction_from_bias(htf_bias)
        trend_dir = self._normalize_htf_direction_from_trend(htf_trend_dir)
        source = "htf_bias"
        selected_dir = bias_dir
        fallback_used = False

        if selected_dir == "unknown":
            selected_dir = trend_dir
            source = "htf_trend_dir_fallback"
            fallback_used = True

        policy = str(self._config.htf_neutral_policy or "permissive").strip().lower()
        if policy not in {"permissive", "strict"}:
            policy = "permissive"

        aligned = False
        if structure_direction == "long":
            if selected_dir == "up":
                aligned = True
            elif selected_dir == "neutral":
                aligned = policy == "permissive"
        elif structure_direction == "short":
            if selected_dir == "down":
                aligned = True
            elif selected_dir == "neutral":
                aligned = policy == "permissive"

        reason = (
            f"htf_filter_v1: aligned={aligned} structure_direction={structure_direction} "
            f"selected_dir={selected_dir} source={source} neutral_policy={policy} "
            f"fallback_used={fallback_used} htf_bias={htf_bias} htf_trend_dir={htf_trend_dir} "
            f"htf_context_reason={htf_context_reason} pattern_reason={pattern_reason}"
        )
        return DirectionAlignResult(direction_aligned=aligned, direction_reason=reason)

    def _normalize_temporal_metadata(self, temporal_meta: dict[str, object]) -> tuple[bool, dict[str, object]]:
        recent_ts = str(temporal_meta.get("recent_third_timestamp", "")).strip()
        if not recent_ts:
            return (
                False,
                {
                    "recent_third_timestamp": "",
                    "recent_third_direction": "",
                    "temporal_lag_bars": None,
                    "temporal_lookback_bars": None,
                },
            )
        return (
            True,
            {
                "recent_third_timestamp": recent_ts,
                "recent_third_direction": str(temporal_meta.get("recent_third_direction", "")).strip(),
                "temporal_lag_bars": temporal_meta.get("temporal_lag_bars"),
                "temporal_lookback_bars": temporal_meta.get("temporal_lookback_bars"),
            },
        )

    @staticmethod
    def _bucket_start(timestamp, timeframe_minutes: int):
        if timeframe_minutes == 60:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        if timeframe_minutes == 240:
            hour_block = (timestamp.hour // 4) * 4
            return timestamp.replace(hour=hour_block, minute=0, second=0, microsecond=0)
        raise ValueError(f"unsupported timeframe_minutes={timeframe_minutes}")

    def _aggregate_completed_htf_bars(
        self,
        window: List[PriceBar],
        timeframe_minutes: int,
        decision_time,
    ) -> tuple[list[dict[str, Any]], bool, str]:
        expected_count = timeframe_minutes // 5
        buckets: dict[Any, list[PriceBar]] = {}
        for bar in window:
            bucket_start = self._bucket_start(bar.timestamp, timeframe_minutes)
            bucket_close = bucket_start + timedelta(minutes=timeframe_minutes)
            if bucket_close > decision_time:
                continue
            buckets.setdefault(bucket_start, []).append(bar)

        aggregated: list[dict[str, Any]] = []
        for bucket_start in sorted(buckets.keys()):
            bars = sorted(buckets[bucket_start], key=lambda b: b.timestamp)
            if len(bars) < expected_count:
                continue
            if any(b.open is None or b.high is None or b.low is None or b.close is None for b in bars):
                return [], False, "ohlc missing in htf aggregation source bars"
            aggregated.append(
                {
                    "start_time": bucket_start,
                    "close_time": bucket_start + timedelta(minutes=timeframe_minutes),
                    "open": bars[0].open,
                    "high": max(b.high for b in bars),
                    "low": min(b.low for b in bars),
                    "close": bars[-1].close,
                }
            )
        if not aggregated:
            return [], False, "no completed htf bars available for decision_time"
        return aggregated, True, "ok"

    @staticmethod
    def _latest_sma(values: list[float], window: int) -> float | None:
        if window <= 0 or len(values) < window:
            return None
        return sum(values[-window:]) / float(window)

    @staticmethod
    def _sma_series(values: list[float], window: int) -> list[float]:
        if window <= 0 or len(values) < window:
            return []
        series: list[float] = []
        running_sum = sum(values[:window])
        series.append(running_sum / float(window))
        for idx in range(window, len(values)):
            running_sum += values[idx] - values[idx - window]
            series.append(running_sum / float(window))
        return series

    @staticmethod
    def _latest_slope(series: list[float], slope_window: int) -> float | None:
        if slope_window <= 0:
            return None
        if len(series) <= slope_window:
            return None
        return series[-1] - series[-1 - slope_window]

    def _compute_htf_v2_trace(self, window: List[PriceBar], current_bar: PriceBar) -> dict[str, object]:
        base = {
            "htf_v2_enabled": self._config.htf_v2_enabled,
            "htf_policy": self._config.htf_v2_policy,
            "h4_bias": "unknown",
            "h4_bias_reason": "htf_v2 disabled",
            "h4_ma20": None,
            "h4_ma50": None,
            "h4_ma20_slope": None,
            "h1_context": "unknown",
            "h1_context_reason": "htf_v2 disabled",
            "h1_ma20": None,
            "h1_ma20_slope": None,
            "htf_v2_direction_allowed": False,
            "htf_v2_filter_reason": "htf_v2 disabled",
            "htf_v2_conflict_flag": False,
            "htf_v2_data_valid_flag": False,
            "htf_v2_candidate_direction": "unknown",
            "htf_v2_aligned_only_allowed": False,
            "htf_v2_pullback_permissive_allowed": False,
            "htf_v2_context_uncertain_flag": True,
            "htf_v2_hard_conflict_flag": False,
        }
        if not self._config.htf_v2_enabled:
            return base

        decision_time = current_bar.timestamp + timedelta(minutes=5)
        h1_bars, h1_ok, h1_reason = self._aggregate_completed_htf_bars(window, 60, decision_time)
        h4_bars, h4_ok, h4_reason = self._aggregate_completed_htf_bars(window, 240, decision_time)
        if not h1_ok or not h4_ok:
            base["h4_bias_reason"] = f"h4 aggregation invalid: {h4_reason}"
            base["h1_context_reason"] = f"h1 aggregation invalid: {h1_reason}"
            base["htf_v2_filter_reason"] = "diagnostic_only:no_entry_filter"
            return base

        h4_closes = [float(b["close"]) for b in h4_bars]
        h1_closes = [float(b["close"]) for b in h1_bars]
        h4_ma_fast = self._latest_sma(h4_closes, self._config.htf_v2_h4_ma_fast)
        h4_ma_slow = self._latest_sma(h4_closes, self._config.htf_v2_h4_ma_slow)
        h4_ma_fast_series = self._sma_series(h4_closes, self._config.htf_v2_h4_ma_fast)
        h4_slope = self._latest_slope(h4_ma_fast_series, self._config.htf_v2_slope_window)
        h1_ma_fast = self._latest_sma(h1_closes, self._config.htf_v2_h1_ma_fast)
        h1_ma_fast_series = self._sma_series(h1_closes, self._config.htf_v2_h1_ma_fast)
        h1_slope = self._latest_slope(h1_ma_fast_series, self._config.htf_v2_slope_window)
        latest_h4_close = h4_closes[-1] if h4_closes else None
        latest_h1_close = h1_closes[-1] if h1_closes else None

        base.update(
            {
                "h4_ma20": h4_ma_fast,
                "h4_ma50": h4_ma_slow,
                "h4_ma20_slope": h4_slope,
                "h1_ma20": h1_ma_fast,
                "h1_ma20_slope": h1_slope,
            }
        )

        if (
            latest_h4_close is None
            or h4_ma_fast is None
            or h4_ma_slow is None
            or h4_slope is None
            or latest_h1_close is None
            or h1_ma_fast is None
            or h1_slope is None
        ):
            base["h4_bias"] = "unknown"
            base["h1_context"] = "unknown"
            base["h4_bias_reason"] = "insufficient history for MA/slope calculation"
            base["h1_context_reason"] = "insufficient history for MA/slope calculation"
            base["htf_v2_filter_reason"] = "diagnostic_only:no_entry_filter"
            return base

        if latest_h4_close > h4_ma_fast and h4_ma_fast > h4_ma_slow and h4_slope > 0:
            h4_bias = "up"
        elif latest_h4_close < h4_ma_fast and h4_ma_fast < h4_ma_slow and h4_slope < 0:
            h4_bias = "down"
        else:
            h4_bias = "neutral"

        h1_trend: str | None = None
        if latest_h1_close > h1_ma_fast and h1_slope > 0:
            h1_trend = "trend_up"
        elif latest_h1_close < h1_ma_fast and h1_slope < 0:
            h1_trend = "trend_down"

        if h4_bias == "up" and h1_trend == "trend_up":
            h1_context = "aligned_up"
        elif h4_bias == "down" and h1_trend == "trend_down":
            h1_context = "aligned_down"
        elif (h4_bias == "up" and h1_trend == "trend_down") or (h4_bias == "down" and h1_trend == "trend_up"):
            h1_context = "pullback_against_h4"
        elif h4_bias == "neutral" and h1_trend in {"trend_up", "trend_down"}:
            h1_context = "range_or_neutral"
        else:
            h1_context = "unknown"

        context_uncertain = (h4_bias in {"neutral", "unknown"}) or (h1_context in {"unknown", "range_or_neutral"})

        policy = str(self._config.htf_v2_policy or "diagnostic_only").strip().lower()
        direction_allowed = False
        filter_reason = "diagnostic_only:no_entry_filter"
        if policy == "aligned_only":
            filter_reason = "aligned_only:direction_allowed_computed"
        elif policy == "pullback_permissive":
            filter_reason = "pullback_permissive:direction_allowed_computed"

        base.update(
            {
                "h4_bias": h4_bias,
                "h4_bias_reason": f"h4_bias by ma/slope rule close={latest_h4_close:.6f}",
                "h1_context": h1_context,
                "h1_context_reason": f"h1_context from h4_bias={h4_bias} h1_trend={h1_trend or 'none'}",
                "htf_v2_direction_allowed": direction_allowed,
                "htf_v2_filter_reason": filter_reason,
                "htf_v2_conflict_flag": False,
                "htf_v2_data_valid_flag": h4_bias != "unknown" and h1_context != "unknown",
                "htf_v2_context_uncertain_flag": context_uncertain,
                "htf_v2_hard_conflict_flag": False,
            }
        )
        return base

    @staticmethod
    def _compute_htf_v2_policy_diagnostics(
        *,
        candidate_direction: str,
        h4_bias: str,
        h1_context: str,
    ) -> dict[str, object]:
        aligned_only_allowed = False
        pullback_permissive_allowed = False
        hard_conflict = False
        context_uncertain = (h4_bias in {"neutral", "unknown"}) or (h1_context in {"unknown", "range_or_neutral"})

        if candidate_direction == "long":
            aligned_only_allowed = h4_bias == "up" and h1_context == "aligned_up"
            pullback_permissive_allowed = h4_bias == "up" and h1_context in {"aligned_up", "pullback_against_h4"}
            if h4_bias == "down" or h1_context == "aligned_down":
                hard_conflict = True
        elif candidate_direction == "short":
            aligned_only_allowed = h4_bias == "down" and h1_context == "aligned_down"
            pullback_permissive_allowed = h4_bias == "down" and h1_context in {"aligned_down", "pullback_against_h4"}
            if h4_bias == "up" or h1_context == "aligned_up":
                hard_conflict = True

        return {
            "htf_v2_candidate_direction": candidate_direction if candidate_direction in {"long", "short"} else "unknown",
            "htf_v2_aligned_only_allowed": aligned_only_allowed,
            "htf_v2_pullback_permissive_allowed": pullback_permissive_allowed,
            "htf_v2_context_uncertain_flag": context_uncertain,
            "htf_v2_hard_conflict_flag": hard_conflict,
            # legacy column is kept for backward compatibility and narrowed to hard conflict semantics.
            "htf_v2_conflict_flag": hard_conflict,
        }

    def _compute_sr_v2_trace(
        self,
        window: List[PriceBar],
        current_bar: PriceBar,
        candidate_direction: str,
    ) -> dict[str, object]:
        policy = str(self._config.sr_v2_policy or "diagnostic_only").strip().lower()
        base = {
            "sr_v2_enabled": self._config.sr_v2_enabled,
            "sr_policy": policy,
            "sr_window_bars": self._config.sr_v2_window_bars,
            "nearest_resistance": None,
            "nearest_support": None,
            "nearest_resistance_distance_pips": None,
            "nearest_support_distance_pips": None,
            "sr_proximity_flag": False,
            "sr_block_side": "none",
            "sr_reason": "sr_v2 disabled",
            "sr_data_valid_flag": False,
            "sr_counterfactual_group": "sr_v2_disabled",
        }
        if not self._config.sr_v2_enabled:
            return base

        history = window[:-1]
        n = max(1, int(self._config.sr_v2_window_bars))
        if len(history) < n:
            base["sr_reason"] = "diagnostic_only:insufficient_history"
            base["sr_counterfactual_group"] = "sr_insufficient_history"
            return base

        lookback = history[-n:]
        resistance = max(float(b.high) for b in lookback)
        support = min(float(b.low) for b in lookback)
        pip_size = float(self._config.sr_v2_pip_size) if float(self._config.sr_v2_pip_size) > 0 else 0.01
        reference_price = float(current_bar.close)
        resistance_distance_pips = abs(resistance - reference_price) / pip_size
        support_distance_pips = abs(reference_price - support) / pip_size
        threshold = float(self._config.sr_v2_near_threshold_pips)

        proximity = False
        block_side = "none"
        direction = candidate_direction if candidate_direction in {"long", "short"} else "unknown"
        if direction == "long":
            if resistance_distance_pips <= threshold:
                proximity = True
                block_side = "resistance"
        elif direction == "short":
            if support_distance_pips <= threshold:
                proximity = True
                block_side = "support"

        if direction == "long":
            group = "sr_long_near_resistance" if proximity else "sr_long_not_near_resistance"
        elif direction == "short":
            group = "sr_short_near_support" if proximity else "sr_short_not_near_support"
        else:
            group = "sr_direction_unknown"

        reason = "diagnostic_only:no_entry_filter"
        if direction == "unknown":
            reason += "|direction_unknown"

        base.update(
            {
                "nearest_resistance": resistance,
                "nearest_support": support,
                "nearest_resistance_distance_pips": resistance_distance_pips,
                "nearest_support_distance_pips": support_distance_pips,
                "sr_proximity_flag": proximity,
                "sr_block_side": block_side,
                "sr_reason": reason,
                "sr_data_valid_flag": True,
                "sr_counterfactual_group": group,
            }
        )
        return base

    def _compute_session_v2_trace(self, current_bar: PriceBar) -> dict[str, object]:
        policy = str(self._config.session_v2_policy or "diagnostic_only").strip().lower()
        base = {
            "session_v2_enabled": self._config.session_v2_enabled,
            "session_policy": policy,
            "hour_utc": None,
            "day_of_week": "unknown",
            "session_label": "unknown",
            "is_tokyo_session": False,
            "is_london_session": False,
            "is_new_york_session": False,
            "is_london_ny_overlap": False,
            "is_low_liquidity_hour": False,
            "session_risk_flag": False,
            "session_reason": "session_v2 disabled",
            "session_data_valid_flag": False,
        }
        if not self._config.session_v2_enabled:
            return base

        ts_utc = current_bar.timestamp.astimezone(timezone.utc)
        hour_utc = int(ts_utc.hour)
        day_of_week = ts_utc.strftime("%A").lower() if self._config.session_v2_use_day_of_week else "disabled"

        is_tokyo = 0 <= hour_utc < 9
        is_london = 8 <= hour_utc < 17
        is_new_york = 13 <= hour_utc < 22
        is_overlap = 13 <= hour_utc < 17
        is_low_liquidity = hour_utc in {22, 23}

        if is_low_liquidity:
            session_label = "low_liquidity"
        elif is_overlap:
            session_label = "london_ny_overlap"
        elif is_tokyo:
            session_label = "tokyo"
        elif is_london:
            session_label = "london"
        elif is_new_york:
            session_label = "new_york"
        else:
            session_label = "off_session"

        base.update(
            {
                "hour_utc": hour_utc if self._config.session_v2_use_hour_bucket else None,
                "day_of_week": day_of_week,
                "session_label": session_label,
                "is_tokyo_session": is_tokyo,
                "is_london_session": is_london,
                "is_new_york_session": is_new_york,
                "is_london_ny_overlap": is_overlap,
                "is_low_liquidity_hour": is_low_liquidity,
                "session_risk_flag": is_low_liquidity,
                "session_reason": "diagnostic_only:no_entry_filter|session_label_utc_fixed_approx",
                "session_data_valid_flag": True,
            }
        )
        return base

    def __call__(self, current_index: int, window: List[PriceBar]) -> Optional[EntryEvent]:
        if not window:
            return None
        if current_index != len(window) - 1:
            raise ValueError("PipelineAdapter requires window[-1] to be the current bar (no future bars)")

        current_bar = window[-1]
        trend_result = TrendDetector.detect(
            window,
            TrendConfig(
                lookback=self._config.trend_lookback,
                min_strength=self._config.trend_min_strength,
            ),
        )
        resistance_result = ResistanceDetector.detect(
            window,
            ResistanceConfig(
                lookback=self._config.support_resistance_lookback,
                min_distance=self._config.min_distance,
            ),
        )
        support_result = SupportDetector.detect(
            window,
            SupportConfig(
                lookback=self._config.support_resistance_lookback,
                min_distance=self._config.min_distance,
            ),
        )
        htf_context_result = ContextAssembler.assemble(
            trend_result=trend_result,
            resistance_result=resistance_result,
            support_result=support_result,
        )
        htf_v2_trace = self._compute_htf_v2_trace(window=window, current_bar=current_bar)
        self._trace_base = {
            "htf_filter_enabled": self._config.htf_filter_enabled,
            "htf_timeframe_policy": self._config.htf_timeframe_policy,
            "htf_neutral_policy": self._config.htf_neutral_policy,
            "htf_bias": htf_context_result.htf_bias,
            "htf_trend_dir": trend_result.htf_trend_dir,
            "htf_direction_aligned": False,
            "htf_filter_reason": "htf filter disabled",
            "htf_context_reason": htf_context_result.htf_context_reason,
            **htf_v2_trace,
        }

        structure_result, wave_phase, breakout_flag, fallback_used, structure_source, temporal_meta = self._build_structure(
            window, htf_context_result.htf_context_reason
        )
        candidate_direction = structure_result.structure_direction if structure_result is not None else "unknown"
        sr_v2_trace = self._compute_sr_v2_trace(window=window, current_bar=current_bar, candidate_direction=candidate_direction)
        self._trace_base.update(sr_v2_trace)
        session_v2_trace = self._compute_session_v2_trace(current_bar=current_bar)
        self._trace_base.update(session_v2_trace)
        if self._config.htf_v2_enabled:
            sem = self._compute_htf_v2_policy_diagnostics(
                candidate_direction=candidate_direction,
                h4_bias=str(self._trace_base.get("h4_bias", "unknown")),
                h1_context=str(self._trace_base.get("h1_context", "unknown")),
            )
            policy = str(self._config.htf_v2_policy or "diagnostic_only").strip().lower()
            direction_allowed = False
            if policy == "aligned_only":
                direction_allowed = bool(sem["htf_v2_aligned_only_allowed"])
            elif policy == "pullback_permissive":
                direction_allowed = bool(sem["htf_v2_pullback_permissive_allowed"])
            self._trace_base.update({**sem, "htf_v2_direction_allowed": direction_allowed})
        temporal_candidate, temporal_fields = self._normalize_temporal_metadata(temporal_meta)
        if structure_result is None:
            self._set_trace(
                bar_index=current_index,
                timestamp=current_bar.timestamp.isoformat(),
                close=current_bar.close,
                htf_bias=htf_context_result.htf_bias,
                wave_phase="unknown",
                wave_direction="unknown",
                breakout_flag=False,
                breakout_direction="neutral",
                structure_candidate=False,
                structure_source="detector_chain",
                temporal_candidate=False,
                recent_third_timestamp="",
                recent_third_direction="",
                temporal_lag_bars=None,
                temporal_lookback_bars=None,
                direction_aligned=False,
                pattern_allowed=False,
                entry_signal=False,
                trade_ok=False,
                fail_stage="structure",
                decision_reason="no structure candidate from detector chain (fallback disabled or no temporal candidate)",
            )
            return None
        if self._config.htf_filter_enabled:
            direction_result = self._check_htf_direction_alignment_v1(
                structure_direction=structure_result.structure_direction,
                htf_bias=str(htf_context_result.htf_bias),
                htf_trend_dir=str(trend_result.htf_trend_dir),
                htf_context_reason=htf_context_result.htf_context_reason,
                pattern_reason=structure_result.pattern_reason,
            )
            self._trace_base["htf_filter_reason"] = direction_result.direction_reason
        else:
            direction_result = DirectionAlignChecker.check(
                htf_bias=htf_context_result.htf_bias,
                structure_direction=structure_result.structure_direction,
                htf_context_reason=htf_context_result.htf_context_reason,
                pattern_reason=structure_result.pattern_reason,
            )
            self._trace_base["htf_filter_reason"] = "htf filter disabled"
        self._trace_base["htf_direction_aligned"] = direction_result.direction_aligned
        pattern_gate_result = PatternGate.check(
            structure_type=structure_result.structure_type,
            structure_candidate=structure_result.structure_candidate,
            breakout_flag=breakout_flag,
            wave_phase=wave_phase,
            pattern_reason=structure_result.pattern_reason,
        )

        entry_result = EntryRuleEngine.evaluate(
            direction_aligned=direction_result.direction_aligned,
            pattern_allowed=pattern_gate_result.pattern_allowed,
            structure_direction=structure_result.structure_direction,
            sub_reasons=[
                direction_result.direction_reason,
                pattern_gate_result.gate_reason,
                structure_result.pattern_reason,
            ],
        )
        exit_result = ExitRuleEngine.evaluate()
        signal_result = SignalAssembler.assemble(
            direction_aligned=direction_result.direction_aligned,
            pattern_allowed=pattern_gate_result.pattern_allowed,
            entry_result=entry_result,
            exit_result=exit_result,
            sub_reasons=[
                htf_context_result.htf_context_reason,
                direction_result.direction_reason,
                pattern_gate_result.gate_reason,
                structure_result.pattern_reason,
            ],
        )

        spread_ok = current_bar.spread <= self._config.max_spread
        entry_price_candidate = current_bar.close
        if not direction_result.direction_aligned:
            self._set_trace(
                bar_index=current_index,
                timestamp=current_bar.timestamp.isoformat(),
                close=current_bar.close,
                htf_bias=htf_context_result.htf_bias,
                wave_phase=wave_phase,
                wave_direction=structure_result.structure_direction,
                breakout_flag=breakout_flag,
                breakout_direction=str(temporal_meta.get("breakout_direction", "")),
                structure_candidate=structure_result.structure_candidate,
                structure_source=structure_source,
                temporal_candidate=temporal_candidate,
                recent_third_timestamp=temporal_fields["recent_third_timestamp"],
                recent_third_direction=temporal_fields["recent_third_direction"],
                temporal_lag_bars=temporal_fields["temporal_lag_bars"],
                temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
                direction_aligned=False,
                pattern_allowed=pattern_gate_result.pattern_allowed,
                entry_signal=signal_result.entry_signal,
                trade_ok=False,
                fail_stage="direction_alignment",
                decision_reason=direction_result.direction_reason,
            )
            return None

        if not pattern_gate_result.pattern_allowed:
            self._set_trace(
                bar_index=current_index,
                timestamp=current_bar.timestamp.isoformat(),
                close=current_bar.close,
                htf_bias=htf_context_result.htf_bias,
                wave_phase=wave_phase,
                wave_direction=structure_result.structure_direction,
                breakout_flag=breakout_flag,
                breakout_direction=str(temporal_meta.get("breakout_direction", "")),
                structure_candidate=structure_result.structure_candidate,
                structure_source=structure_source,
                temporal_candidate=temporal_candidate,
                recent_third_timestamp=temporal_fields["recent_third_timestamp"],
                recent_third_direction=temporal_fields["recent_third_direction"],
                temporal_lag_bars=temporal_fields["temporal_lag_bars"],
                temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
                direction_aligned=direction_result.direction_aligned,
                pattern_allowed=False,
                entry_signal=signal_result.entry_signal,
                trade_ok=False,
                fail_stage="pattern_gate",
                decision_reason=pattern_gate_result.gate_reason,
            )
            return None

        if (not signal_result.entry_signal) or signal_result.signal_type == "none":
            self._set_trace(
                bar_index=current_index,
                timestamp=current_bar.timestamp.isoformat(),
                close=current_bar.close,
                htf_bias=htf_context_result.htf_bias,
                wave_phase=wave_phase,
                wave_direction=structure_result.structure_direction,
                breakout_flag=breakout_flag,
                breakout_direction=str(temporal_meta.get("breakout_direction", "")),
                structure_candidate=structure_result.structure_candidate,
                structure_source=structure_source,
                temporal_candidate=temporal_candidate,
                recent_third_timestamp=temporal_fields["recent_third_timestamp"],
                recent_third_direction=temporal_fields["recent_third_direction"],
                temporal_lag_bars=temporal_fields["temporal_lag_bars"],
                temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
                direction_aligned=direction_result.direction_aligned,
                pattern_allowed=pattern_gate_result.pattern_allowed,
                entry_signal=signal_result.entry_signal,
                trade_ok=False,
                fail_stage="signal",
                decision_reason=signal_result.signal_reason,
            )
            return None

        size_result = PositionSizer.size(
            account_balance=self._config.placeholder_account_balance,
            position_sizer_config=PositionSizerConfig(fixed_lot=self._config.fixed_lot),
        )
        stop_result = StopLossPlanner.plan(
            signal_type=signal_result.signal_type,
            entry_price_candidate=entry_price_candidate,
            stop_loss_config=StopLossConfig(fixed_stop_distance=self._config.stop_loss_distance),
        )
        take_profit_result = TakeProfitPlanner.plan(
            signal_type=signal_result.signal_type,
            entry_price_candidate=entry_price_candidate,
            take_profit_config=TakeProfitConfig(fixed_take_profit_distance=self._config.take_profit_distance),
        )

        risk_result = RiskAssembler.assemble(
            entry_signal=signal_result.entry_signal,
            exit_signal=signal_result.exit_signal,
            signal_type=signal_result.signal_type,
            signal_reason=signal_result.signal_reason,
            event_risk_flag=False,
            spread_ok=spread_ok,
            limit_ok=True,
            max_trade_reached_flag=False,
            lot=size_result.lot,
            stop_loss=stop_result.stop_loss,
            take_profit=take_profit_result.take_profit,
            sub_reasons=[
                signal_result.signal_reason,
                size_result.size_reason,
                stop_result.stop_loss_reason,
                take_profit_result.take_profit_reason,
            ],
        )

        if not risk_result.trade_ok or risk_result.lot is None:
            self._set_trace(
                bar_index=current_index,
                timestamp=current_bar.timestamp.isoformat(),
                close=current_bar.close,
                htf_bias=htf_context_result.htf_bias,
                wave_phase=wave_phase,
                wave_direction=structure_result.structure_direction,
                breakout_flag=breakout_flag,
                breakout_direction=str(temporal_meta.get("breakout_direction", "")),
                structure_candidate=structure_result.structure_candidate,
                structure_source=structure_source,
                temporal_candidate=temporal_candidate,
                recent_third_timestamp=temporal_fields["recent_third_timestamp"],
                recent_third_direction=temporal_fields["recent_third_direction"],
                temporal_lag_bars=temporal_fields["temporal_lag_bars"],
                temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
                direction_aligned=direction_result.direction_aligned,
                pattern_allowed=pattern_gate_result.pattern_allowed,
                entry_signal=signal_result.entry_signal,
                trade_ok=False,
                fail_stage="risk_filter",
                decision_reason=risk_result.filter_reason or risk_result.risk_reason or "trade not allowed",
            )
            return None

        if signal_result.signal_type == SIGNAL_LONG_ENTRY:
            direction = "long"
        elif signal_result.signal_type == SIGNAL_SHORT_ENTRY:
            direction = "short"
        else:
            self._set_trace(
                bar_index=current_index,
                timestamp=current_bar.timestamp.isoformat(),
                close=current_bar.close,
                htf_bias=htf_context_result.htf_bias,
                wave_phase=wave_phase,
                wave_direction=structure_result.structure_direction,
                breakout_flag=breakout_flag,
                breakout_direction=str(temporal_meta.get("breakout_direction", "")),
                structure_candidate=structure_result.structure_candidate,
                structure_source=structure_source,
                temporal_candidate=temporal_candidate,
                recent_third_timestamp=temporal_fields["recent_third_timestamp"],
                recent_third_direction=temporal_fields["recent_third_direction"],
                temporal_lag_bars=temporal_fields["temporal_lag_bars"],
                temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
                direction_aligned=direction_result.direction_aligned,
                pattern_allowed=pattern_gate_result.pattern_allowed,
                entry_signal=signal_result.entry_signal,
                trade_ok=False,
                fail_stage="signal",
                decision_reason="signal_type is not entry type",
            )
            return None

        signal_reason = signal_result.signal_reason
        risk_reason = risk_result.risk_reason
        filter_reason = risk_result.filter_reason
        reason_parts = [signal_reason, risk_reason, filter_reason]
        entry_reason = " | ".join(part.strip() for part in reason_parts if part and part.strip())
        if not entry_reason:
            entry_reason = "pipeline adapter produced entry without explicit reasons"

        recent_third_timestamp = str(temporal_fields["recent_third_timestamp"]).strip()
        if not self._allow_entry_for_recent_third_candidate(recent_third_timestamp):
            self._set_trace(
                bar_index=current_index,
                timestamp=current_bar.timestamp.isoformat(),
                close=current_bar.close,
                htf_bias=htf_context_result.htf_bias,
                wave_phase=wave_phase,
                wave_direction=structure_result.structure_direction,
                breakout_flag=breakout_flag,
                breakout_direction=str(temporal_meta.get("breakout_direction", "")),
                structure_candidate=structure_result.structure_candidate,
                structure_source=structure_source,
                temporal_candidate=temporal_candidate,
                recent_third_timestamp=recent_third_timestamp,
                recent_third_direction=temporal_fields["recent_third_direction"],
                temporal_lag_bars=temporal_fields["temporal_lag_bars"],
                temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
                direction_aligned=direction_result.direction_aligned,
                pattern_allowed=pattern_gate_result.pattern_allowed,
                entry_signal=signal_result.entry_signal,
                trade_ok=False,
                fail_stage="dedup",
                decision_reason="recent_third_timestamp entry limit reached",
            )
            return None

        self._set_trace(
            bar_index=current_index,
            timestamp=current_bar.timestamp.isoformat(),
            close=current_bar.close,
            htf_bias=htf_context_result.htf_bias,
            wave_phase=wave_phase,
            wave_direction=structure_result.structure_direction,
            breakout_flag=breakout_flag,
            breakout_direction=str(temporal_meta.get("breakout_direction", "")),
            structure_candidate=structure_result.structure_candidate,
            structure_source=structure_source,
            temporal_candidate=temporal_candidate,
            recent_third_timestamp=recent_third_timestamp,
            recent_third_direction=temporal_fields["recent_third_direction"],
            temporal_lag_bars=temporal_fields["temporal_lag_bars"],
            temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
            direction_aligned=direction_result.direction_aligned,
            pattern_allowed=pattern_gate_result.pattern_allowed,
            entry_signal=signal_result.entry_signal,
            trade_ok=True,
            fail_stage="none",
            decision_reason=entry_reason,
        )

        return EntryEvent(
            entry_index=current_index,
            direction=direction,
            lot=risk_result.lot,
            stop_loss=risk_result.stop_loss or current_bar.close,
            take_profit=risk_result.take_profit or current_bar.close,
            entry_reason=entry_reason,
            signal_reason=signal_reason,
            risk_reason=risk_reason,
            filter_reason=filter_reason,
            fallback_used=fallback_used,
            structure_source=structure_source,
            recent_third_timestamp=recent_third_timestamp,
            recent_third_direction=str(temporal_fields["recent_third_direction"]),
            temporal_lag_bars=temporal_fields["temporal_lag_bars"],
            temporal_lookback_bars=temporal_fields["temporal_lookback_bars"],
            breakout_direction=temporal_meta.get("breakout_direction", ""),
        )

    def _allow_entry_for_recent_third_candidate(self, recent_third_timestamp: str) -> bool:
        limit = self._config.max_entries_per_recent_third_candidate
        if limit is None:
            return True
        if limit <= 0:
            return False
        if not recent_third_timestamp:
            return True
        current = self._recent_third_entry_counts.get(recent_third_timestamp, 0)
        if current >= limit:
            return False
        self._recent_third_entry_counts[recent_third_timestamp] = current + 1
        return True

    def _build_structure(self, window: List[PriceBar], context_reason: str):
        swing_result = SwingExtractor.extract(
            window,
            SwingConfig(window=self._config.swing_window, causal=self._config.swing_causal),
        )
        wave_result = WaveClassifier.classify(
            swing_result.swing_points,
            WaveConfig(min_swing_points=self._config.min_swing_points),
        )
        breakout_result = BreakoutDetector.detect(
            window,
            swing_result.swing_points,
            BreakoutConfig(use_close=self._config.breakout_use_close),
        )
        triangle_result = TriangleDetector.detect(
            ltf_price_frame=window,
            swing_points=swing_result.swing_points,
            triangle_config=TriangleConfig(
                lookback=self._config.triangle_lookback,
                tolerance=self._config.triangle_tolerance,
            ),
        )
        structure_result = StructureAssembler.assemble(
            wave_phase=wave_result.wave_phase,
            wave_direction=wave_result.wave_direction,
            breakout_flag=breakout_result.breakout_flag,
            breakout_direction=breakout_result.breakout_direction,
            triangle_flag=triangle_result.triangle_flag,
            sub_reasons=[
                context_reason,
                swing_result.swing_reason,
                wave_result.wave_reason,
                breakout_result.breakout_reason,
                triangle_result.triangle_reason,
            ],
        )

        if structure_result.structure_candidate:
            return structure_result, wave_result.wave_phase, breakout_result.breakout_flag, False, "detector_chain", {}

        temporal_result = self._build_temporal_third_break_structure(
            window=window,
            wave_phase=wave_result.wave_phase,
            breakout_flag=breakout_result.breakout_flag,
            breakout_direction=breakout_result.breakout_direction,
            context_reason=context_reason,
        )
        if temporal_result is not None:
            temporal_structure, temporal_meta = temporal_result
            return temporal_structure, "third", True, False, "detector_chain_temporal", temporal_meta

        # Minimal fallback to keep the adapter useful while detector outputs are still sparse.
        # TODO(TBD): remove this once LTF detector chain is fully connected in backtest path.
        if not self._config.allow_heuristic_fallback:
            return None, "unknown", False, False, "detector_chain", {}
        fallback = self._build_heuristic_structure(window, context_reason)
        fallback_wave_phase = "third" if fallback.structure_type == "third_wave_break" else "unknown"
        fallback_breakout_flag = bool(fallback.structure_candidate)
        return fallback, fallback_wave_phase, fallback_breakout_flag, True, "heuristic_fallback", {}

    def _build_heuristic_structure(self, window: List[PriceBar], context_reason: str):
        if len(window) < 2:
            return StructureAssembler.assemble(
                wave_phase="unknown",
                wave_direction="neutral",
                breakout_flag=False,
                breakout_direction="neutral",
                triangle_flag=False,
                sub_reasons=[context_reason, "insufficient bars for structure detection"],
            )

        current_bar = window[-1]
        previous_bar = window[-2]

        if current_bar.close > previous_bar.close:
            wave_direction = "long"
        elif current_bar.close < previous_bar.close:
            wave_direction = "short"
        else:
            wave_direction = "neutral"

        wave_phase = "third" if len(window) >= 3 and wave_direction in {"long", "short"} else "unknown"

        prior_bars = window[:-1]
        if wave_direction == "long":
            breakout_flag = current_bar.close > max(bar.high for bar in prior_bars)
            breakout_direction = "long" if breakout_flag else "neutral"
        elif wave_direction == "short":
            breakout_flag = current_bar.close < min(bar.low for bar in prior_bars)
            breakout_direction = "short" if breakout_flag else "neutral"
        else:
            breakout_flag = False
            breakout_direction = "neutral"

        return StructureAssembler.assemble(
            wave_phase=wave_phase,
            wave_direction=wave_direction,
            breakout_flag=breakout_flag,
            breakout_direction=breakout_direction,
            triangle_flag=False,
            sub_reasons=[context_reason, "fallback heuristic structure was used"],
        )

    def _build_temporal_third_break_structure(
        self,
        window: List[PriceBar],
        wave_phase: str,
        breakout_flag: bool,
        breakout_direction: str,
        context_reason: str,
    ) -> tuple[StructureResult, dict[str, object]] | None:
        if not self._config.allow_temporal_third_break:
            return None
        if wave_phase == "third":
            return None
        if not breakout_flag or breakout_direction not in {"long", "short"}:
            return None

        lookback_bars = max(1, int(self._config.third_candidate_lookback_bars))
        last_idx = len(window) - 1
        start_idx = max(0, last_idx - lookback_bars + 1)

        for idx in range(last_idx, start_idx - 1, -1):
            sub_window = window[: idx + 1]
            swing_result = SwingExtractor.extract(
                sub_window,
                SwingConfig(window=self._config.swing_window, causal=self._config.swing_causal),
            )
            historical_wave = WaveClassifier.classify(
                swing_result.swing_points,
                WaveConfig(min_swing_points=self._config.min_swing_points),
            )
            if historical_wave.wave_phase != "third":
                continue
            if historical_wave.wave_direction != breakout_direction:
                continue

            recent_bar = window[idx]
            reason = (
                "temporal third_wave_break candidate confirmed"
                f" | recent third candidate timestamp={recent_bar.timestamp.isoformat()}"
                f" | recent third direction={historical_wave.wave_direction}"
                f" | breakout_direction={breakout_direction}"
                f" | lookback bars={lookback_bars}"
            )
            return (
                StructureResult(
                    structure_type=STRUCTURE_THIRD_WAVE_BREAK,
                    structure_direction=breakout_direction,
                    structure_candidate=True,
                    pattern_reason=reason,
                    sub_reasons=[context_reason, reason],
                ),
                {
                    "recent_third_timestamp": recent_bar.timestamp.isoformat(),
                    "recent_third_direction": historical_wave.wave_direction,
                    "temporal_lag_bars": last_idx - idx,
                    "temporal_lookback_bars": lookback_bars,
                    "breakout_direction": breakout_direction,
                },
            )

        return None
