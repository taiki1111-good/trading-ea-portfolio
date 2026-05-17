from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .log_serializer import LogSerializer
from .types import PersistenceWriteResult


def _flatten_record(value: Any, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    if isinstance(value, dict):
        items: Dict[str, Any] = {}
        for key, item in value.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else str(key)
            items.update(_flatten_record(item, new_key, sep=sep))
        return items

    if isinstance(value, list):
        return {parent_key: json.dumps(value, ensure_ascii=False)}

    return {parent_key: value}


class CsvLogWriter:
    @staticmethod
    def write(path: str, records: Iterable[Any], append: bool = True) -> PersistenceWriteResult:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        prepared_rows: List[Dict[str, Any]] = []
        warnings: List[str] = []

        for record in records:
            serialized = LogSerializer.serialize(record)
            if not isinstance(serialized, dict):
                warnings.append("record could not be serialized to a dict and was skipped")
                continue
            flat_record: Dict[str, Any] = {}
            for key, value in serialized.items():
                flat_record.update(_flatten_record(value, parent_key=key))
            prepared_rows.append(flat_record)

        if not prepared_rows:
            reason = "No serializable records provided for CSV write"
            return PersistenceWriteResult(
                success=False,
                path=str(output_path.resolve()),
                record_count=0,
                persistence_reason=reason,
                warnings=warnings,
            )

        header_fields = sorted({key for row in prepared_rows for key in row.keys()})
        mode = "a" if append else "w"

        if append and output_path.exists() and output_path.stat().st_size > 0:
            with output_path.open("r", encoding="utf-8", newline="") as existing_handle:
                existing_reader = csv.DictReader(existing_handle)
                if existing_reader.fieldnames is not None:
                    existing_header = existing_reader.fieldnames
                    extra_keys = [key for key in header_fields if key not in existing_header]
                    if extra_keys:
                        warnings.append(
                            f"CSV append skipped extra columns: {extra_keys}"
                        )
                    header_fields = existing_header

        try:
            with output_path.open(mode, encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=header_fields, extrasaction="ignore")
                if not append or output_path.stat().st_size == 0:
                    writer.writeheader()
                writer.writerows(prepared_rows)

            return PersistenceWriteResult(
                success=True,
                path=str(output_path.resolve()),
                record_count=len(prepared_rows),
                persistence_reason="CSV write completed successfully",
                warnings=warnings,
            )
        except Exception as exc:
            warnings.append(str(exc))
            return PersistenceWriteResult(
                success=False,
                path=str(output_path.resolve()),
                record_count=0,
                persistence_reason=f"CSV write failed: {exc}",
                warnings=warnings,
            )
