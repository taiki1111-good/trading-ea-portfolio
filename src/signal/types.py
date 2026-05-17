from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, List

from src.htf_context.types import HTFBias
from src.ltf_structure.types import StructureDirection, StructureType, WavePhase

SignalType = Literal["long_entry", "short_entry", "exit", "none"]

SIGNAL_LONG_ENTRY: SignalType = "long_entry"
SIGNAL_SHORT_ENTRY: SignalType = "short_entry"
SIGNAL_EXIT: SignalType = "exit"
SIGNAL_NONE: SignalType = "none"


@dataclass(frozen=True)
class DirectionAlignResult:
    direction_aligned: bool
    direction_reason: str


@dataclass(frozen=True)
class PatternGateResult:
    pattern_allowed: bool
    gate_reason: str


@dataclass(frozen=True)
class EntryRuleResult:
    entry_signal: bool
    signal_type: SignalType
    entry_reason: str


@dataclass(frozen=True)
class ExitRuleResult:
    exit_signal: bool
    exit_reason: str


@dataclass(frozen=True)
class SignalInput:
    # TODO(TBD): keep this as a future boundary DTO candidate.
    # Decide in RiskFilter-prep phase whether to adopt this end-to-end or remove it.
    htf_bias: HTFBias
    structure_direction: StructureDirection
    structure_type: StructureType
    structure_candidate: bool
    breakout_flag: bool
    wave_phase: WavePhase
    htf_context_reason: str
    pattern_reason: str


@dataclass(frozen=True)
class SignalResult:
    entry_signal: bool
    exit_signal: bool
    signal_type: SignalType
    signal_reason: str
    direction_aligned: bool
    pattern_allowed: bool
    sub_reasons: List[str] = field(default_factory=list)
