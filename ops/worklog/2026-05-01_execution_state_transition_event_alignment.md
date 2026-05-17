# 2026-05-01 Execution State Transition Event Alignment

## Summary
- `StateTransitionManager` に `transition_by_event(previous_state, event)` を追加し、`docs/06_state_spec.md` の正式イベント集合に沿う遷移を実装。
- 既存呼び出し互換のため `transition(...)` は残し、初期 skeleton 用ラッパーとして維持。
- `transition(...)` は `IDLE -> POSITION_OPEN` の直接遷移を返すため、`docs/06_state_spec.md` の正式イベント列とは完全一致しない互換 API である。
- 将来的には `transition(...)` を deprecated 扱いとし、呼び出し箇所を `transition_by_event` へ寄せる縮退計画を ops に明記。
- integration / unit テストをイベント駆動遷移列へ更新。

## Test Result
- 実行: `$env:PYTHONPATH='.'; pytest -q`
- 結果: `130 passed`

## Notes
- 現時点の E2E 最小統合はエントリー側（`IDLE -> ENTRY_PENDING -> POSITION_OPEN`）を主対象として確認。
- `POSITION_OPEN -> EXIT_PENDING -> IDLE`、timeout 系、`ERROR -> SUSPENDED` のシナリオ拡張は次段の scenario テストで明確化する。
