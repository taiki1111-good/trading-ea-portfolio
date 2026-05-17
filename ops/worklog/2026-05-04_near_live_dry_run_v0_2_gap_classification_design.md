# 2026-05-04 near-live dry-run v0.2 gap classification design

## 1. 目的
- Phase 9 near-live / CSV replay dry-run の次段として、`data_gap` を分類して扱う設計方針を文書化する。
- `ordinary missing` と `expected weekend / market closure` を区別し、Go/No-Go 判断精度を上げる。
- 本作業は設計文書化のみとし、コード変更は行わない。

## 2. 背景
- 現行 `scripts/run_csv_replay_dry_run.py` は、期待時間足超過を一律 `data_gap` warning として記録する。
- 1day replay は `warning_count=0`。
- multi-day replay は `warning_count=1` / `data_gap_count=1`。
- 該当warning:
  - `timestamp=2024-01-07T17:05:00+00:00`
  - `message=data gap detected: expected 0 days 00:05:00, got 2 days 00:10:00`
- 現時点方針として、上記は通常欠損と即断せず `weekend / market closure gap` 候補として扱い、単独では No-Go としない。

## 3. gap classification案
1. `ordinary_missing_bar_gap`
   - 通常市場時間中のbar欠損候補。
   - warning + investigation required。
   - 多発時は No-Go 候補。
2. `expected_weekend_gap`
   - 金曜終盤〜週明け再開にまたがるgap候補。
   - warning記録は維持するが、単独で No-Go にしない。
3. `expected_market_closure_gap`
   - weekend以外の休止・メンテナンス・祝日候補。
   - 取引カレンダー未導入段階では candidate 扱い。
4. `unexpected_market_hours_gap`
   - 市場時間中で closure説明がつかないgap。
   - 優先調査対象、多発・長時間で No-Go 候補。
5. `unknown_gap`
   - 現行情報では分類不能。
   - warning保持し後続情報で再分類。

## 4. 将来ログ列候補（今回は未実装）
- `gap_class`
- `expected_gap_flag`
- `gap_duration`
- `previous_timestamp`
- `current_timestamp`
- `market_session_status`
- `gap_reason`
- `gap_action`
- `gap_requires_investigation`

## 5. Go/No-Go方針（設計）
- `duplicate_timestamp` / `out_of_order_timestamp` は引き続き高優先warning。
- `data_gap` は一律 No-Go としない。
- `expected_weekend_gap` / `expected_market_closure_gap` は単独では No-Go にしない。
- `unexpected_market_hours_gap` 多発時は No-Go 候補。
- `unknown_gap` は調査対象。
- warningは握りつぶさず、`near_live_validation_warnings.csv` / `near_live_event_logs.csv` / `near_live_state_logs.csv` に残す。
- 分類導入後も `warning_count` は維持し、summary側で分類別count追加を検討する。

## 6. 実装しないこと（今回）
- `scripts/run_csv_replay_dry_run.py` の変更。
- tests / スキーマ変更。
- BacktestRunner / PipelineAdapter / Signal / RiskFilter / Execution の変更。
- 売買ロジック変更、HTF/SR/Session/RiskStop/Halt のfilter化。
- OANDA/API接続、実注文・デモ注文。

## 7. 次段候補
- gap classification design の文書レビュー。
- `gap_class` / `expected_gap_flag` の最小列追加要否判断。
- 必要なら CSV replay skeleton へ最小分類ロジック導入。
- summary分類別countとValidation Framework接続方式の設計。
