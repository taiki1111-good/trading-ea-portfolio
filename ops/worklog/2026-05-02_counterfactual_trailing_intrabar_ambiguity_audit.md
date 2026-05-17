# 2026-05-02 Counterfactual Trailing Intrabar Ambiguity Audit

## 目的
`simple_trailing_after_1R` の OHLC intrabar sequence 不明による楽観バイアスを監査し、保守的 variant を追加した。

## 変更
- `scripts/replay_counterfactual_exits_position_aware.py`
  - rule拡張:
    - `simple_trailing_after_1R`
    - `simple_trailing_after_1R_conservative`
    - `simple_trailing_after_1R_next_bar_activation`
    - `baseline_fixed_exit`
  - intrabar ambiguity 監査列を replay trades に追加:
    - `intrabar_ambiguous`
    - `activation_and_stop_same_bar`
    - `conservative_exit_applied`
    - `ambiguity_note`
  - summary に ambiguity集計を追加:
    - `intrabar_ambiguous_count`
    - `activation_and_stop_same_bar_count`
    - `conservative_exit_applied_count`
  - validation/集計は既存項目を維持しつつ拡張。
- `tests/unit/backtest/test_replay_counterfactual_exits_position_aware.py`
  - long/short ambiguous 検出
  - next_bar_activation の同一バー発動抑止
  - conservative の曖昧ケース非楽観処理
  - max_holding_bars=10 実行
  - 既存 skip/accept/整合/overlap テスト維持
- `docs/17_backtest_design.md`
  - 6.7節を追加し、OHLC intrabar sequence 不明と trailing variant 比較方針を明記。

## 実行
- `$env:PYTHONPATH='.'; pytest -q`
- 指定4コマンド（conservative/next_bar_activation × max_holding 6/10）

## 結果
- `pytest -q`: `229 passed`
- ambiguity は実データで `79` 件検出。
- conservative は `conservative_exit_applied_count=79`。
- next_bar_activation は ambiguity を記録しつつ同一バー発動を回避。

## 注意
- BacktestRunner / PipelineAdapter / ExitRuleEngine / 売買ロジック本体は未変更。
- 収益性評価ではなく構造検証。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
