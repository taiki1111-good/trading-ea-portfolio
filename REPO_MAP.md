# REPO MAP

## 1. このファイルの目的
本ファイルは、リポジトリ内のフォルダと主要ファイルの役割を整理し、human および AI agent が構造を見失わないようにするための地図である。

## 2. ルート直下

### `README.md`
外部から見た入口。
このプロジェクトの概要を簡潔に示す。

### `AGENT_INDEX.md`
AI agent 向けの入口。
最初に読む順番、役割、基本ルールを示す。

### `REPO_MAP.md`
本ファイル。
フォルダと主要ファイルの役割を一覧化する。

### `.gitignore`
Git に追跡させないファイルを定義する。

### `.gitattributes`
改行コードやファイル属性の扱いを定義する。

## 3. `docs/`
内部設計資料。
会話履歴に依存せず、別チャット・別 agent・将来の自分でも継続できるようにするための主文書群。

### `docs/00_how_to_continue.md`
再開用の入口文書。

### `docs/01_overview.md`
プロジェクト概要。
`docs/03_architecture.md` の前段として全体像を短く示す。

### `docs/02_requirements.md`
要件定義。
対象市場、時間足、売買思想、品質要求を定義する。

### `docs/03_architecture.md`
全体アーキテクチャ。
現行フロー `Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` を示す。

### `docs/04_module_spec.md`
モジュール仕様。
各上位モジュールと下位部品候補の責務を定義する。

### `docs/05_variable_spec.md`
主要変数仕様。
骨格変数の意味とモジュール間の受け渡しを整理する。

### `docs/06_state_spec.md`
状態仕様。
状態一覧、状態遷移、各状態で許可される操作を定義する。

### `docs/07_test_plan.md`
テスト計画。
単体・結合・シナリオ・状態遷移・実験検証の方針を整理する。

### `docs/08_development_plan.md`
開発計画。
どの順で何を実装・確認していくかを整理する。

### `docs/09_presentation_notes.md`
外部向け説明やポートフォリオ用の素材メモ。
現時点では成果説明・構成説明・技術アピール整理の下書きとして扱う。

### `docs/10_interface_contract.md`
モジュール間インターフェース契約の補助文書。
存在は認識するが、今回時点では `docs/02` から `docs/08` より優先しない。

### `docs/11_data_source_policy.md`
Data 実装前のデータソース方針文書。
CSV / parquet / pkl の役割、UTC 統一、spread / bid-ask / volume の扱い、H1/H4 集約、用途別採用判定を定義する。

### `docs/12_project_kpi.md`
プロジェクトの成功条件、フェーズ別完了条件、main v0 受入基準、ポートフォリオ視点の達成条件を整理する。

### `docs/13_project_management.md`
進行管理方針、フェーズ構成、マイルストーン、依存関係、完了定義、リスク・変更管理を整理する。

### `docs/14_traceability_matrix.md`
要件とモジュール、変数、状態、テストの対応関係を示し、設計と検証の追跡を助ける。

### `docs/15_non_functional_requirements.md`
説明可能性、保守性、信頼性、テスト容易性、拡張性、移植性、安全性、運用性、再現性などの非機能要件を整理する。

### `docs/16_operation_design.md`
ログ運用、異常対応、停止・再開ルール、パラメータ変更ルール、experiment 採用フロー、backtest/構造検証/実運用近似の区別を整理する。

## 4. `docs/experiments/`
新しい裁量仮説や試作アイデアの記録領域。
本体採用前の構想・比較・判断材料を残す。

### `docs/experiments/EXPERIMENT_INDEX.md`
実験一覧。

### `docs/experiments/EXPERIMENT_TEMPLATE.md`
新規実験を記録するためのテンプレート。

### `docs/experiments/exp_*.md`
個別実験ノート。

## 5. `ops/`
agent 運用とレビュー管理の領域。

### `ops/AGENT_WORKFLOW.md`
agent の役割分担と変更フロー。

### `ops/VS_CODE_SETUP.md`
VS Code の workspace 設定と推奨拡張の運用手順。

### `ops/CURRENT_TASKS.md`
現在進行中・保留・次候補のタスク一覧。

### `ops/DECISION_LOG.md`
重要な設計判断の記録。

### `ops/CHANGE_MEMO_TEMPLATE.md`
agent が変更内容を記録するための雛形。

### `ops/CODEX_REVIEW_CHECKLIST.md`
Codex に確認してほしい観点を整理したチェックリスト。

### `ops/worklog/`
agent が行った変更内容の記録。

### `ops/review/`
人間レビュー用の領域。
レビュー待ち、承認済み変更、レビュー記録を扱う。

### `ops/review/REVIEW_TEMPLATE.md`
レビュー記録テンプレート。

### `ops/review/PENDING_REVIEW.md`
レビュー待ちの変更一覧。

### `ops/review/APPROVED_CHANGES.md`
確認済み・採用済み変更の記録。

## 6. `portfolio/`
外部向け文章の下書き。
GitHub Pages や note に流用することを想定する。

### `portfolio/project-summary.md`
プロジェクト全体の説明下書き。

### `portfolio/architecture-summary.md`
設計・構成の説明下書き。

### `portfolio/test-summary.md`
テスト方針・品質保証の説明下書き。

### `portfolio/reflections.md`
学び、反省、改善余地の整理。

### `portfolio/README.md`
`portfolio/` 配下の各ファイルの役割説明。

## 7. `src/`
本体実装。

本体実装では、上位モジュールごとにフォルダを分け、その内部をさらに交換可能な下位部品へ分解する。

### `src/common/`
全体で共有する最小限の共通定義を置く。

### `src/data/`
価格データ・イベントデータ入力処理。

### `src/htf_context/`
上位足環境認識。

### `src/ltf_structure/`
執行足構造認識。

### `src/signal/`
HTF と LTF を統合して売買候補を作る。

### `src/risk_filter/`
取引可否、停止条件、lot、SL/TP を扱う。

### `src/execution/`
注文実行、約定確認、状態更新を扱う。

### `src/logger/`
理由、状態遷移、注文結果、損益を記録する。

### `src/persistence/`
CSV persistence の骨組みを置く。
Logger からのログを永続化し、Evaluator で再現・評価に使う設計を想定する。

### `src/evaluator/`
成績評価、比較集計、改善対象の整理を行う。

### `src/experiments/`
本体未採用の試作コードを置く。
新しい裁量パターンや補助ロジックを、本体から分離した形で比較・検証する。

## 8. `tests/`
テストコード。

### `tests/unit/`
下位部品単体テスト。

### `tests/integration/`
上位モジュール結合テスト、モジュール間結合テスト。
- E2E 最小統合テストは `tests/integration/test_end_to_end_minimal_pipeline.py` に実装されている。

### `tests/scenario/`
状態遷移テスト、停止条件テスト、シナリオテスト。

### `tests/fixtures/`
テスト用データや補助。

### `tests/experiments/`
実験ロジック専用テスト。

## 9. `images/`
図、スクリーンショット、結果画像。

## 10. `results/`
軽量な出力結果や要約結果。
巨大な生データや機密情報は置かない。

## 11. 基本ルール
- `docs/00_how_to_continue.md` を再開入口として扱う
- Source of Truth は `docs/02` から `docs/08` を優先する
- `docs/10_interface_contract.md` は存在する補助文書として扱う
- Data 実装時は `docs/11_data_source_policy.md` を必須参照とする
- 本体と experiments を混ぜない
- docs は内部設計資料として扱う
- ops は運用・記録・レビュー用とする
- portfolio は外部向け下書きとする
- 大きな変更は worklog / review / decision log を通す
