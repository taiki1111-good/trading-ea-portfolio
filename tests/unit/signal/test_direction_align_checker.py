from src.signal.direction_align_checker import DirectionAlignChecker


def test_direction_align_checker_long_bias_long_structure_is_true():
    result = DirectionAlignChecker.check("long_bias", "long")
    assert result.direction_aligned is True
    assert result.direction_reason


def test_direction_align_checker_short_bias_short_structure_is_true():
    result = DirectionAlignChecker.check("short_bias", "short")
    assert result.direction_aligned is True
    assert result.direction_reason


def test_direction_align_checker_long_bias_short_structure_is_false():
    result = DirectionAlignChecker.check("long_bias", "short")
    assert result.direction_aligned is False
    assert "mismatch" in result.direction_reason


def test_direction_align_checker_neutral_bias_is_false():
    result = DirectionAlignChecker.check("neutral", "long")
    assert result.direction_aligned is False
    assert "neutral" in result.direction_reason
