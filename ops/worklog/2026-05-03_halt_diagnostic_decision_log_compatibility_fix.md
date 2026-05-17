# 2026-05-03 Halt diagnostic decision_log compatibility fix

## 1. 失敗原因
- 実データの `decision_logs` に `entry_time` / `signal_type` が無いケースで、`_load_decision_entries` が必須列エラーを投げ、診断全体が停止していた。
- 本来は `trade_logs` が有効なら診断継続できるべきだが、decision 側がハード必須になっていた。

## 2. 修正方針
- `trade_logs` を主入力、`decision_logs` を補助入力へ明確化。
- `decision_logs` 読み込みに strict モードを追加。
- `trade_logs` から候補が取得できる場合は decision 側列不足を warning 扱いでスキップ。
- `trade_logs` 候補が無く、decision 側必須列も不足の場合のみエラー。
- warning は summary md の `## Warnings` と stdout `[warning]` に出力。

## 3. テスト結果
- decision 側列不足でも trade 側有効なら成功するケースを追加。
- decision スキップ warning が summary md に残ることを追加。
- decision 側必須列ありで補助候補が使われることを追加。
- trade 側空 + decision 側不足で明確エラーになることを追加。
- 既存重複排除ロジック（trade_id優先 / entry_time+signal_type）のテスト継続通過を確認。
