# 2026-05-02 Wave/Breakout Overlap Diagnosis

## Summary
- 診断スクリプトを拡張し、wave_phase=third と breakout の同時成立、方向一致、過去Nバー内の third 候補有無・方向を追加計測。
- ロジック本体（WaveClassifier / BreakoutDetector / StructureAssembler）は未変更。
- future leak 回避のため、各バーで `bars[:i+1]` のみを使って `recent_third_candidate_within_{3,5,10}_bars` を算出。

## Files Changed
- scripts/diagnose_ltf_detector_chain_on_m5_slice.py

## Commands
- `$env:PYTHONPATH='.'; python scripts/diagnose_ltf_detector_chain_on_m5_slice.py --input-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv --output-dir logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis_wave_breakout_overlap`
- `$env:PYTHONPATH='.'; pytest -q`

## Output
- logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis_wave_breakout_overlap/ltf_detector_diagnosis.csv
- logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis_wave_breakout_overlap/ltf_detector_diagnosis_summary.csv
- logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis_wave_breakout_overlap/ltf_detector_diagnosis_summary.md

## Key Metrics
- bars_wave_third_and_breakout_true: 0
- bars_wave_breakout_direction_match: 0
- bars_breakout_true_but_wave_unknown: 406
- bars_wave_third_but_no_breakout: 58
- bars_breakout_after_recent_third_3: 27
- bars_breakout_after_recent_third_5: 49
- bars_breakout_after_recent_third_10: 93
- direction_match_after_recent_third_3: 5
- direction_match_after_recent_third_5: 15
- direction_match_after_recent_third_10: 36

## Notes
- 同一バーでの `wave_phase=third` と `breakout_flag=true` は 0。
- ただし、直近Nバーに third がある breakout では方向一致が高率で発生。
