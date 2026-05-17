# 2026-05-02 htf filter v1 smoke validation

## 実施内容
- `pytest -q` 実行（全件パス）。
- 短期期間（2024-04-01〜2024-04-08, fixed_sl_tp）で以下3条件を実行。
  - HTF OFF
  - HTF ON + neutral permissive
  - HTF ON + neutral strict
- 各runで `trade_logs` / `decision_logs` を `CsvSchemaValidator` で検証し、log consistency も確認。

## 結果
- 3条件すべて完走。
- schema valid:
  - trade_logs: valid=true
  - decision_logs: valid=true
- consistency: valid=true（3条件とも warning なし）。
- decision_logs のHTF最小8列は3条件すべてで存在。
- 記録値:
  - OFF: `htf_filter_enabled=False`
  - ON permissive: `htf_filter_enabled=True`, `htf_neutral_policy=permissive`
  - ON strict: `htf_filter_enabled=True`, `htf_neutral_policy=strict`
- ON条件では `htf_filter_reason` に `htf_filter_v1: ...` の判定理由行を確認。

## 注意点（warning）
- `decision_logs` に HTF列を追加したため、`CsvSchemaValidator` で unknown extra columns warning が出る。
- これは実行不正ではなく、decision_logs schema の既知列更新が未反映なことが原因。

## 追加修正候補（今回未対応）
- `src/persistence/csv_schema_validator.py` の decision_logs 既知列に HTF最小8列を追加し、warning を解消する。
