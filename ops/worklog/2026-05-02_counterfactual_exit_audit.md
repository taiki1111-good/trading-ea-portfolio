# 2026-05-02 Counterfactual Exit Audit

## 目的
`simple_trailing_after_1R` の改善幅が大きいため、売買ロジック本体を変更せず `counterfactual exit analysis` の実装妥当性を監査した。

## 変更
- `scripts/analyze_counterfactual_exits.py`
  - `simple_trailing_after_1R` 各tradeの監査詳細出力を追加。
  - 出力追加:
    - `counterfactual_exit_trade_details.csv`
    - `counterfactual_exit_audit.md`
  - 監査観点の診断を `diagnostics` として計算:
    - entryバーexit有無
    - max_holding_bars遵守
    - trailing方向単調性（longは上方向のみ、shortは下方向のみ）
    - best_favorable参照がexit時点までのバーのみか（future参照なしチェック）
  - baseline整合チェック（trade_count / pnl / exit_reason）を監査Markdownに明記。
- `tests/unit/backtest/test_analyze_counterfactual_exits.py`
  - long trailing更新方向テスト追加
  - short trailing更新方向テスト追加
  - entryバーexit禁止テスト追加
  - max_holding_bars遵守テスト追加
  - future max値の後出し未使用テスト追加
  - baselineと元trade_logs整合テスト追加

## 生成物
- `logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/counterfactual_exit/counterfactual_exit_trade_details.csv`
- `logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/counterfactual_exit/counterfactual_exit_audit.md`

## 実行
- `python scripts/analyze_counterfactual_exits.py --price-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-04-01.csv --trade-logs logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/trade_logs.csv --output-dir logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/counterfactual_exit --max-holding-bars 6 --sl-multiplier-list 1.5,2.0 --tp-multiplier-list 1.5,2.0 --include-breakeven --include-trailing`
- `$env:PYTHONPATH='.'; pytest -q`

## 結果
- `pytest -q`: `218 passed`
- 監査Markdownの baseline 一致:
  - `baseline_trade_count_match: True`
  - `baseline_pnl_match: True`
  - `baseline_exit_reason_match: True`

## 注意
- BacktestRunner / PipelineAdapter / ExitRuleEngine は未変更。
- 売買ロジック本体は未変更。
- 収益性確認済みを示すものではない。
