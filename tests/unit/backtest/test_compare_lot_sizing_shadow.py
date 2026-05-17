from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

from scripts.compare_lot_sizing_shadow import compare_shadow
from scripts.compare_lot_sizing_shadow import main
from scripts.compare_lot_sizing_shadow import parse_args


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _base_kwargs(input_csv: Path, output_dir: Path) -> dict[str, object]:
    return {
        "input_csv": input_csv,
        "output_dir": output_dir,
        "fixed_lot": 0.1,
        "account_balance": 1000.0,
        "risk_per_trade": 0.01,
        "pip_value_per_lot": 10.0,
        "lot_step": 0.01,
        "min_lot": 0.01,
        "max_lot": 2.0,
        "rounding_mode": "floor",
        "stop_loss_distance_pips_fallback": None,
    }


def test_parse_args() -> None:
    old = sys.argv
    try:
        sys.argv = [
            "compare_lot_sizing_shadow.py",
            "--input-csv",
            "in.csv",
            "--output-dir",
            "out",
            "--fixed-lot",
            "0.1",
            "--account-balance",
            "1000",
            "--risk-per-trade",
            "0.01",
            "--pip-value-per-lot",
            "10",
            "--lot-step",
            "0.01",
            "--min-lot",
            "0.01",
            "--max-lot",
            "2.0",
            "--rounding-mode",
            "floor",
        ]
        args = parse_args()
    finally:
        sys.argv = old
    assert args.input_csv == "in.csv"
    assert args.output_dir == "out"


def test_normal_case_generates_rows_and_summary(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(
        input_csv,
        [
            {"stop_loss_distance_pips": 20.0},
            {"stop_loss_distance_pips": 25.0},
        ],
    )
    rows, summary = compare_shadow(**_base_kwargs(input_csv, output_dir))

    assert len(rows) == 2
    assert summary["row_count"] == 2
    assert summary["valid_risk_lot_count"] == 2
    assert (output_dir / "lot_sizing_shadow_rows.csv").exists()
    assert (output_dir / "lot_sizing_shadow_summary.csv").exists()
    assert (output_dir / "lot_sizing_shadow_summary.md").exists()


def test_clamp_count_increases(tmp_path: Path) -> None:
    input_csv = tmp_path / "decision_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"stop_loss_distance_pips": 2.0}])
    kwargs = _base_kwargs(input_csv, output_dir)
    kwargs["risk_per_trade"] = 0.8
    kwargs["max_lot"] = 1.0
    rows, summary = compare_shadow(**kwargs)

    assert rows[0]["risk_based_clamped_flag"] == "True"
    assert summary["clamped_count"] == 1


def test_below_min_is_invalid(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"stop_loss_distance_pips": 20.0}])
    kwargs = _base_kwargs(input_csv, output_dir)
    kwargs["account_balance"] = 10.0
    kwargs["risk_per_trade"] = 0.001
    rows, summary = compare_shadow(**kwargs)

    assert rows[0]["risk_lot_valid_flag"] == "False"
    assert rows[0]["risk_based_lot_sizing_reason"] == "invalid_lot_sizing_input: below_min_lot"
    assert summary["below_min_count"] == 1
    assert summary["invalid_risk_lot_count"] == 1


def test_stop_loss_distance_uses_csv_column(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"stop_loss_distance_pips": 30.0}])
    kwargs = _base_kwargs(input_csv, output_dir)
    kwargs["stop_loss_distance_pips_fallback"] = 10.0
    rows, _ = compare_shadow(**kwargs)

    assert rows[0]["stop_loss_distance_pips"] == 30.0


def test_stop_loss_distance_uses_cli_fallback(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"some_col": "x"}])
    kwargs = _base_kwargs(input_csv, output_dir)
    kwargs["stop_loss_distance_pips_fallback"] = 15.0
    rows, _ = compare_shadow(**kwargs)

    assert rows[0]["stop_loss_distance_pips"] == 15.0


def test_stop_loss_distance_missing_raises_error(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"some_col": "x"}])
    kwargs = _base_kwargs(input_csv, output_dir)
    with pytest.raises(ValueError, match="stop_loss_distance_pips"):
        compare_shadow(**kwargs)


def test_fixed_lot_zero_keeps_diff_and_ratio_blank(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"stop_loss_distance_pips": 20.0}])
    kwargs = _base_kwargs(input_csv, output_dir)
    kwargs["fixed_lot"] = 0.0
    rows, summary = compare_shadow(**kwargs)

    assert rows[0]["risk_lot_valid_flag"] == "True"
    assert rows[0]["risk_based_effective_lot"] != ""
    assert rows[0]["lot_size_diff"] == ""
    assert rows[0]["lot_size_ratio"] == ""
    assert summary["average_lot_size_diff"] == ""
    assert summary["average_lot_size_ratio"] == ""
    assert summary["max_lot_size_diff"] == ""
    assert summary["min_lot_size_diff"] == ""


def test_input_csv_is_not_modified(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"stop_loss_distance_pips": 20.0}])
    before = input_csv.read_text(encoding="utf-8")
    compare_shadow(**_base_kwargs(input_csv, output_dir))
    after = input_csv.read_text(encoding="utf-8")
    assert before == after


def test_main_writes_outputs(tmp_path: Path) -> None:
    input_csv = tmp_path / "trade_logs.csv"
    output_dir = tmp_path / "out"
    _write_csv(input_csv, [{"stop_loss_distance_pips": 20.0}])
    old = sys.argv
    try:
        sys.argv = [
            "compare_lot_sizing_shadow.py",
            "--input-csv",
            str(input_csv),
            "--output-dir",
            str(output_dir),
            "--fixed-lot",
            "0.1",
            "--account-balance",
            "1000",
            "--risk-per-trade",
            "0.01",
            "--pip-value-per-lot",
            "10",
            "--lot-step",
            "0.01",
            "--min-lot",
            "0.01",
            "--max-lot",
            "2.0",
            "--rounding-mode",
            "floor",
        ]
        rc = main()
    finally:
        sys.argv = old
    assert rc == 0
    assert (output_dir / "lot_sizing_shadow_rows.csv").exists()
