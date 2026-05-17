from __future__ import annotations

import math
from dataclasses import dataclass

_REASON_APPLIED = "lot_sizing_v1_applied"
_REASON_APPLIED_CLAMPED = "lot_sizing_v1_applied:max_lot_clamped"
_REASON_INVALID_INPUT = "invalid_lot_sizing_input"
_ROUNDING_MODE_FLOOR = "floor"
_EPS = 1e-12


@dataclass(frozen=True)
class LotSizingV1Config:
    account_balance: float
    risk_per_trade: float
    stop_loss_distance_pips: float
    pip_value_per_lot: float
    lot_step: float
    min_lot: float
    max_lot: float
    rounding_mode: str = _ROUNDING_MODE_FLOOR


@dataclass(frozen=True)
class LotSizingV1Result:
    lot: float | None
    raw_lot: float | None
    rounded_lot: float | None
    clamped_flag: bool
    size_reason: str


class LotSizingCalculator:
    @staticmethod
    def calculate(config: LotSizingV1Config) -> LotSizingV1Result:
        numeric_checks = [
            ("account_balance", config.account_balance),
            ("risk_per_trade", config.risk_per_trade),
            ("stop_loss_distance_pips", config.stop_loss_distance_pips),
            ("pip_value_per_lot", config.pip_value_per_lot),
            ("lot_step", config.lot_step),
            ("min_lot", config.min_lot),
            ("max_lot", config.max_lot),
        ]
        for name, value in numeric_checks:
            if not _is_valid_number(value):
                return _invalid(name)

        if config.account_balance <= 0:
            return _invalid("account_balance")
        if config.risk_per_trade <= 0:
            return _invalid("risk_per_trade")
        if config.risk_per_trade >= 1:
            return _invalid("risk_per_trade")
        if config.stop_loss_distance_pips <= 0:
            return _invalid("stop_loss_distance_pips")
        if config.pip_value_per_lot <= 0:
            return _invalid("pip_value_per_lot")
        if config.lot_step <= 0:
            return _invalid("lot_step")
        if config.min_lot <= 0:
            return _invalid("min_lot")
        if config.max_lot <= 0:
            return _invalid("max_lot")
        if config.min_lot > config.max_lot:
            return _invalid("min_gt_max")
        if config.rounding_mode != _ROUNDING_MODE_FLOOR:
            return _invalid("rounding_mode")
        if not _is_step_aligned(config.min_lot, config.lot_step):
            return _invalid("min_lot_step_mismatch")
        if not _is_step_aligned(config.max_lot, config.lot_step):
            return _invalid("max_lot_step_mismatch")

        raw_lot = (
            config.account_balance * config.risk_per_trade
        ) / (config.stop_loss_distance_pips * config.pip_value_per_lot)
        if not _is_valid_number(raw_lot) or raw_lot <= 0:
            return _invalid("raw_lot")

        rounded_lot = _floor_to_step(raw_lot, config.lot_step)
        if not _is_valid_number(rounded_lot):
            return _invalid("rounded_lot")
        if rounded_lot < config.min_lot:
            return LotSizingV1Result(
                lot=None,
                raw_lot=raw_lot,
                rounded_lot=rounded_lot,
                clamped_flag=False,
                size_reason=f"{_REASON_INVALID_INPUT}: below_min_lot",
            )

        if rounded_lot > config.max_lot:
            return LotSizingV1Result(
                lot=config.max_lot,
                raw_lot=raw_lot,
                rounded_lot=rounded_lot,
                clamped_flag=True,
                size_reason=_REASON_APPLIED_CLAMPED,
            )

        return LotSizingV1Result(
            lot=rounded_lot,
            raw_lot=raw_lot,
            rounded_lot=rounded_lot,
            clamped_flag=False,
            size_reason=_REASON_APPLIED,
        )


def _invalid(detail: str) -> LotSizingV1Result:
    return LotSizingV1Result(
        lot=None,
        raw_lot=None,
        rounded_lot=None,
        clamped_flag=False,
        size_reason=f"{_REASON_INVALID_INPUT}: {detail}",
    )


def _is_valid_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _is_step_aligned(value: float, step: float) -> bool:
    ratio = value / step
    return abs(ratio - round(ratio)) <= _EPS


def _floor_to_step(value: float, step: float) -> float:
    units = math.floor((value / step) + _EPS)
    floored = units * step
    step_str = f"{step:.16f}".rstrip("0")
    decimals = 0
    if "." in step_str:
        decimals = len(step_str.split(".")[1])
    return round(floored, decimals)
