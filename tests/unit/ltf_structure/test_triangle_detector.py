from src.ltf_structure.triangle_detector import TriangleDetector


def test_triangle_detector_returns_reserved_false_neutral_for_initial_main():
    result = TriangleDetector.detect([], [])

    assert result.triangle_flag is False
    assert result.triangle_direction_hint == "neutral"
    assert "reserved for experiments" in result.triangle_reason
