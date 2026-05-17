# 2026-05-03 Validation Summary Script v0.2 minimal implementation

## 実装内容
- `ops/validation/validation_targets_v0_2.csv` を追加。
- `scripts/build_validation_v0_2_summary.py` を追加。
- 既存runの `backtest_summary.csv` / `trade_logs.csv` を基礎に最小集約を実装。
- module別に最小 decision rule を適用し、`summary/decision_log/layer_status/md` を出力。

## 入力
- `validation_targets_v0_2.csv`
- `run_dir/backtest_summary.csv`（優先）
- `run_dir/trade_logs.csv`（fallback）
- `run_dir/risk_stop_v2_analysis/risk_stop_v2_summary.csv`（risk_stop補助）
- `run_dir/cost_adjusted_summary.csv`（exit policy判定補助）

## 出力
- `validation_v0_2_summary.csv`
- `validation_v0_2_decision_log.csv`
- `validation_v0_2_layer_status.csv`
- `validation_v0_2_summary.md`

## decision rule（最小）
- `trade_count` 不明: `insufficient_sample`
- `trade_count < 20`: `insufficient_sample`
- `htf_v2/sr_v2/session_v2`: `keep_as_explanation_layer`
- `risk_stop_v2` で `net_counterfactual_effect_pips < 0`: `pause_no_go`
- `risk_stop_v2` で triggerなし等: `continue_diagnostic`
- `exit_policy` で cost-adjusted欠損: `needs_cost_adjusted_check`
- それ以外: `continue_diagnostic`

## テスト結果
- `tests/unit/backtest/test_build_validation_v0_2_summary.py` を追加。
- targets読込、metrics取得/fallback、欠損warning継続、sample_size_flag、module別decision、4出力生成を検証。

## 未解決事項
- `validation_targets.csv` の最終配置場所
- run命名揺れの吸収
- 診断summaryごとのschema統合
- `max_drawdown` の正式入力化
- `cost_adjusted` 標準入力化
- Markdown report粒度の最終設計

## 注意
- 本対応は後処理集約のみ。
- backtest再実行・売買ロジック変更・filter本体統合・閾値本採用は未実施。
