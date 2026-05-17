from datetime import datetime, timezone

from src.backtest.position_tracker import PositionTracker
from src.backtest.types import BacktestPosition


def _pos() -> BacktestPosition:
    return BacktestPosition(
        direction="long",
        entry_price=100.0,
        entry_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lot=1.0,
        stop_loss=99.0,
        take_profit=101.0,
        entry_index=0,
    )


def test_position_tracker_open_close():
    tracker = PositionTracker()
    assert not tracker.has_open_position()
    assert tracker.get_position() is None

    assert tracker.open_position(_pos()) is True
    assert tracker.has_open_position()
    assert tracker.get_position() is not None

    closed = tracker.close_position()
    assert closed is not None
    assert not tracker.has_open_position()


def test_position_tracker_blocks_entry_when_holding():
    tracker = PositionTracker()
    assert tracker.open_position(_pos()) is True
    assert tracker.open_position(_pos()) is False

