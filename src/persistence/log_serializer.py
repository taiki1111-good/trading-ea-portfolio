from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Dict


class LogSerializer:
    @staticmethod
    def serialize(value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, datetime):
            return value.isoformat()

        if is_dataclass(value):
            return LogSerializer.serialize(asdict(value))

        if isinstance(value, dict):
            return {str(key): LogSerializer.serialize(item) for key, item in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [LogSerializer.serialize(item) for item in value]

        if hasattr(value, "to_dict") and callable(value.to_dict):
            try:
                return LogSerializer.serialize(value.to_dict())
            except Exception:
                pass

        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)
