# 2026-05-02 BreakoutDetector Prior Swing Fix

## Summary
- BreakoutDetector を修正し、breakout level 候補を `current_bar.timestamp` より前の swing に限定。
- `timestamp` が現在バーと同一の swing は除外。
- prior swing high/low が両方とも存在しない場合は `breakout_flag=false` を返し、理由を明示。
- 診断スクリプトに `breakout_reason` を診断CSV出力として追加。
- unit test を更新し、現在バーswing除外・prior swing breakout・prior swing欠如ケースを確認。

## Files Changed
- src/ltf_structure/breakout_detector.py
- tests/unit/ltf_structure/test_breakout_detector.py
- scripts/diagnose_ltf_detector_chain_on_m5_slice.py

## Validation
- `pytest -q tests/unit/ltf_structure/test_breakout_detector.py` -> 6 passed
- `pytest -q` -> 186 passed

## Re-run Results
### Detector diagnosis (M5 slice: 2024-01-02 to 2024-01-09)
- total_bars=1439
- bars_with_swing_points=1437
- bars_wave_phase_third=58
- bars_breakout_true=406
- bars_structure_candidate_true=0
- bars_pattern_allowed_true=0
- detector_chain_entry_candidate_count=0
- fail_stage_counts={'insufficient_swing': 4, 'wave_not_third': 1377, 'no_breakout': 58}

### Backtest (fallback OFF, same period)
- trade_count=0
- structure_source counts: {} (trade logs generated 0)
- fallback_used rate: N/A (denominator 0)

## Notes
- breakout_true は修正前0から増加（406）した。
- ただし entry は未発生。現時点の主なボトルネックは `wave_not_third` が多数（1377バー）。
- WaveClassifier の条件緩和や fallback 改修は未実施（今回範囲外）。
