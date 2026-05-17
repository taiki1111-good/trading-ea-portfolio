# 2026-05-02 LTF Detector Chain Diagnosis

## Summary
- Added `scripts/diagnose_ltf_detector_chain_on_m5_slice.py`.
- Ran full test suite first (`pytest -q`) and confirmed pass.
- Ran detector-chain-only diagnosis on existing M5 slice without backtest rerun logic changes.

## Scope
- Purpose is detector-chain activation diagnosis only.
- No broker/OANDA integration.
- No period extension, optimization, or profitability claim.
- No fallback heuristic removal/improvement in this task.

## Outputs
- `logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis/ltf_detector_diagnosis.csv`
- `logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis/ltf_detector_diagnosis_summary.md`
- `logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis/ltf_detector_diagnosis_summary.csv`

## Key Result
- `detector_chain_entry_candidate_count = 0`
- Dominant fail stage: `wave_not_third`

