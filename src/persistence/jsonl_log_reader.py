from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List

from .types import PersistenceReadResult


class JsonlLogReader:
    @staticmethod
    def read(path: str, skip_invalid: bool = False) -> PersistenceReadResult:
        input_path = Path(path)
        warnings: list[str] = []
        data: list[Dict[str, Any]] = []

        if not input_path.exists():
            reason = f"JSONL read failed: path does not exist ({input_path})"
            return PersistenceReadResult(
                success=False,
                path=str(input_path.resolve()),
                record_count=0,
                data=[],
                persistence_reason=reason,
                warnings=[reason],
            )

        try:
            with input_path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue

                    try:
                        record = json.loads(stripped)
                        if isinstance(record, dict):
                            data.append(record)
                        else:
                            data.append({"value": record})
                    except JSONDecodeError as exc:
                        message = f"line {line_number}: {exc}"
                        if skip_invalid:
                            warnings.append(message)
                            continue
                        return PersistenceReadResult(
                            success=False,
                            path=str(input_path.resolve()),
                            record_count=len(data),
                            data=[],
                            persistence_reason=f"JSONL read failed at line {line_number}: {exc}",
                            warnings=[message],
                        )

            return PersistenceReadResult(
                success=True,
                path=str(input_path.resolve()),
                record_count=len(data),
                data=data,
                persistence_reason="JSONL read completed successfully",
                warnings=warnings,
            )
        except Exception as exc:
            reason = f"JSONL read failed: {exc}"
            warnings.append(str(exc))
            return PersistenceReadResult(
                success=False,
                path=str(input_path.resolve()),
                record_count=len(data),
                data=data,
                persistence_reason=reason,
                warnings=warnings,
            )
