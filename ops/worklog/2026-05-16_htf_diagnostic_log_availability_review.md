# 2026-05-16 htf diagnostic log availability review

## 実行目的
- HTF filter v1 strict/permissive 比較に必要なログ項目が、既存 `decision_logs` / `near_live_decision_logs` / 既存仕様でどこまで充足しているかを確認する。
- 今回はログ確認と欠落整理のみを対象とし、HTF filter本体実装や比較runner実装は行わない。

## 確認対象
- 代表出力:
  - `tmp/phase9_pipeline_rep_20260509/near_live/near_live_decision_logs.csv`
  - `tmp/phase9_pipeline_weekend_rep_20260509/near_live/near_live_decision_logs.csv`
- 仕様/関連実装:
  - `docs/10_interface_contract.md`
  - `docs/17_backtest_design.md`
  - `scripts/summarize_csv_replay_dry_run.py`
  - `scripts/run_csv_replay_pipeline_dry_run.py`
  - `src/backtest/pipeline_adapter.py`
  - `src/backtest/backtest_runner.py`

## 結果サマリ
- 結論: **B（不足ログ項目の最小追加設計を先行）** が妥当。
- 理由:
  - `PipelineAdapter` 内部traceには HTF比較向け項目がある。
  - ただし `near_live_decision_logs.csv` への書き出し列が限定され、HTF比較必須項目の多くが欠落している。
  - 既存ログのみでは strict/permissive 比較を十分に再現できない。

## 1) 既に存在し、比較に使える列
- `filter_reason`
  - `scripts/run_csv_replay_pipeline_dry_run.py` では `trace["htf_filter_reason"]` が `filter_reason` に入るため、理由文字列の一部は取得可能。
- `entry_signal`
- `trade_ok`
- `signal_type`
- `decision_reason`
- `timestamp`
- （仕様側）`htf_bias` / `htf_trend_dir` / `htf_context_reason` は docs と `pipeline_adapter` 内部では扱いあり。

## 2) 存在するが意味・粒度が不足している列
- `filter_reason`
  - 1列に集約され、`htf_filter_reason` 専用列として分離されていない。
  - strict/permissive差分（neutral通過/拒否）を安定集計しづらい。
- `decision_reason`
  - 説明文として有用だが、比較用の構造化カウントに直接使いにくい。
- `entry_signal` / `trade_ok`
  - 結果列としては有用だが、HTF理由内訳（neutral起因、against起因）は直接分解できない。

## 3) 存在せず、v1 diagnostic comparison 前に追加候補となる列
- `htf_filter_enabled`
- `htf_timeframe_policy`
- `htf_neutral_policy`
- `htf_trend_dir`
- `htf_bias`
- `htf_direction_aligned`
- `htf_filter_reason`（独立列）
- `htf_context_reason`
- `neutral_passed_count`（集計項目）
- `neutral_rejected_count`（集計項目）
- `htf_filter_rejected_count`（集計項目）
- `htf_filter_rejected_by_reason`（集計項目）
- `htf_against_entry`（または同等に判定可能な構造列）

補足:
- `src/backtest/pipeline_adapter.py` の `_trace_base` には
  - `htf_filter_enabled`
  - `htf_timeframe_policy`
  - `htf_neutral_policy`
  - `htf_bias`
  - `htf_trend_dir`
  - `htf_direction_aligned`
  - `htf_filter_reason`
  - `htf_context_reason`
  が入る設計だが、`run_csv_replay_pipeline_dry_run.py` の `near_live_decision_logs.csv` 出力列に含まれていない。

## strict/permissive 比較に最低限必要な列（提案）
- 行レベル:
  - `timestamp`
  - `entry_signal`
  - `trade_ok`
  - `htf_filter_enabled`
  - `htf_timeframe_policy`
  - `htf_neutral_policy`
  - `htf_trend_dir`
  - `htf_bias`
  - `htf_direction_aligned`
  - `htf_filter_reason`
  - `htf_context_reason`
  - `decision_reason`
- 集計レベル:
  - `htf_filter_rejected_count`
  - `htf_filter_rejected_by_reason`
  - `neutral_passed_count`
  - `neutral_rejected_count`
  - `htf_against_entry count`（または同等指標）

## 既存ログだけで可能な確認
- `entry_signal` / `trade_ok` の件数確認
- `filter_reason` の文字列観察（`htf filter disabled` など）
- `decision_log_count` と `replay_bar_count` の整合確認

## 既存ログだけでは不可能/不十分な確認
- strict vs permissive の同条件比較
- neutral通過/拒否件数の明示集計
- `htf_bias` / `htf_trend_dir` / `htf_direction_aligned` の定量比較
- `htf_filter_rejected_by_reason` の安定集計
- `htf_against_entry` の直接カウント

## 推奨次タスク判断
- **B: 不足ログ項目の最小追加設計を先に行う**
  - 先に「どの列を near_live/backtest decision logs に露出させるか」を最小差分で固定する。
  - その後に HTF filter v1 diagnostic comparison 設計へ進む。

## 非影響確認
- 今回は確認作業のみで、コード変更なし。
- HTF filter の本体ONなし。
- `PipelineAdapter` / `BacktestRunner` / `Signal` / `RiskFilter` / `Execution path` 変更なし。
- PnL / trade_count / entry / exit / `trade_ok` に影響なし。
