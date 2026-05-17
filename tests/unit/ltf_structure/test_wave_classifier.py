from datetime import datetime, timezone

from src.ltf_structure.types import SwingPoint
from src.ltf_structure.wave_classifier import WaveClassifier


def test_wave_classifier_returns_third_long():
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.0000, swing_type="low"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=1.1000, swing_type="high"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), price=1.0500, swing_type="low"),
    ]

    result = WaveClassifier.classify(swing_points)

    assert result.wave_phase == "third"
    assert result.wave_direction == "long"
    assert result.wave_reason


def test_wave_classifier_returns_third_short():
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.1500, swing_type="high"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=1.0500, swing_type="low"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), price=1.1000, swing_type="high"),
    ]

    result = WaveClassifier.classify(swing_points)

    assert result.wave_phase == "third"
    assert result.wave_direction == "short"
    assert result.wave_reason


def test_wave_classifier_returns_unknown_and_neutral():
    swing_points = [
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), price=1.0000, swing_type="low"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), price=1.0500, swing_type="high"),
        SwingPoint(timestamp=datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc), price=0.9900, swing_type="low"),
    ]

    result = WaveClassifier.classify(swing_points)

    assert result.wave_phase == "unknown"
    assert result.wave_direction == "neutral"
    assert result.wave_reason
