from src.risk_filter.position_sizer import PositionSizer
from src.risk_filter.types import PositionSizerConfig


def test_position_sizer_returns_fixed_lot_when_balance_positive():
    config = PositionSizerConfig(fixed_lot=0.1)
    result = PositionSizer.size(1000.0, config)

    assert result.lot == 0.1
    assert "placeholder_fixed_lot" in result.size_reason


def test_position_sizer_returns_none_when_balance_non_positive():
    config = PositionSizerConfig(fixed_lot=0.1)
    result = PositionSizer.size(0.0, config)

    assert result.lot is None
    assert "invalid_lot" in result.size_reason
    assert "invalid_account_balance" in result.size_reason


def test_position_sizer_returns_none_when_fixed_lot_is_invalid():
    config = PositionSizerConfig(fixed_lot=0.0)
    result = PositionSizer.size(1000.0, config)

    assert result.lot is None
    assert "invalid_lot" in result.size_reason


def test_position_sizer_returns_none_when_balance_is_invalid_number():
    config = PositionSizerConfig(fixed_lot=0.1)

    for balance in [None, True, float("nan"), float("inf"), float("-inf"), "1000"]:  # type: ignore[list-item]
        result = PositionSizer.size(balance, config)  # type: ignore[arg-type]
        assert result.lot is None
        assert "invalid_lot" in result.size_reason
        assert "invalid_account_balance" in result.size_reason


def test_position_sizer_returns_none_when_fixed_lot_is_invalid_number():
    for fixed_lot in [None, True, float("nan"), float("inf"), float("-inf"), "0.1"]:  # type: ignore[list-item]
        config = PositionSizerConfig(fixed_lot=fixed_lot)  # type: ignore[arg-type]
        result = PositionSizer.size(1000.0, config)
        assert result.lot is None
        assert "invalid_lot" in result.size_reason
