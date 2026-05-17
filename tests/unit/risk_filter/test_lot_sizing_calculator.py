import math

from src.risk_filter.lot_sizing_calculator import (
    LotSizingCalculator,
    LotSizingV1Config,
)
from src.risk_filter.position_sizer import PositionSizer
from src.risk_filter.types import PositionSizerConfig


def _base_config() -> LotSizingV1Config:
    return LotSizingV1Config(
        account_balance=1000.0,
        risk_per_trade=0.01,
        stop_loss_distance_pips=20.0,
        pip_value_per_lot=10.0,
        lot_step=0.01,
        min_lot=0.01,
        max_lot=2.0,
        rounding_mode="floor",
    )


def test_formula_normal_case():
    result = LotSizingCalculator.calculate(_base_config())

    assert result.lot == 0.05
    assert result.raw_lot == 0.05
    assert result.rounded_lot == 0.05
    assert result.clamped_flag is False
    assert result.size_reason == "lot_sizing_v1_applied"


def test_floor_rounding_applies_to_step():
    config = _base_config()
    config = LotSizingV1Config(**{**config.__dict__, "risk_per_trade": 0.01019})

    result = LotSizingCalculator.calculate(config)

    assert result.raw_lot is not None
    assert result.raw_lot > 0.05
    assert result.rounded_lot == 0.05
    assert result.lot == 0.05


def test_max_lot_clamp():
    config = _base_config()
    config = LotSizingV1Config(**{**config.__dict__, "risk_per_trade": 0.8, "max_lot": 0.2})

    result = LotSizingCalculator.calculate(config)

    assert result.raw_lot == 4.0
    assert result.rounded_lot == 4.0
    assert result.lot == 0.2
    assert result.clamped_flag is True
    assert result.size_reason == "lot_sizing_v1_applied:max_lot_clamped"


def test_below_min_lot_is_invalid():
    config = _base_config()
    config = LotSizingV1Config(
        **{
            **config.__dict__,
            "account_balance": 10.0,
            "risk_per_trade": 0.001,
            "min_lot": 0.01,
        }
    )

    result = LotSizingCalculator.calculate(config)

    assert result.lot is None
    assert result.raw_lot == 0.00005
    assert result.rounded_lot == 0.0
    assert result.clamped_flag is False
    assert result.size_reason == "invalid_lot_sizing_input: below_min_lot"


def test_risk_per_trade_greater_equal_one_is_invalid():
    config = _base_config()
    config = LotSizingV1Config(**{**config.__dict__, "risk_per_trade": 1.0})

    result = LotSizingCalculator.calculate(config)

    assert result.lot is None
    assert result.size_reason == "invalid_lot_sizing_input: risk_per_trade"


def test_non_positive_values_are_invalid():
    base = _base_config()
    invalid_cases = [
        {"account_balance": 0.0, "expected": "account_balance"},
        {"risk_per_trade": 0.0, "expected": "risk_per_trade"},
        {"stop_loss_distance_pips": 0.0, "expected": "stop_loss_distance_pips"},
        {"pip_value_per_lot": 0.0, "expected": "pip_value_per_lot"},
        {"lot_step": 0.0, "expected": "lot_step"},
        {"min_lot": 0.0, "expected": "min_lot"},
        {"max_lot": 0.0, "expected": "max_lot"},
    ]

    for case in invalid_cases:
        updated = dict(base.__dict__)
        updated.update({k: v for k, v in case.items() if k != "expected"})
        result = LotSizingCalculator.calculate(LotSizingV1Config(**updated))
        assert result.lot is None
        assert result.size_reason == f"invalid_lot_sizing_input: {case['expected']}"


def test_bool_values_are_invalid():
    base = _base_config()
    bool_fields = [
        "account_balance",
        "risk_per_trade",
        "stop_loss_distance_pips",
        "pip_value_per_lot",
        "lot_step",
        "min_lot",
        "max_lot",
    ]
    for field in bool_fields:
        updated = dict(base.__dict__)
        updated[field] = True
        result = LotSizingCalculator.calculate(LotSizingV1Config(**updated))
        assert result.lot is None
        assert result.size_reason == f"invalid_lot_sizing_input: {field}"


def test_nan_and_inf_are_invalid():
    base = _base_config()
    invalid_numbers = [float("nan"), float("inf"), float("-inf")]
    fields = [
        "account_balance",
        "risk_per_trade",
        "stop_loss_distance_pips",
        "pip_value_per_lot",
        "lot_step",
        "min_lot",
        "max_lot",
    ]
    for field in fields:
        for value in invalid_numbers:
            updated = dict(base.__dict__)
            updated[field] = value
            result = LotSizingCalculator.calculate(LotSizingV1Config(**updated))
            assert result.lot is None
            assert result.size_reason == f"invalid_lot_sizing_input: {field}"


def test_unsupported_rounding_mode_is_invalid():
    config = _base_config()
    config = LotSizingV1Config(**{**config.__dict__, "rounding_mode": "ceil"})

    result = LotSizingCalculator.calculate(config)

    assert result.lot is None
    assert result.size_reason == "invalid_lot_sizing_input: rounding_mode"


def test_min_lot_greater_than_max_lot_is_invalid():
    config = _base_config()
    config = LotSizingV1Config(**{**config.__dict__, "min_lot": 0.2, "max_lot": 0.1})

    result = LotSizingCalculator.calculate(config)

    assert result.lot is None
    assert result.size_reason == "invalid_lot_sizing_input: min_gt_max"


def test_min_lot_step_mismatch_is_invalid():
    config = _base_config()
    config = LotSizingV1Config(**{**config.__dict__, "min_lot": 0.015})

    result = LotSizingCalculator.calculate(config)

    assert result.lot is None
    assert result.size_reason == "invalid_lot_sizing_input: min_lot_step_mismatch"


def test_max_lot_step_mismatch_is_invalid():
    config = _base_config()
    config = LotSizingV1Config(**{**config.__dict__, "max_lot": 2.005})

    result = LotSizingCalculator.calculate(config)

    assert result.lot is None
    assert result.size_reason == "invalid_lot_sizing_input: max_lot_step_mismatch"


def test_position_sizer_fixed_lot_baseline_is_unchanged():
    config = PositionSizerConfig(fixed_lot=0.1)
    result = PositionSizer.size(1000.0, config)

    assert result.lot == 0.1
    assert "placeholder_fixed_lot" in result.size_reason
