# 2026-05-02 Chart Review Template

## 目的
MTFチャートの目視確認結果を、後続の改善判断に使える形で記録するための review template CSV 生成スクリプトを追加した。

## 実施内容
- `scripts/create_chart_review_template.py` を追加。
- 入力:
  - `--chart-index`
  - `--output-csv`
- 元データ列を保持しつつ、人間レビュー列を追加したテンプレートCSVを出力。

元データ列:
- chart_file
- trade_index
- signal_type
- entry_time
- exit_time
- recent_third_timestamp
- temporal_lag_bars
- exit_reason
- pnl
- structure_source

追加レビュー列:
- visual_entry_ok
- visual_exit_ok
- issue_category
- issue_note
- priority

issue_category 候補:
- entry_ok
- exit_too_early
- htf_against_entry
- range_noise_breakout
- entry_too_late
- sl_tp_too_fixed
- unclear

## 実行確認
- 入力: `logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/mtf_charts/mtf_chart_index.csv`
- 出力: `logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/mtf_charts/chart_review_template.csv`
- 行数: 30

## 制約確認
- 売買ロジック変更なし
- BacktestRunner / PipelineAdapter / ExitRuleEngine 変更なし
- 実データや生成画像を Git 追加しない方針を維持
