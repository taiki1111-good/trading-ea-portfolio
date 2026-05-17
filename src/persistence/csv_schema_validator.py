from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set

from .types import BacktestLogConsistencyResult, CsvSchemaValidationResult

SCHEMA_REQUIRED_COLUMNS: Dict[str, Set[str]] = {
    "decision_logs": {
        "log_time",
        "bar_index",
        "timestamp",
        "close",
        "htf_bias",
        "wave_phase",
        "wave_direction",
        "breakout_flag",
        "breakout_direction",
        "structure_candidate",
        "structure_source",
        "temporal_candidate",
        "recent_third_timestamp",
        "recent_third_direction",
        "temporal_lag_bars",
        "temporal_lookback_bars",
        "direction_aligned",
        "pattern_allowed",
        "entry_signal",
        "trade_ok",
        "fail_stage",
        "decision_reason",
    },
    "trade_logs": {
        "log_time",
        "order_result",
        "lot",
        "fill_price",
        "execution_price",
        "stop_loss",
        "take_profit",
    },
    "state_logs": {
        "log_time",
        "previous_state",
        "next_state",
        "position_state",
        "transition_reason",
        "order_result",
        "execution_reason",
    },
    "event_logs": {
        "log_time",
        "event_flag",
        "event_type",
        "event_risk_flag",
        "filter_reason",
    },
}

POSITION_STATES = {"IDLE", "ENTRY_PENDING", "POSITION_OPEN", "EXIT_PENDING", "SUSPENDED", "ERROR"}
ORDER_RESULTS = {"filled", "rejected", "cancelled", "failed", "none"}
SIGNAL_TYPES = {"long_entry", "short_entry", "none"}
FAIL_STAGES = {"structure", "direction_alignment", "pattern_gate", "signal", "risk_filter", "dedup", "none"}
KNOWN_STRUCTURE_SOURCES = {"detector_chain", "detector_chain_temporal", "heuristic_fallback"}
NONE_LIKE_STRINGS = {"", "none", "null", "na", "n/a"}
KNOWN_TRADE_LOG_COLUMNS = {
    "log_time",
    "entry_time",
    "exit_time",
    "signal_type",
    "order_result",
    "lot",
    "fill_price",
    "execution_price",
    "stop_loss",
    "take_profit",
    "pnl",
    "realized_pnl",
    "exit_reason",
    "entry_reason",
    "signal_reason",
    "risk_reason",
    "filter_reason",
    "fallback_used",
    "structure_source",
    "recent_third_timestamp",
    "recent_third_direction",
    "temporal_lag_bars",
    "temporal_lookback_bars",
    "breakout_direction",
    # experimental backtest columns
    "entry_time_mode",
    "exit_policy",
    "holding_bars",
    "trailing_activation_R",
}
KNOWN_DECISION_LOG_COLUMNS = {
    "log_time",
    "bar_index",
    "timestamp",
    "close",
    "htf_bias",
    "wave_phase",
    "wave_direction",
    "breakout_flag",
    "breakout_direction",
    "structure_candidate",
    "structure_source",
    "temporal_candidate",
    "recent_third_timestamp",
    "recent_third_direction",
    "temporal_lag_bars",
    "temporal_lookback_bars",
    "direction_aligned",
    "pattern_allowed",
    "entry_signal",
    "trade_ok",
    "fail_stage",
    "decision_reason",
    # HTF filter v1 trace columns (optional)
    "htf_filter_enabled",
    "htf_timeframe_policy",
    "htf_neutral_policy",
    "htf_trend_dir",
    "htf_direction_aligned",
    "htf_filter_reason",
    "htf_context_reason",
}


