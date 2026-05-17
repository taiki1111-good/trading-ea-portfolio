from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

from .types import PersistenceReadResult


def _normalize_value(value: str) -> Any:
    if value == "":
        return None

    normalized = value.strip()
    lowered = normalized.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        if "." in normalized:
            return float(normalized)
        return int(normalized)
    except ValueError:
        return normalized


class CsvLogReader:
    @staticmethod
    def read(path: str) -> PersistenceReadResult:
        input_path = Path(path)
        warnings: List[str] = []
        data: List[Dict[str, Any]] = []

        if not input_path.exists():
            reason = f"CSV read failed: path does not exist ({input_path})"
            warnings.append(reason)
            return PersistenceReadResult(
                success=False,
                path=str(input_path.resolve()),
                record_count=0,
                data=[],
                persistence_reason=reason,
                warnings=warnings,
            )

        try:
            with input_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    reason = "CSV read completed successfully but file has no header"
                    warnings.append(reason)
                    return PersistenceReadResult(
                        success=True,
                        path=str(input_path.resolve()),
                        record_count=0,
                        data=[],
                        persistence_reason=reason,
                        warnings=warnings,
                    )

                for row in reader:
                    normalized_row = {
                        key: _normalize_value(value) if value is not None else None
                        for key, value in row.items()
                    }
                    data.append(normalized_row)

            return PersistenceReadResult(
                success=True,
                path=str(input_path.resolve()),
                record_count=len(data),
                data=data,
                persistence_reason="CSV read completed successfully",
                warnings=warnings,
            )
        except Exception as exc:
            reason = f"CSV read failed: {exc}"
            warnings.append(reason)
            return PersistenceReadResult(
                success=False,
                path=str(input_path.resolve()),
                record_count=0,
                data=[],
                persistence_reason=reason,
                warnings=warnings,
            )
