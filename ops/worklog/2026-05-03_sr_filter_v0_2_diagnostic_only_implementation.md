# 2026-05-03 SR Filter v0.2 diagnostic_only implementation

## 実装内容
- `src/backtest/pipeline_adapter.py` に `sr_v2` 設定を追加:
  - `sr_v2_enabled`
  - `sr_v2_policy`
  - `sr_v2_window_bars`
  - `sr_v2_near_threshold_pips`
  - `sr_v2_pip_size`
  - `sr_v2_use_atr_normalized`
- `PipelineAdapter` に `sr_v2 diagnostic_only` 計算を追加:
  - 初期SR定義は `fixed window rolling high/low`
  - `resistance=max(high[-N:])`, `support=min(low[-N:])`
  - current bar は集計対象から除外（`window[:-1]`）
  - 履歴不足時は `sr_data_valid_flag=False`
  - direction別で `sr_proximity_flag` / `sr_block_side` を計算
  - `sr_reason` に `diagnostic_only:no_entry_filter` を付与
- decision trace / decision_logs 出力列を追加:
  - `sr_v2_enabled`
  - `sr_policy`
  - `sr_window_bars`
  - `nearest_resistance`
  - `nearest_support`
  - `nearest_resistance_distance_pips`
  - `nearest_support_distance_pips`
  - `sr_proximity_flag`
  - `sr_block_side`
  - `sr_reason`
  - `sr_data_valid_flag`
  - `sr_counterfactual_group`
- `scripts/run_backtest_exit_experiment.py` に SR v2 CLI と metadata/summary 出力を追加。

## entryを止めていないこと
- `sr_v2_enabled=True` + `sr_v2_policy=diagnostic_only` でも entry制御は実施していない。
- `entry_signal` / `trade_ok` の判定フローはSR列で変更していない。
- SRは診断タグのみ出力する。

## テスト
- `tests/unit/backtest/test_pipeline_adapter.py`:
  - SR無効時の既存挙動維持
  - `diagnostic_only` で entry非変更
  - longでresistance近接時の `sr_proximity_flag=True`
  - shortでsupport近接時の `sr_proximity_flag=True`
  - longでsupport側はblockしない
  - shortでresistance側はblockしない
  - current barの極端値をSR計算に使わない
  - 履歴不足時 `sr_data_valid_flag=False`
  - decision traceへのSR列出力
- `tests/unit/backtest/test_run_backtest_exit_experiment.py`:
  - SR v2 CLI引数パース
  - runnerからConfigへのSR値受け渡し
  - `backtest_summary.csv` / `run_metadata.json` へのSR設定出力

## 未解決事項
- `sr_v2_use_atr_normalized` は現時点で未使用（将来拡張用フラグ）。
- window長/閾値は初期仮説であり本採用値ではない。
- SR proximity群の損益診断（代表月）は未実施。
