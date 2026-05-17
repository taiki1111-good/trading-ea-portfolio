# AGENT INDEX

## 1. このファイルの目的
本ファイルは、このリポジトリを AI agent が安全に読み始めるための入口である。

## 1.1 入口要約（運用固定）
- 通常運用の主力は 5.3 Codex（VSCode auto）とする
- 5.4thinking（チャット/アプリ）は最上流の判断専用とする
- 5.4（VSCode）は repo 横断の難所や広域整合のときだけ使う
- Copilot / Cursor は仕様確定後の機械実装・骨組み作成で使う
- Human が採用 / 保留 / 却下を決める
- 依頼は 1目的・少数ファイルに分割する

このリポジトリでは、
- 5.3 Codex を通常運用の主力として、タスク化・差分横断レビュー・整合確認に使う
- 5.4thinking を最上流判断が必要なときだけ使う
- 5.4（VSCode）を repo 横断の難所や広域整合が必要なときだけ使う
- Copilot / Cursor を仕様確定後の実装・機械的編集に使う
- Human を最終判断者とする

ことを前提とする。

## 2. 最初に読む順番
作業前に原則として以下の順で読むこと。

1. `docs/00_how_to_continue.md`
2. `README.md`
3. `REPO_MAP.md`
4. `ops/VS_CODE_SETUP.md`
5. `docs/02_requirements.md`
6. `docs/03_architecture.md`
7. `docs/04_module_spec.md`
8. `docs/05_variable_spec.md`
9. `docs/06_state_spec.md`
10. `docs/07_test_plan.md`
11. `docs/08_development_plan.md`
12. `docs/11_data_source_policy.md`（Data 実装前は必読）
13. `ops/AGENT_WORKFLOW.md`
14. `ops/CURRENT_TASKS.md`
15. `ops/DECISION_LOG.md`

補足:
- `docs/10_interface_contract.md` は存在する補助文書として認識してよい
- ただし今回時点では、主要な Source of Truth は `docs/02` から `docs/08` と `docs/00_how_to_continue.md` とする
- Data 実装に関しては `docs/11_data_source_policy.md` を必須参照文書として追加する

## 3. このリポジトリの重要方針
- 主対象は USDJPY
- 執行足は 5分足
- 上位足は 1時間足・4時間足
- 中核判断はルールベース
- 全体フローは `Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator`
- 上位足環境認識と執行足構造認識を分ける
- 初期 main は `third_wave_break` のみを扱う
- `triangle_break` は `experiments` で先行検証する
- 競合ケースは安全側で見送る
- 新規裁量パターンは experiments 領域で試す
- 会話履歴ではなく docs / ops を主たる知識源とする

## 4. agent ごとの基本役割
### 5.4thinking（チャット/アプリ）
- 必要時のみの最上流判断
- 受け入れ基準・例外境界・優先順位の確定
- 未解決論点の分離

### 5.4（VSCode）
- 必要時のみの repo 横断難所対応
- 広域整合が必要な変更の落とし込み
- 対象ファイル、確認観点、handoff 指示の整理

### Copilot / Cursor
- 仕様確定後の実装の下書き
- 機械的編集
- 骨組みコード生成
- 軽微修正

### 5.3 Codex（VSCode auto）
- 通常運用の主力
- タスク化の実行支援
- 差分横断レビュー
- 設計文書との整合確認
- 変更の統合判断補助

### Human
- 最終承認
- 採用 / 保留 / 却下
- 設計判断の確定
- 外部公開内容の決定

## 5. 作業前に必ず確認するもの
- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`
- `docs/11_data_source_policy.md`（Data 実装時は必須）
- `ops/CURRENT_TASKS.md`
- `ops/VS_CODE_SETUP.md`

必要に応じて:
- `ops/DECISION_LOG.md`
- `docs/10_interface_contract.md`

## 6. 変更後に更新対象となるもの
### 設計変更
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`
- `ops/DECISION_LOG.md`

### 実装変更
- `ops/worklog/`
- 必要に応じて `ops/review/PENDING_REVIEW.md`
- 採用後は `ops/review/APPROVED_CHANGES.md`

### 実験追加
- `docs/experiments/EXPERIMENT_INDEX.md`
- `docs/experiments/` の個別ノート
- `src/experiments/`
- `tests/experiments/`

## 7. 基本ルール
- `docs/00_how_to_continue.md` を再開入口として扱う
- Source of Truth は `docs/02` から `docs/08` を優先する
- Data 実装では `docs/11_data_source_policy.md` を必ず参照する
- `portfolio/` は外部説明用であり Source of Truth にしない
- 設計文書に反する変更は行わない
- 本体と experiments を混ぜない
- 大きな変更は記録を残す
- review 前提で変更を扱う
- docs と ops に残っていない判断を増やさない
