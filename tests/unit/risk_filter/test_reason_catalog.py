from src.risk_filter.reason_catalog import (
    RISK_ALL_FILTERS_PASSED,
    RISK_ALL_FILTERS_PASSED_LEGACY,
    RISK_INVALID_ACCOUNT_BALANCE,
    RISK_INVALID_LOT,
    normalize_reason_category,
    normalize_reason_categories,
)


def test_normalize_reason_category_handles_new_format():
    assert normalize_reason_category(RISK_ALL_FILTERS_PASSED) == RISK_ALL_FILTERS_PASSED


def test_normalize_reason_category_applies_legacy_mapping_on_raw_prefix():
    assert normalize_reason_category(RISK_ALL_FILTERS_PASSED_LEGACY) == RISK_ALL_FILTERS_PASSED


def test_normalize_reason_category_extracts_prefix_from_detail():
    assert normalize_reason_category("risk_contract_invalid: unsupported_signal_type=none") == "risk_contract_invalid"


def test_normalize_reason_category_handles_old_and_new_risk_contract_invalid_details():
    assert normalize_reason_category("risk_contract_invalid: entry_signal_false") == "risk_contract_invalid"
    assert normalize_reason_category("risk_contract_invalid: non_entry_signal_type=exit") == "risk_contract_invalid"
    assert normalize_reason_category("risk_contract_invalid: missing_entry_signal") == "risk_contract_invalid"
    assert normalize_reason_category("risk_contract_invalid: unsupported_signal_type=exit") == "risk_contract_invalid"


def test_normalize_reason_category_handles_invalid_account_balance_token():
    assert normalize_reason_category(f"{RISK_INVALID_ACCOUNT_BALANCE}: account_balance=0.0") == RISK_INVALID_ACCOUNT_BALANCE
    assert normalize_reason_category(f"{RISK_INVALID_LOT}: fixed_lot=0.1") == RISK_INVALID_LOT


def test_normalize_reason_categories_handles_multiple_categories():
    assert normalize_reason_categories("fixed_sl_tp | placeholder_fixed_lot") == ["fixed_sl_tp", "placeholder_fixed_lot"]


def test_normalize_reason_categories_handles_detail_entries():
    assert normalize_reason_categories(
        "risk_contract_invalid: entry_signal_false | invalid_lot: fixed_lot=0"
    ) == ["risk_contract_invalid", "invalid_lot"]


def test_normalize_reason_categories_handles_legacy_success_reason():
    assert normalize_reason_categories("all risk filters passed") == ["all_risk_filters_passed"]


def test_normalize_reason_categories_handles_empty_or_separator_only():
    assert normalize_reason_categories("") == []
    assert normalize_reason_categories(" | ") == []
