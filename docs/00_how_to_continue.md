# このプロジェクトを再開するために

## 1. このファイルの目的
本ファイルは、このリポジトリを初めて見る人、別チャットのAI、別のagent、または将来の自分が、会話履歴に依存せずに開発を再開できるようにするための入口文書である。

本プロジェクトでは、特定のチャット履歴ではなく、repo 内の `docs/` と `ops/` を主な知識源として継続可能性を確保することを方針としている。

## 2. このプロジェクトの概要
本プロジェクトは、自動売買EAを単なる売買条件の集合ではなく、設計・状態管理・テスト・実験拡張を意識したシステムとして構築するためのものである。

主対象は USDJPY だが、構造としては他商品への流用可能性を意識する。

現在の基本思想は以下である。
- 執行足は 5分足
- 上位足は 1時間足・4時間足
- 中核判断はルールベース
- 上位足環境認識と執行足構造認識を分ける
- 新しい裁量パターンは experiments 領域で試す
- 会話履歴ではなく docs を主たる引き継ぎ基盤とする

## 3. 最初に読むべき文書
このプロジェクトを再開する場合、原則として以下の順に読む。

1. `README.md`
2. `AGENT_INDEX.md`
3. `REPO_MAP.md`
4. `ops/VS_CODE_SETUP.md`
5. `docs/01_overview.md`
6. `docs/02_requirements.md`
7. `docs/03_architecture.md`
8. `docs/04_module_spec.md`
9. `docs/05_variable_spec.md`
10. `docs/06_state_spec.md`
11. `docs/07_test_plan.md`
12. `docs/08_development_plan.md`
13. `docs/11_data_source_policy.md`（Data 実装前は必読）
14. `ops/AGENT_WORKFLOW.md`
15. `ops/CURRENT_TASKS.md`
16. `ops/DECISION_LOG.md`

## 4. 読み方の目安

### 4.1 まず全体像を把握したい場合
- `README.md`
- `docs/01_overview.md`
- `docs/02_requirements.md`
- `docs/03_architecture.md`

