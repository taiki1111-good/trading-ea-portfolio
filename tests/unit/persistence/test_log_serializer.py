from dataclasses import dataclass
from datetime import datetime, timezone

from src.logger.types import (
    DecisionLogRecord,
    EventLogRecord,
    LoggerBundle,
    StateLogRecord,
    TradeLogRecord,
)
from src.persistence.log_serializer import LogSerializer


@dataclass
class NestedType:
    label: str
    timestamp: datetime


@dataclass
class ContainerType:
    nested: NestedType
    value: int


def test_log_serializer_serializes_dataclass_to_dict():
    decision = DecisionLogRecord(signal_type="long_entry", structure_type="third_wave_break")
    serialized = LogSerializer.serialize(decision)

    assert isinstance(serialized, dict)
    assert serialized["signal_type"] == "long_entry"
    assert isinstance(serialized["log_time"], str)
    assert "T" in serialized["log_time"]


def test_log_serializer_serializes_logger_bundle_nested_dataclasses():
    bundle = LoggerBundle(
        decision_log=DecisionLogRecord(signal_type="short_entry"),
        trade_log=TradeLogRecord(order_result="filled", signal_type="short_entry"),
        state_log=StateLogRecord(
            previous_state="IDLE",
            next_state="ENTRY_PENDING",
            position_state="ENTRY_PENDING",
            transition_reason="transition test",
        ),
        event_log=EventLogRecord(event_type="price_signal", filter_reason="filter ok"),
    )
    serialized = LogSerializer.serialize(bundle)

    assert isinstance(serialized, dict)
    assert serialized["decision_log"]["signal_type"] == "short_entry"
    assert serialized["event_log"]["event_type"] == "price_signal"
    assert isinstance(serialized["trade_log"]["log_time"], str)


def test_log_serializer_serializes_nested_dataclass_values():
    now = datetime.now(timezone.utc)
    container = ContainerType(NestedType(label="nested", timestamp=now), value=123)
    serialized = LogSerializer.serialize(container)

    assert isinstance(serialized, dict)
    assert serialized["nested"]["label"] == "nested"
    assert serialized["nested"]["timestamp"] == now.isoformat()
