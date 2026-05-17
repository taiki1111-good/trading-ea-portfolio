# 2026-05-03 Halt/Risk diagnostic script

## 1. 実装内容
- `scripts/diagnose_halt_filters_on_m5_slice.py` を追加。
- `price_shock_halt`（M5 range / M15相当rolling3）と `volatility_spike_halt`（ATR ratio / range ratio）を counterfactual 診断として実装。
- trigger から cooldown 分の halt window を生成し、重複/連続 window を結合。
- trade_logs 優先 + decision_logs 補助で entry候補を抽出し、halt window 内候補を `halted_entry_candidates.csv` に出力。
- summary（avoided_loss / missed_profit / net effect / trade_count_reduction）を CSV/MD で出力。

## 2. テスト
- `tests/unit/backtest/test_diagnose_halt_filters_on_m5_slice.py` を追加。
- 検証項目:
  - M5 shock 検出
  - M15 shock 検出
  - ATR ratio spike 検出
  - range ratio spike 検出
  - 重複/連続 window 結合
  - halt window 内 entry 抽出
  - trade_id または entry_time+signal_type 重複排除
  - avoided_loss / missed_profit / net effect 計算
  - 必須列不足時の明確エラー

## 3. 未解決事項
- range_ratio の `recent_range` 定義は初期実装で M5 bar range を採用。将来、複数バー集約版を比較する余地あり。
- decision_logs の列ばらつき（環境ごとの差分）に対する追加互換ルールは運用で必要なら拡張。
- 本結果は構造診断であり、収益性確認や閾値本採用を意味しない。
