from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .log_serializer import LogSerializer
from .types import PersistenceWriteResult


class JsonlLogWriter:
    @staticmethod
    def write(path: str, records: Iterable[Any], append: bool = True) -> PersistenceWriteResult:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        record_count = 0
        warnings: list[str] = []

        try:
            with output_path.open(mode, encoding="utf-8") as handle:
                for record in records:
                    serialized = LogSerializer.serialize(record)
                    handle.write(json.dumps(serialized, ensure_ascii=False))
                    handle.write("\n")
                    record_count += 1

            return PersistenceWriteResult(
                success=True,
                path=str(output_path.resolve()),
                record_count=record_count,
                persistence_reason="JSONL write completed successfully",
                warnings=warnings,
            )
        except Exception as exc:
            warnings.append(str(exc))
            return PersistenceWriteResult(
                success=False,
                path=str(output_path.resolve()),
                record_count=record_count,
                persistence_reason=f"JSONL write failed: {exc}",
                warnings=warnings,
            )
