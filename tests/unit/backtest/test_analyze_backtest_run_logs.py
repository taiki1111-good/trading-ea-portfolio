from scripts.analyze_backtest_run_logs import _build_reason_category_metrics


def test_build_reason_category_metrics_handles_multi_reason_and_primary() -> None:
    rows = [
        {
            "risk_reason": "fixed_sl_tp | placeholder_fixed_lot",
            "filter_reason": "all risk filters passed",
        },
        {
            "risk_reason": "",
            "filter_reason": "risk_contract_invalid: entry_signal_false | invalid_lot: fixed_lot=0",
        },
    ]

    metrics = _build_reason_category_metrics(rows)

    assert metrics["risk_reason_category_counts"]["fixed_sl_tp"] == 1
    assert metrics["risk_reason_category_counts"]["placeholder_fixed_lot"] == 1
    assert metrics["risk_reason_primary_category_counts"]["fixed_sl_tp"] == 1
    assert metrics["risk_reason_primary_category_counts"]["unknown"] == 1
    assert metrics["risk_reason_unknown_count"] == 1

    assert metrics["filter_reason_category_counts"]["all_risk_filters_passed"] == 1
    assert metrics["filter_reason_category_counts"]["risk_contract_invalid"] == 1
    assert metrics["filter_reason_category_counts"]["invalid_lot"] == 1
    assert metrics["filter_reason_primary_category_counts"]["all_risk_filters_passed"] == 1
    assert metrics["filter_reason_primary_category_counts"]["risk_contract_invalid"] == 1
    assert metrics["filter_reason_unknown_count"] == 0


def test_build_reason_category_metrics_treats_none_as_unknown_not_none_category() -> None:
    rows = [
        {
            "risk_reason": None,
            "filter_reason": None,
        },
        {
            "risk_reason": "",
            "filter_reason": " ",
        },
    ]

    metrics = _build_reason_category_metrics(rows)

    assert metrics["risk_reason_primary_category_counts"]["unknown"] == 2
    assert metrics["filter_reason_primary_category_counts"]["unknown"] == 2
    assert "none" not in metrics["risk_reason_category_counts"]
    assert "none" not in metrics["filter_reason_category_counts"]
