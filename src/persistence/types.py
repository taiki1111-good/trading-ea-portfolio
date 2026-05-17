from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class PersistenceWriteResult:
    success: bool
    path: str
    record_count: int
    persistence_reason: str
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PersistenceReadResult:
    success: bool
    path: str
    record_count: int
    data: List[Dict[str, Any]] = field(default_factory=list)
    persistence_reason: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CsvSchemaValidationResult:
    valid: bool
    schema_name: str
    missing_columns: List[str] = field(default_factory=list)
    extra_columns: List[str] = field(default_factory=list)
    validation_reason: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestLogConsistencyResult:
    valid: bool
    consistency_reason: str = ""
    warnings: List[str] = field(default_factory=list)
