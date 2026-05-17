# 変更メモ（2026-04-24）

## 変更目的
Data モジュール実装へ移る前に、docs / ops / 入口文書の不整合を解消し、実装準備状態を明確化するため。

## 変更ファイル
- `README.md`
- `AGENT_INDEX.md`
- `REPO_MAP.md`
- `docs/00_how_to_continue.md`
- `docs/05_variable_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`
- `docs/14_traceability_matrix.md`
- `ops/CURRENT_TASKS.md`

## 主な修正点
- `docs/11_data_source_policy.md` を Data 実装前の必須参照として入口文書に追加した
- `docs/14_traceability_matrix.md` を `docs/02_requirements.md` と整合させ、FR-10 / FR-34 を追記し、NFR 対応表を追加した
- `docs/14` の変数名を `docs/05` 準拠へ修正し、`spread_flag` など未定義名を排除した
- `docs/05_variable_spec.md` の見出し崩れを修正し、RiskFilter 配下の運用制約整理と Execution 見出し重複を解消した
- `docs/07_test_plan.md` に Data 実装で必要な最低観点を補強し、初期版のテスト基盤を `pytest` 基本方針へ整理した
- `docs/08_development_plan.md` と `ops/CURRENT_TASKS.md` に Data 骨組み実装対象ファイルと着手条件を明記した

## 未解決事項
- `pytest` / `unittest` の最終統一タイミングは未確定（初期版は `pytest` 基本で運用）
- FR-34（外部イベント高度比較）の数値閾値は TBD
- Data 骨組みの実コード作成は未着手

## 次にやること
1. Data 骨組みファイル（`src/data/*.py`）の作成に着手する
2. Data 向けテスト骨組みと初期 fixture を追加する
3. 実装後に docs/契約/命名/テスト観点の横断整合チェックを実施する
