# 2026-05-01 CSV Schema Validation Skeleton

## Summary
- `src/persistence/csv_schema_validator.py` を追加し、CSV の最小 schema validation を実装。
- 対象 schema は `decision_logs` / `trade_logs` / `state_logs` / `event_logs`。
- 初期版は必須列チェックを主目的とし、型の厳密検証は将来対応とする。
- 最小 enum チェックとして `position_state` と `order_result` の警告判定を追加。

## Validation Output
- `valid`
- `schema_name`
- `missing_columns`
- `extra_columns`
- `validation_reason`
- `warnings`

## Test Scope
- unit:
  - `trade_logs` の valid / invalid（missing columns）検証
  - `state_logs` の enum 警告検証
- integration:
  - Logger -> CSV readback -> schema validation -> Evaluator の正常パス
  - invalid records で missing_columns が返ること

## Notes
- Logger はログ生成のみを担当し、保存責務は持たない。
- Evaluator はファイルI/Oを持たず、読み戻し済みの records を受け取る。
- 本実装は CSV skeleton の最小検証であり、厳密型検証や migration は対象外。