class CsvSchemaValidator:
    @staticmethod
    def validate_records(schema_name: str, records: Iterable[Dict[str, Any]]) -> CsvSchemaValidationResult:
        required_columns = SCHEMA_REQUIRED_COLUMNS.get(schema_name)
        if required_columns is None:
            return CsvSchemaValidationResult(
                valid=False,
                schema_name=schema_name,
                validation_reason=f"unsupported schema_name: {schema_name}",
                warnings=["schema name is not recognized in initial CSV validator"],
            )

        record_list = list(records)
        observed_columns: Set[str] = set()
        for record in record_list:
            observed_columns.update(record.keys())

        missing_columns = sorted(required_columns - observed_columns)
        known_columns = CsvSchemaValidator._known_columns_for_schema(schema_name, required_columns)
        extra_columns = sorted(observed_columns - known_columns)
        warnings: List[str] = []
        if extra_columns:
            warnings.append(f"unknown extra columns are present: {extra_columns}")

        valid = True
        if missing_columns:
            valid = False

        enum_warnings, enum_errors = CsvSchemaValidator._validate_minimal_enums(schema_name, record_list)
        warnings.extend(enum_warnings)
        if enum_errors:
            valid = False

        temporal_errors = []
        if schema_name == "decision_logs":
            temporal_errors = CsvSchemaValidator._validate_decision_log_temporal_consistency(record_list)
            if temporal_errors:
                valid = False

        reasons: List[str] = []
        if missing_columns:
            reasons.append(f"missing required columns for {schema_name}")
        if enum_errors:
            reasons.append("enum/value validation failed")
        if temporal_errors:
            reasons.append("temporal consistency validation failed")
        if not reasons:
            reasons.append(f"required columns and validation checks passed for {schema_name}")

        warnings.extend(enum_errors)
        warnings.extend(temporal_errors)

        return CsvSchemaValidationResult(
            valid=valid,
            schema_name=schema_name,
            missing_columns=missing_columns,
            extra_columns=extra_columns,
            validation_reason="; ".join(reasons),
            warnings=warnings,
        )

    @staticmethod
    def validate_backtest_log_consistency(
        trade_logs: Iterable[Dict[str, Any]],
        decision_logs: Iterable[Dict[str, Any]],
    ) -> BacktestLogConsistencyResult:
        trades = list(trade_logs)
        decisions = list(decision_logs)
        warnings: List[str] = []

        trade_count = len(trades)
        trade_ok_true_count = sum(1 for row in decisions if CsvSchemaValidator._as_bool(row.get("trade_ok")) is True)
        if trade_ok_true_count != trade_count:
            return BacktestLogConsistencyResult(
                valid=False,
                consistency_reason=(
                    f"trade_ok=true decision log count ({trade_ok_true_count}) does not match trade log count ({trade_count})"
                ),
                warnings=warnings,
            )

        trade_sources = {CsvSchemaValidator._normalize_text(row.get("structure_source")) for row in trades}
        decision_sources = {CsvSchemaValidator._normalize_text(row.get("structure_source")) for row in decisions}

        unknown_trade_sources = sorted(
            source for source in trade_sources if source and source not in KNOWN_STRUCTURE_SOURCES
        )
        unknown_decision_sources = sorted(
            source for source in decision_sources if source and source not in KNOWN_STRUCTURE_SOURCES
        )

        if unknown_trade_sources or unknown_decision_sources:
            return BacktestLogConsistencyResult(
                valid=False,
                consistency_reason="unknown structure_source detected",
                warnings=[
                    f"unknown trade structure_source values: {unknown_trade_sources}",
                    f"unknown decision structure_source values: {unknown_decision_sources}",
                ],
            )

        fallback_used_false_for_all = all(CsvSchemaValidator._as_bool(row.get("fallback_used")) is False for row in trades)
        if fallback_used_false_for_all:
            heuristic_count = sum(1 for row in decisions if CsvSchemaValidator._normalize_text(row.get("structure_source")) == "heuristic_fallback")
            if heuristic_count > 0:
                return BacktestLogConsistencyResult(
                    valid=False,
                    consistency_reason="trade logs indicate fallback_used=false, but decision logs include heuristic_fallback",
                    warnings=[f"heuristic_fallback decision log rows: {heuristic_count}"],
                )

        return BacktestLogConsistencyResult(
            valid=True,
            consistency_reason="trade and decision logs are consistent",
            warnings=warnings,
        )

    @staticmethod
    def _validate_minimal_enums(schema_name: str, records: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        warnings: List[str] = []
        errors: List[str] = []

        if schema_name == "state_logs":
            for index, record in enumerate(records, start=1):
                position_state = record.get("position_state")
                if position_state is not None and str(position_state) not in POSITION_STATES:
                    warnings.append(f"row {index}: position_state={position_state} is outside allowed initial enum set")

        if schema_name in {"trade_logs", "state_logs"}:
            for index, record in enumerate(records, start=1):
                order_result = record.get("order_result")
                if order_result is not None and str(order_result) not in ORDER_RESULTS:
                    warnings.append(f"row {index}: order_result={order_result} is outside allowed initial enum set")

        if schema_name == "trade_logs":
            for index, record in enumerate(records, start=1):
                signal_type = CsvSchemaValidator._normalize_text(record.get("signal_type"))
                if signal_type and signal_type not in SIGNAL_TYPES:
                    errors.append(f"row {index}: signal_type={record.get('signal_type')} is outside allowed enum set")

                structure_source = CsvSchemaValidator._normalize_text(record.get("structure_source"))
                if structure_source and structure_source not in KNOWN_STRUCTURE_SOURCES:
                    errors.append(
                        f"row {index}: structure_source={record.get('structure_source')} is outside allowed enum set"
                    )

                fallback_used = CsvSchemaValidator._as_bool(record.get("fallback_used"))
                if (not CsvSchemaValidator._is_none_like(record.get("fallback_used"))) and fallback_used is None:
                    errors.append(f"row {index}: fallback_used={record.get('fallback_used')} is not bool-like")

        if schema_name == "decision_logs":
            for index, record in enumerate(records, start=1):
                fail_stage = CsvSchemaValidator._normalize_text(record.get("fail_stage"))
                if fail_stage and fail_stage not in FAIL_STAGES:
                    errors.append(f"row {index}: fail_stage={record.get('fail_stage')} is outside allowed enum set")

                structure_source = CsvSchemaValidator._normalize_text(record.get("structure_source"))
                if structure_source and structure_source not in KNOWN_STRUCTURE_SOURCES:
                    errors.append(
                        f"row {index}: structure_source={record.get('structure_source')} is outside allowed enum set"
                    )

        return warnings, errors

    @staticmethod
    def _known_columns_for_schema(schema_name: str, required_columns: Set[str]) -> Set[str]:
        if schema_name == "trade_logs":
            return set(KNOWN_TRADE_LOG_COLUMNS)
        if schema_name == "decision_logs":
            return set(KNOWN_DECISION_LOG_COLUMNS)
        return set(required_columns)

    @staticmethod
    def _validate_decision_log_temporal_consistency(records: List[Dict[str, Any]]) -> List[str]:
        errors: List[str] = []

        for index, record in enumerate(records, start=1):
            temporal_candidate = CsvSchemaValidator._as_bool(record.get("temporal_candidate"))
            recent_ts_non_empty = CsvSchemaValidator._is_non_empty(record.get("recent_third_timestamp"))
            recent_dir_non_empty = CsvSchemaValidator._is_non_empty(record.get("recent_third_direction"))
            lag_non_empty = CsvSchemaValidator._is_non_empty(record.get("temporal_lag_bars"))
            lookback_non_empty = CsvSchemaValidator._is_non_empty(record.get("temporal_lookback_bars"))

            if temporal_candidate is True:
                if not recent_ts_non_empty:
                    errors.append(f"row {index}: temporal_candidate=true requires recent_third_timestamp")
                if not lag_non_empty:
                    errors.append(f"row {index}: temporal_candidate=true requires temporal_lag_bars")
                if not lookback_non_empty:
                    errors.append(f"row {index}: temporal_candidate=true requires temporal_lookback_bars")
            elif temporal_candidate is False:
                if recent_ts_non_empty:
                    errors.append(f"row {index}: temporal_candidate=false requires empty recent_third_timestamp")
                if recent_dir_non_empty:
                    errors.append(f"row {index}: temporal_candidate=false requires empty recent_third_direction")
                if lag_non_empty:
                    errors.append(f"row {index}: temporal_candidate=false requires empty temporal_lag_bars")
                if lookback_non_empty:
                    errors.append(f"row {index}: temporal_candidate=false requires empty temporal_lookback_bars")

        return errors

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    @staticmethod
    def _is_none_like(value: Any) -> bool:
        text = CsvSchemaValidator._normalize_text(value)
        return text in NONE_LIKE_STRINGS

    @staticmethod
    def _is_non_empty(value: Any) -> bool:
        return not CsvSchemaValidator._is_none_like(value)

    @staticmethod
    def _as_bool(value: Any) -> bool | None:
        text = CsvSchemaValidator._normalize_text(value)
        if text == "true":
            return True
        if text == "false":
            return False
        return None
