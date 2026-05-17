from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal

from src.data.types import PriceFrame

SwingType = Literal["high", "low"]
WavePhase = Literal["first", "second", "third", "unknown"]
WaveDirection = Literal["long", "short", "neutral"]
StructureDirection = Literal["long", "short", "neutral"]
StructureType = Literal["third_wave_break", "triangle_break", "none"]
BreakoutDirection = StructureDirection

STRUCTURE_THIRD_WAVE_BREAK: StructureType = "third_wave_break"
STRUCTURE_TRIANGLE_BREAK: StructureType = "triangle_break"
STRUCTURE_NONE: StructureType = "none"

WAVE_PHASE_UNKNOWN: WavePhase = "unknown"
WAVE_DIRECTION_LONG: WaveDirection = "long"
WAVE_DIRECTION_SHORT: WaveDirection = "short"
WAVE_DIRECTION_NEUTRAL: WaveDirection = "neutral"

BREAKOUT_DIRECTION_NEUTRAL: BreakoutDirection = "neutral"


@dataclass(frozen=True)
class SwingConfig:
    window: int = 2
    causal: bool = True


@dataclass(frozen=True)
class WaveConfig:
    min_swing_points: int = 3


@dataclass(frozen=True)
class BreakoutConfig:
    # Initial main uses close-price breakout only.
    use_close: bool = True


@dataclass(frozen=True)
class TriangleConfig:
    lookback: int = 5
    tolerance: float = 0.01


@dataclass(frozen=True)
class SwingPoint:
    timestamp: datetime
    price: float
    swing_type: SwingType


@dataclass(frozen=True)
class SwingResult:
    swing_points: List[SwingPoint]
    swing_reason: str


@dataclass(frozen=True)
class WaveResult:
    wave_phase: WavePhase
    wave_direction: WaveDirection
    wave_reason: str


@dataclass(frozen=True)
class BreakoutResult:
    breakout_flag: bool
    breakout_direction: BreakoutDirection
    breakout_level: float
    breakout_reason: str


@dataclass(frozen=True)
class TriangleResult:
    triangle_flag: bool
    triangle_direction_hint: WaveDirection
    triangle_reason: str


@dataclass(frozen=True)
class StructureResult:
    structure_type: StructureType
    structure_direction: StructureDirection
    structure_candidate: bool
    pattern_reason: str
    sub_reasons: List[str] = field(default_factory=list)
