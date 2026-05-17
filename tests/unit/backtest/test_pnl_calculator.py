import pytest

from src.backtest.pnl_calculator import PnLCalculator


def test_pnl_calculator_long_pnl():
    pnl = PnLCalculator.calculate(direction="long", entry_price=100.0, exit_price=101.0, lot=1.0)
    assert pnl == pytest.approx(1.0)


def test_pnl_calculator_short_pnl():
    pnl = PnLCalculator.calculate(direction="short", entry_price=100.0, exit_price=99.0, lot=1.0)
    assert pnl == pytest.approx(1.0)


def test_pnl_calculator_applies_lot():
    pnl = PnLCalculator.calculate(direction="long", entry_price=100.0, exit_price=101.0, lot=0.5)
    assert pnl == pytest.approx(0.5)


def test_pnl_calculator_rejects_invalid_direction():
    with pytest.raises(ValueError):
        PnLCalculator.calculate(direction="broken", entry_price=100.0, exit_price=101.0, lot=1.0)

