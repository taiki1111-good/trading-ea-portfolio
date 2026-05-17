# 2026-05-01 Persistence JSONL Skeleton

## Summary
- `src/persistence` を追加し、LoggerBundle / LogRecord の保存・読込を担当する persistence 層を実装。
- 初期正式保存形式の最低方針は docs/05_variable_spec.md に従い CSV である。
- `CsvLogWriter` / `CsvLogReader` は実装済み。
- Logger -> CSV Persistence -> Evaluator の接続確認済み。
- JSONL は補助形式 / 将来候補 / nested構造保持用の任意形式として扱う。
- Logger はログレコード生成のみを担い、保存処理は持たない。
- Evaluator は直接ファイル I/O を持たず、読み戻し後の dict を受け取る。
- persistence は保存・読込境界を担当し、Logger / Evaluator の責務を分離する。

## Design
- `LogSerializer`
  - dataclass / dict / nested dataclass を再帰的に dict 化する。
  - `datetime` を ISO 8601 文字列に変換する。
  - `None` は `None` のまま保持する。
- `JsonlLogWriter`
  - 補助形式として UTF-8 で 1 record = 1 行 JSONL を書き込む。
  - `append=True` で追記、`append=False` で上書き。
  - 保存先の親ディレクトリを自動作成する。
- `JsonlLogReader`
  - 補助形式として JSONL を `list[dict]` として読み戻す。
  - 空行を無視し、破損行は `skip_invalid=True` で warnings に入れてスキップできる。
  - `PersistenceWriteResult` / `PersistenceReadResult` で結果・reason・warnings を返す。

## Notes
- persistence は保存境界を明確に分離するため、Logger / Evaluator の責務を変更しない。
- LoggerBundle を JSONL の 1 行として保存できる設計で、読み戻し後に各サブレコードを Evaluator に渡せる。
- JSONL は append と読み戻しが単純で、後続の CSV / DB 方式との橋渡しとしても適切。
- CSV は docs/05 の初期正式最低方針として実装済みで、JSONL は補助形式として扱う。

## Test Result
- `pytest -q` により persistence の unit / integration tests を含むテスト実行済み。
- 結果: `149 passed`
