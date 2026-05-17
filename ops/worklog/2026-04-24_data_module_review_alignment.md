# 変更メモ（2026-04-24 Dataレビュー）

## 変更目的
Data モジュール骨組みの実装を、SoT（docs/04/05/07/10/11）と横断整合レビューし、契約・命名・テスト観点の明確化を行う。

## 変更ファイル
- `src/data/types.py`
- `src/data/price_loader.py`
- `src/data/event_loader.py`
- `src/data/timeframe_aligner.py`
- `src/data/validator.py`
- `tests/unit/data/test_event_loader.py`
- `tests/unit/data/test_timeframe_aligner.py`
- `tests/unit/data/test_validator.py`

## 主な修正点
- Data 契約の明記を強化:
  - `ValidationResult.validated_frame` が正規化済みであることを明記
  - `event_type` の例示を `cpi/nfp/policy_rate/other` に統一
- PriceDataLoader の列要件と欠損許容の関係を明示:
  - `spread/volume` は列必須、値欠損は fallback 正規化で扱うことを docstring/コメントに追記
- EventDataLoader の行エラー方針を明確化:
  - `row_error_policy` の許容値を `skip/fail` に限定し、未知値は即時 `ValueError`
- UTC 契約を明確化:
  - DataValidator/TimeframeAligner で UTC-aware を明示的に検証
  - non-UTC 入力のテストを追加
- TimeframeAligner 命名整合:
  - `bucket_seconds` を実態に合わせて `bucket_minutes` へ変更（内部変数/引数）
- DataValidator の補強:
  - volume 負値、bid>ask を検証NGに追加
  - gap 検出が初期版で厳格である旨と、将来の市場カレンダー対応 TODO(TBD) を docstring に追記

## 未解決事項
- spread 単位（pips）と fixture 実値の整合は一部で解釈余地が残るため、実データ導入前に再確認が必要
- gap 検出は初期版では厳格運用のため、週末/休場を含む運用向け緩和方針は TBD
- `tests/unit/test_data_module.py` と `tests/unit/data/` の重複が残るため、段階的整理が必要

## 次にやること
1. Data integration テストへ移すべきケースを棚卸し（unitとの責務分離）
2. spread 単位の fixture 方針（pips固定）を明文化
3. HTFContext / LTFStructure 接続前に Data 出力契約の最終確認
