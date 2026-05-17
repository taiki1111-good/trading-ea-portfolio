# 2026-05-09 pipeline dry-run health minimal implementation

## 目的
- Phase 9 CSV replay pipeline dry-run を、skeleton実行だけでなく最小health判定できる状態へ進める。
- 売買ロジック変更ではなく、出力検証と集計基盤の最小整備に限定する。

## 実施内容
- `scripts/summarize_csv_replay_dry_run.py` に pipeline mode 判定を追加。
- `mode=csv_replay_pipeline`（または `pipeline_mode=pipeline`）時に `pass/warn/fail` の最小health判定を追加。
- 判定対象に以下を追加:
  - `real_order_sent_count`
  - `no_real_order_integrity_violation_count`
  - `pipeline_adapter_error_count`
  - `duplicate_bar_count`
  - `out_of_order_count`
  - `ordinary_missing_bar_gap_count`
  - `unknown_gap_count`
  - `decision_log_count` と `replay_bar_count` の整合
- `dry_run_period_summary.csv` に pipeline関連カウント列を追加。
- pipeline output列棚卸し観点として `tests/unit/backtest/test_run_csv_replay_pipeline_dry_run.py` に summary列検証を追加。
- `tests/unit/backtest/test_summarize_csv_replay_dry_run.py` に pipeline health判定ケース（pass/warn/fail）を追加。

## 判定方針（最小）
- fail:
  - `real_order_sent_count > 0`
  - `no_real_order_integrity_violation_count > 0`
  - `decision_log_count != replay_bar_count`
- warn:
  - `pipeline_adapter_error_count > 0`
  - `ordinary_missing_bar_gap_count > 0`
  - `unknown_gap_count > 0`
  - `duplicate_bar_count > 0`
  - `out_of_order_count > 0`
- pass:
  - 上記 fail/warn に該当しない
- `expected_weekend_gap_count` 単独は warn/fail にしない。

## 非対応（今回の範囲外）
- OANDA/API接続
- 実注文送信
- BacktestRunner本体・PipelineAdapter本体の売買判断変更
- 収益性評価
