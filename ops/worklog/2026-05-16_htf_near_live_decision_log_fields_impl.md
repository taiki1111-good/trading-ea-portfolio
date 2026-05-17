# 2026-05-16 htf near_live decision log fields impl

## 実行目的
- HTF diagnostic comparison に必要な最小行レベル8列を、`near_live_decision_logs.csv` へ additive 追加する。
- 既存 `filter_reason` / `decision_reason` は維持し、既存CSV互換を壊さない。
- 本作業はログ列露出のみであり、HTF filter本体実装・ON化・比較runner実装は行わない。

## 変更ファイル
- `scripts/run_csv_replay_pipeline_dry_run.py`
- `tests/unit/backtest/test_run_csv_replay_pipeline_dry_run.py`

## 実装内容
### 1) near_live decision log へのHTF列追加（additive）
- 追加列:
  - `htf_filter_enabled`
  - `htf_timeframe_policy`
  - `htf_neutral_policy`
  - `htf_trend_dir`
  - `htf_bias`
  - `htf_direction_aligned`
  - `htf_filter_reason`
  - `htf_context_reason`
- `pipeline_adapter.get_last_decision_trace()` から取得し、列化した。
- trace欠落時は安全既定値で出力する実装とした。
  - bool列: `False`
  - 文字列列: `""`
- 既存 `filter_reason` は維持した。
- `htf_filter_reason` は HTF専用独立列として追加した（`filter_reason` とは別列）。
- CSV fieldnames に上記8列を追加した（既存列は削除・改名なし）。

### 2) 既存挙動非影響
- 売買判断ロジックは未変更。
- `entry_signal` / `trade_ok` / `filter_reason` / `decision_reason` の既存扱いを維持。
- summary計数や no real order integrity 系ロジックは未変更。

## テスト
- 実行:
  - `pytest -q tests/unit/backtest/test_run_csv_replay_pipeline_dry_run.py`
- 結果:
  - `7 passed`

テストで確認した点:
- traceにHTF項目がある場合、`decision_logs` に8列と値が入る。
- traceにHTF項目がない場合でも、8列が存在し安全既定値で出力される。
- `main()` 実行で出力される `near_live_decision_logs.csv` ヘッダに8列が含まれる。
- 既存 summary の主要カウント項目検証は維持される。

## 非対応範囲（今回未実施）
- HTF filter本体実装
- HTF filter ON化
- strict/permissive comparison runner 実装
- summary候補5項目実装
- backtest decision_logs 側の同等列追加
- PnL / trade_count / entry / exit / `trade_ok` に影響する変更
- OANDA/API、実注文、broker連携

## 次に進む判断
- 次フェーズは HTF diagnostic comparison 設計へ進める（strict/permissive 比較条件と評価フローの固定）。
