# 2026-05-02 schema validator known columns update

## 目的
- HTF filter v1 smoke validation で出ていた schema warning ノイズ（unknown extra columns）を低減する。

## 対応
- `CsvSchemaValidator` の既知列を更新。
  - decision_logs: HTF最小8列を known columns へ追加（必須化はしない）。
  - trade_logs: experimental列（`entry_time_mode` / `exit_policy` / `holding_bars` / `trailing_activation_R`）を known columns へ追加（必須化はしない）。

## 検証
- persistence関連テスト + 全pytestパス。
- 既存smoke run（OFF / ON permissive / ON strict）を再検証し、trade/decisionの unknown extra columns warning が解消されたことを確認。

## メモ
- 未知列は引き続き warning になる挙動を維持。
- valid/invalid 判定ロジックは緩めず、必須列・enum・temporal整合チェックは据え置き。
