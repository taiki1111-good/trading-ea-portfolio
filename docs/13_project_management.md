# プロジェクト管理

## 1. 文書の目的
この文書は、`trading-ea` プロジェクトの進行管理方針、フェーズ構成、マイルストーン、依存関係、完了定義、リスク・変更管理を整理する。
主に設計と実装の流れを可視化し、`docs/02_requirements.md` から `docs/08_development_plan.md` への追従を担保する。

## 2. 管理方針
- Source of Truth は `docs/02` 〜 `docs/08` とし、`docs/10_interface_contract.md` は補助文書として扱う
- main と `experiments` の境界を崩さない
- 実装前に設計を優先し、`ops/CURRENT_TASKS.md` で次の主タスクを明確にする
- 重要な判断は `ops/DECISION_LOG.md` に記録する
- 変更は `ops/worklog/` と `ops/review/` を通して追跡する

## 3. フェーズ一覧
### Phase 1: 設計基盤整備
- `docs/01` 〜 `docs/08` の文書基盤を整備する
- `AGENT_INDEX.md` / `REPO_MAP.md` / `ops/CURRENT_TASKS.md` の整備完了

### Phase 2: Data 実装準備
- Data モジュールの契約と受け入れ基準を確定する
- `docs/11_data_source_policy.md` を参照にデータ品質方針を固める

### Phase 3: 骨組み実装と接続検証
- Data から Execution までの最低限のフローを通す
- 状態遷移とログ記録の基礎を確認する

### Phase 4: 初期本体パターン導入
- `third_wave_break` を本体に導入する
- `triangle_break` などの追加候補を `experiments` で扱う

### Phase 5: 実装評価と運用設計
- 実装結果を評価し、運用ルール・停止ルールを整理する
- 実験の本体採用判断基準を明確にする

## 4. マイルストーン
- M1: 設計文書 `docs/02` 〜 `docs/08` が一通り整った状態
- M2: `ops/CURRENT_TASKS.md` に Data 実装準備が明確に記載された状態
- M3: Data モジュール骨組みが実装可能な設計状態
- M4: `Data → HTFContext → LTFStructure → Signal → RiskFilter → Execution` の基本接続が確認された状態
- M5: `third_wave_break` 本体ロジックが implementation-ready である状態
- M6: `experiments` の新規パターンが分離された状態

## 5. 依存関係
- `docs/12_project_kpi.md` は `docs/02_requirements.md` の要件を受けて定義される
- `docs/14_traceability_matrix.md` は `docs/02` 〜 `docs/07` の要素を結びつける
- `docs/15_non_functional_requirements.md` は `docs/02_requirements.md` の品質要求を詳細化する
- `docs/16_operation_design.md` は `docs/06_state_spec.md` / `docs/07_test_plan.md` / `docs/11_data_source_policy.md` を補完する
- `ops/CURRENT_TASKS.md` は `docs/08_development_plan.md` を反映し、次アクションを示す

## 6. 完了定義
- 文書・運用ファイルの目的に沿った内容が明示されている
- 既存設計資料との重複が過剰でない
- main と `experiments` の用途が分離されている
- 次の作業が `ops/CURRENT_TASKS.md` で一目で分かる
- 重要な不確定事項は `TBD` / `未確定` として明示されている

## 7. リスク管理
- 主要リスク
  - 設計と実装の乖離
  - `main` と `experiments` の混在
  - データ品質不備による誤判定
  - 状態遷移の不整合
  - 変更管理の不徹底
- 対応方針
  - 設計は `docs/02` 〜 `docs/08` で固める
  - `experiments` は `docs/experiments/` と `src/experiments/` に分離する
  - `docs/11_data_source_policy.md` でデータ採用基準を明確化する
  - `docs/06_state_spec.md` に状態遷移を明示的に定義する
  - 変更は `ops/DECISION_LOG.md` / `ops/review/` で追跡する

## 8. 変更管理
- 変更要求は `ops/CURRENT_TASKS.md` に追加する
- 変更理由は `ops/DECISION_LOG.md` に記録する
- 変更内容は `ops/worklog/` に残す
- 重要変更は `ops/review/PENDING_REVIEW.md` を通す
- 採用済み変更は `ops/review/APPROVED_CHANGES.md` に記録する
- 設計変更は `docs/03_architecture.md` / `docs/04_module_spec.md` / `docs/05_variable_spec.md` / `docs/06_state_spec.md` / `docs/07_test_plan.md` に反映する

## 9. 未確定事項
- プロジェクトのフェーズ終了判定に使う具体的な指標値は未確定 / TBD
- 実装ペースやリリースタイムラインは現時点では未確定 / TBD
- 詳細な変更承認フローのステップ数は未確定 / TBD
