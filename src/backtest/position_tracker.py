from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .types import BacktestPosition


@dataclass
class PositionTracker:
    """Tracks a single open position for initial skeleton."""

    _position: Optional[BacktestPosition] = None

    def has_open_position(self) -> bool:
        return self._position is not None

    def get_position(self) -> Optional[BacktestPosition]:
        return self._position

    def open_position(self, position: BacktestPosition) -> bool:
        if self._position is not None:
            return False
        self._position = position
        return True

    def close_position(self) -> Optional[BacktestPosition]:
        if self._position is None:
            return None
        pos = self._position
        self._position = None
        return pos

