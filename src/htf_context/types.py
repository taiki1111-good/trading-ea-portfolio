from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, List

from src.data.types import PriceFrame

HTFTrendDir = Literal["up", "down", "neutral"]
HTFBias = Literal["long_bias", "short_bias", "neutral"]

HTF_TREND_UP: HTFTrendDir = "up"
HTF_TREND_DOWN: HTFTrendDir = "down"
HTF_TREND_NEUTRAL: HTFTrendDir = "neutral"

HTF_BIAS_LONG: HTFBias = "long_bias"
HTF_BIAS_SHORT: HTFBias = "short_bias"
HTF_BIAS_NEUTRAL: HTFBias = "neutral"


@dataclass(frozen=True)
class TrendConfig:
    lookback: int = 3
    min_strength: float = 0.1


@dataclass(frozen=True)
class ResistanceConfig:
    lookback: int = 3
    min_distance: float = 0.01


@dataclass(frozen=True)
class SupportConfig:
    lookback: int = 3
    min_distance: float = 0.01


@dataclass(frozen=True)
class TrendResult:
    htf_trend_dir: HTFTrendDir
    htf_trend_strength: float
    trend_reason: str


@dataclass(frozen=True)
class ResistanceResult:
    htf_resistance_ok: bool
    resistance_reason: str


@dataclass(frozen=True)
class SupportResult:
    htf_support_ok: bool
    support_reason: str


@dataclass(frozen=True)
class HTFContextResult:
    htf_trend_dir: HTFTrendDir
    htf_trend_strength: float
    htf_resistance_ok: bool
    htf_support_ok: bool
    htf_bias: HTFBias
    htf_context_reason: str
    sub_reasons: List[str] = field(default_factory=list)