### 4.2 実装に入る前に必要な場合
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`
- Data 実装に入る場合は `docs/11_data_source_policy.md` を必ず確認する
- `docs/11` では CSV / parquet / pkl の役割、UTC 統一、spread / bid-ask / volume、H1/H4 集約、用途別採用判定を確認する

### 4.3 今何をやるべきか知りたい場合
- `ops/CURRENT_TASKS.md`

### 4.4 過去に何を決めたか知りたい場合
- `ops/DECISION_LOG.md`

### 4.5 実験中の裁量パターンを知りたい場合
- `docs/experiments/EXPERIMENT_INDEX.md`
- `docs/experiments/exp_*.md`

### 4.6 モジュール間I/O契約を補助的に確認したい場合
- `docs/10_interface_contract.md`
- ただし `docs/10` は補助文書であり、正式定義は `docs/04` から `docs/07` を優先する

### 4.7 AI の使い分けと段階別手順を確認したい場合
- `ops/AGENT_WORKFLOW.md`
- 5.4thinking / 5.4（VSCode） / Copilot / 5.3 Codex / Human の役割と、Data・Signal・Logger/Evaluator 各フェーズでの依頼順序を確認する

### 4.8 再開時に AI の使い分けをすぐ判断したい場合
- 方向性、受け入れ基準、優先順位、例外境界を決めるなら 5.4thinking（チャット/アプリ）
- 決まった内容を repo 内タスク、対象ファイル、確認観点へ落とし込むなら 5.4（VSCode）
- 骨組み実装や機械的変更を書くなら Copilot / Cursor
- 実装後に docs / 命名 / 契約 / テスト観点を横断で揃えるなら 5.3 Codex（VSCode auto）
- 採用 / 保留 / 却下を決めるのは Human
- 通常運用の主力は 5.3 Codex とし、5.4 は難所限定で使う
- 1ファイル修正や単純追記では 5.4 を使わない
- docs 3枚以上に波及する判断や repo 横断の難所だけ 5.4 を使う
- 依頼は 1目的・少数ファイルに分割する

## 5. このプロジェクトの構造
このプロジェクトでは、大きく以下の層を分けている。

### `docs/`
内部設計資料。
会話履歴に頼らずに実装継続できるようにするための主文書群。

### `ops/`
agent 運用資料、タスク管理、判断記録、レビュー運用資料。

### `src/`
本体実装。

### `tests/`
本体テストおよび実験テスト。

### `docs/experiments/`, `src/experiments/`, `tests/experiments/`
本体未採用の裁量仮説・試作・比較検証の領域。

### `portfolio/`
外部向け文章の下書き。

## 6. 本体と experiments の違い

### 本体
- 採用済みまたは採用候補として安定化を目指す領域
- `src/`
- `tests/`
- 関連する設計文書

### experiments
- 新規裁量パターンや補助ロジックの試作領域
- 本体に直接混ぜない
- 比較・レビュー・採用判断を前提に記録する

新しい裁量知見は、原則として最初から本体へ直接追加しない。

## 7. 実装前に確認すべきこと
実装や修正に入る前に、最低限以下を確認すること。

- 要件が `docs/02_requirements.md` と矛盾しないか
- モジュール責務が `docs/04_module_spec.md` と矛盾しないか
- 変数名が `docs/05_variable_spec.md` と矛盾しないか
- 状態遷移が `docs/06_state_spec.md` と矛盾しないか
- テスト観点が `docs/07_test_plan.md` に存在するか
- Data 実装時のデータ受け入れ基準が `docs/11_data_source_policy.md` と矛盾しないか
- 現在の優先タスクが `ops/CURRENT_TASKS.md` にあるか

## 8. 変更したら更新すべきもの
大きな変更をした場合、コードだけでなく文書も更新する。

### 設計変更
更新候補:
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `ops/DECISION_LOG.md`

### 実装変更
更新候補:
- `ops/worklog/`
- 必要に応じて `ops/review/PENDING_REVIEW.md`
- 採用後は `ops/review/APPROVED_CHANGES.md`

### 実験追加
更新候補:
- `docs/experiments/EXPERIMENT_INDEX.md`
- `docs/experiments/` の個別ノート
- `src/experiments/`
- `tests/experiments/`

## 9. 現在の重要方針
再開時に見落としやすい重要方針を以下にまとめる。

- 主対象は USDJPY
- 他商品への流用可能性を意識する
- 執行足は 5分足
- 上位足は 1時間足・4時間足
- 上位足環境認識と執行足構造認識を分ける
- 中核判断はルールベース
- ML は補助・将来拡張
- 指標時刻フィルターは含める
- 新規裁量パターンは部品として追加しやすい構造を目指す
- docs を主な引き継ぎ基盤とする

## 10. 再開時の最小手順
このプロジェクトを別チャット・別agent・未来の自分が再開する場合、最低限の手順は以下とする。

1. このファイルを読む
2. `AGENT_INDEX.md` と `REPO_MAP.md` を読む
3. `docs/02`〜`08` を読む
4. Data 実装に入る場合は `docs/11_data_source_policy.md` を読む
5. `ops/CURRENT_TASKS.md` を確認する
6. 必要なら `ops/DECISION_LOG.md` を確認する
7. 実験対象なら `docs/experiments/` を確認する
8. 変更前に対象ファイルと影響範囲を整理する
9. 変更後は worklog / review / decision log を必要に応じて更新する

### 10.1 実装フェーズごとの依頼順序（初期版）
1. Data フェーズ:
   - 5.4thinking で受け入れ基準・例外境界を確定
   - 5.4（VSCode）で repo 内タスクへ落とし込む
   - Copilot / Cursor で骨組み実装
   - 5.3 Codex で文書整合と契約チェック
2. Signal フェーズ:
   - 5.4thinking で仕様トレードオフを確定
   - 5.4（VSCode）で repo 内タスクへ落とし込む
   - Copilot / Cursor で骨組み実装
   - 5.3 Codex で境界契約と命名整合を確認
3. Logger / Evaluator フェーズ:
   - 5.4thinking で評価範囲を確定
   - 5.4（VSCode）で repo 内タスクへ落とし込む
   - Copilot / Cursor で骨組み実装
   - 5.3 Codex でログ責務分離と評価整合を確認

## 11. このファイルの更新タイミング
以下の場合は本ファイルの更新を検討する。
- 読む順番が変わったとき
- docs / ops の構成が大きく変わったとき
- 本体と experiments の運用ルールが変わったとき
- 会話履歴依存をさらに下げるための重要方針を追加したとき

## 12. 補足
このプロジェクトでは、「今のチャットで共有されていること」よりも、「repo 内文書に何が残っているか」を優先する。

そのため、重要な設計判断や運用ルールは、できる限り `docs/` または `ops/` に反映してから次へ進むこと。
