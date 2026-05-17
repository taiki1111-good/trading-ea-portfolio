from __future__ import annotations

# Canonical category tokens for risk/filter reason management.
RISK_ALL_FILTERS_PASSED = "all_risk_filters_passed"
RISK_FIXED_SL_TP = "fixed_sl_tp"
# Currently unused in runtime output. Kept as a catalog token for compatibility and phased migration.
RISK_FIXED_SKELETON_APPLIED = "fixed_risk_skeleton_applied"
RISK_PLACEHOLDER_FIXED_LOT = "placeholder_fixed_lot"
RISK_INVALID_LOT = "invalid_lot"
RISK_INVALID_STOP_LOSS = "invalid_stop_loss"
RISK_INVALID_TAKE_PROFIT = "invalid_take_profit"
RISK_INVALID_ACCOUNT_BALANCE = "invalid_account_balance"
RISK_MISSING_ENTRY_SIGNAL = "missing_entry_signal"
RISK_UNSUPPORTED_SIGNAL_TYPE = "unsupported_signal_type"
RISK_CONTRACT_INVALID = "risk_contract_invalid"
RISK_EVENT = "event_risk"
RISK_SPREAD_TOO_WIDE = "spread_too_wide"
RISK_TRADE_LIMIT_REACHED = "trade_limit_reached"

# Legacy value kept for backward compatibility in current log outputs.
RISK_ALL_FILTERS_PASSED_LEGACY = "all risk filters passed"

_LEGACY_TO_CANONICAL = {
    RISK_ALL_FILTERS_PASSED_LEGACY: RISK_ALL_FILTERS_PASSED,
}


def normalize_reason_category(reason: str) -> str:
    if not reason:
        return ""
    raw = str(reason).strip()
    if not raw:
        return ""
    prefix = raw.split(":", 1)[0].strip()
    mapped_raw = _LEGACY_TO_CANONICAL.get(prefix)
    if mapped_raw:
        return mapped_raw
    compact = prefix.replace(" ", "_").replace("-", "_").lower()
    return _LEGACY_TO_CANONICAL.get(compact, compact)


def normalize_reason_categories(reason: str) -> list[str]:
    if not reason:
        return []
    categories: list[str] = []
    seen: set[str] = set()
    for part in str(reason).split("|"):
        category = normalize_reason_category(part)
        if not category or category in seen:
            continue
        seen.add(category)
        categories.append(category)
    return categories
