from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.apply_cost_scenarios_to_m1_replay import CostScenarioConfig
from scripts.apply_cost_scenarios_to_m1_replay import apply_cost_adjustment
from scripts.apply_cost_scenarios_to_m1_replay import load_rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _cfg(
    *,
    slippage: float = 0.0,
    commission: float = 0.0,
    add_spread: float = 0.0,
    spread_included: bool = True,
) -> CostScenarioConfig:
    return CostScenarioConfig(
        scenario_name="unit",
        instrument="USDJPY",
        pip_size=0.01,
        slippage_pips_round_turn=slippage,
        commission_pips_round_turn=commission,
        additional_spread_pips=add_spread,
        spread_already_included=spread_included,
        swap_mode="none",
        notes="",
    )


def test_usdjpy_pip_conversion_is_correct() -> None:
    rows = [
        {"accepted_entry": "True", "m1_replay_pnl": "0.120", "rule": "baseline_fixed_exit"},
    ]
    adjusted, _ = apply_cost_adjustment(rows, _cfg())
    assert len(adjusted) == 1
    assert adjusted[0]["gross_pips"] == pytest.approx(12.0)


def test_net_pips_and_net_pnl_after_costs_are_correct() -> None:
    rows = [
        {"accepted_entry": "True", "m1_replay_pnl": "0.120", "rule": "baseline_fixed_exit"},
    ]
    cfg = _cfg(slippage=0.5, commission=0.3, add_spread=0.2)
    adjusted, _ = apply_cost_adjustment(rows, cfg)
    assert adjusted[0]["total_cost_pips"] == pytest.approx(1.0)
    assert adjusted[0]["net_pips"] == pytest.approx(11.0)
    assert adjusted[0]["net_pnl"] == pytest.approx(0.11)


def test_accepted_entry_false_is_excluded_from_summary() -> None:
    rows = [
        {"accepted_entry": "False", "m1_replay_pnl": "1.000", "rule": "simple_trailing_after_1R"},
        {"accepted_entry": "True", "m1_replay_pnl": "0.100", "rule": "simple_trailing_after_1R"},
    ]
    adjusted, summary = apply_cost_adjustment(rows, _cfg())
    assert len(adjusted) == 1
    assert len(summary) == 1
    assert summary[0]["accepted_trade_count"] == 1


def test_spread_already_included_avoids_double_count_by_zero_additional_spread() -> None:
    rows = [
        {"accepted_entry": "True", "m1_replay_pnl": "0.200", "rule": "baseline_fixed_exit"},
    ]
    cfg = _cfg(slippage=0.4, commission=0.1, add_spread=0.0, spread_included=True)
    adjusted, _ = apply_cost_adjustment(rows, cfg)
    # spread_already_included=true で追加spread=0.0なら、spread分の追加控除は発生しない
    assert adjusted[0]["total_cost_pips"] == pytest.approx(0.5)
    assert adjusted[0]["net_pips"] == pytest.approx(19.5)


def test_summary_gross_and_net_aggregation_is_correct() -> None:
    rows = [
        {"accepted_entry": "True", "m1_replay_pnl": "0.100", "rule": "r1"},
        {"accepted_entry": "True", "m1_replay_pnl": "-0.050", "rule": "r1"},
    ]
    cfg = _cfg(slippage=1.0, commission=0.0, add_spread=0.0)
    _, summary = apply_cost_adjustment(rows, cfg)
    assert len(summary) == 1
    s = summary[0]
    assert s["gross_total_pips"] == pytest.approx(5.0)
    assert s["total_cost_pips"] == pytest.approx(2.0)
    assert s["net_total_pips"] == pytest.approx(3.0)
    assert s["gross_total_pnl"] == pytest.approx(0.05)
    assert s["net_total_pnl"] == pytest.approx(0.03)


def test_missing_required_columns_raises_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    _write_csv(
        path,
        ["accepted_entry", "rule"],
        [{"accepted_entry": "True", "rule": "x"}],
    )
    with pytest.raises(ValueError, match="missing required columns"):
        load_rows(path)
