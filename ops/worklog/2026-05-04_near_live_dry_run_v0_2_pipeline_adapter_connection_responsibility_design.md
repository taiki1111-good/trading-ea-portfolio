# 2026-05-04 near-live dry-run v0.2 pipeline adapter connection responsibility design

## Summary
- Phase 9 CSV replay dry-run に PipelineAdapter を接続する前提で、責務分離と接続方針を実装前に整理した。
- 今回は設計文書更新のみで、コード・テスト・売買ロジックは未変更。
- 現行 dry-run health は `warn`（`expected_weekend_gap_only`）で No-Go ではないため、設計検討の進行は可能とした。

## Current skeleton responsibilities
- CSV replay
- warmup/replay split
- data quality warning（duplicate / out_of_order / data_gap）
- gap classification（expected_weekend / ordinary_missing / unknown）
- placeholder decision/state/event log
- near-live 風ログ出力

## Responsibilities added by PipelineAdapter connection
- 各バーで `HTFContext / LTFStructure / Signal / RiskFilter` を現在バーまでの情報で呼ぶ。
- future leak 防止を明示する。
- `entry_signal / exit_signal / trade_ok` を placeholder固定から実モジュール出力へ切替える。
- ただし実注文・デモ注文は行わず、副作用なしの dry-run を維持する。

## Responsibilities kept without connection
- CSV replay / dry-run health / data quality warning / gap classification は維持。
- OANDA/API接続は対象外のまま維持。
- `paper_order_action` は `none`（または将来 `paper_only`）を維持し、実注文行為を出さない。

## Placeholder integrity relation
- 現在の placeholder integrity は Phase 9 csv_replay skeleton 専用。
- PipelineAdapter 接続後は `entry_signal=False` 全固定前提が崩れるため、同一判定は使わない。
- 接続版では `no_real_order_integrity` を別定義する方針とした。

## Option comparison
- Option A: skeleton維持 + 別スクリプト分離
- Option B: 既存スクリプトに `--mode skeleton|pipeline` 追加
- Option C: 接続を後送りし summary/validation を先に固定

## Recommended option
- 推奨は Option A（別スクリプト分離）。
- 理由:
  - 既存skeleton運用と placeholder integrity を壊さない。
  - pipeline専用 integrity check を独立管理しやすい。
  - skeleton/pipeline の横比較が容易。

## Pre-implementation I/O freeze points
- 入力CLI契約（期間・timeframe・run_id）を維持する。
- 出力 `near_live_*` CSV 群の互換性を維持する。
- Pipeline接続版の追加ログ列と integrity列を事前固定する。
- health判定は skeleton版とpipeline版で分離する。

## Out of scope in this step
- コード変更・テスト変更
- BacktestRunner/PipelineAdapter/Signal/RiskFilter/Execution 変更
- 売買ロジック変更
- OANDA/API接続、実注文、デモ注文
