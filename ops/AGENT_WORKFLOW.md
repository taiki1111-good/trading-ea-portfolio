# AGENT WORKFLOW

## 1. 目的
本ファイルは、このプロジェクトにおける AI agent と human の役割分担、および変更の基本フローを定義する。

## 2. 運用思想
- 5.4thinking（チャット/アプリ）は最上流判断だけを決める
- 5.4（VSCode）は repo 横断の難所や広域整合だけを落とし込む
- Copilot / Cursor は仕様確定後の機械実装・骨組みを担当する
- 5.3 Codex（VSCode auto）を通常運用の主力にする
- Human は承認する

この順序は、設計判断、repo 内タスクへの変換、実装、横断整合、最終判断を分離するためのものである。

細かい ping-pong を避けるため、原則として 1フェーズまたは 1サブフェーズをまとめて進めてから 5.3 Codex に横断確認させる。
関数単位・数行単位で Copilot / Cursor と 5.3 Codex を往復させない。
途中で設計判断が必要になった場合のみ、5.4thinking または Human に戻す。

## 3. 役割分担

### 5.4thinking（チャット/アプリ）
- 設計判断
- 仕様確定
- 受け入れ基準の確定
- 例外 / 失敗結果 / 非対応範囲の境界確定
- テスト観点と優先順位の整理
- トレードオフ整理

次へ handoff する条件:
- 対象フェーズの目的が 1文で言える
- 受け入れ基準が明文化されている
- 例外境界と非対応範囲が明文化されている
- 未解決論点が残る場合は、未解決であること自体が明記されている

### 5.4（VSCode）
- 5.4thinking の判断を repo 内の作業単位へ落とし込む
- 対象ファイル、対象モジュール、更新すべき docs を整理する
- 実装順序、確認順序、テスト観点を実装者が使える粒度へ変換する
- handoff 用の指示文を短く具体化する

次へ handoff する条件:
- どのファイル / モジュールを触るかが分かる
- 命名、入出力、非対応範囲が実装者に渡せる粒度になっている
- 実装後に 5.3 Codex が確認すべき観点が列挙されている

### Copilot / Cursor
- 定型コード作成
- 骨組みコード生成
- 単純補完
- 既存構造に沿った機械的変更
- 明示済み仕様に沿ったテスト骨組み作成

次へ handoff する条件:
- 対象フェーズの骨組み実装が一通り揃っている
- 明らかな命名揺れや未接続箇所が埋められている
- 実装差分を 5.3 Codex が横断確認できる単位でまとめられている

### 5.3 Codex（VSCode auto）
- 差分横断レビュー
- 設計文書との整合確認
- 複数ファイル変更の俯瞰確認
- 命名、I/O 契約、責務分離、テスト観点の揃え込み
- 小中規模の整合修正

次へ handoff する条件:
- docs と実装の不一致が修正または記録されている
- テスト観点の抜けが洗い出されている
- Human が採用 / 保留 / 却下を判断できる状態になっている

### Human
- 最終判断
- 採用 / 保留 / 却下
- 設計変更の承認
- 外部向け公開内容の決定

次へ handoff する条件:
- 採用 / 保留 / 却下が決まっている
- 必要なら docs / review / decision log の更新方針が決まっている
- 設計判断が不足している場合は 5.4thinking へ戻す

## 4. 基本フロー
1. `ops/CURRENT_TASKS.md` で対象タスクを確認
2. 必要な設計文書を読む
3. 必要なときだけ 5.4thinking が対象フェーズの判断と受け入れ基準を決める
4. 必要なときだけ 5.4（VSCode）が repo 内の作業単位と確認観点へ落とし込む
5. 仕様確定後に Copilot / Cursor が骨組みと定型実装を進める
6. 5.3 Codex が通常運用の主力として、フェーズ単位で横断整合を確認し、必要なら揃え込みを行う
7. `ops/worklog/` に記録を残す
8. 必要に応じて `ops/review/PENDING_REVIEW.md` に追加する
9. Human が確認する
10. 採用時は `ops/review/APPROVED_CHANGES.md` と `ops/DECISION_LOG.md` を更新する

## 5. 実装前に必ず読む文書
- `docs/00_how_to_continue.md`
- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`

## 6. 変更後に残すべきもの
### 必須
- worklog

### 必要に応じて
- review queue
- approved changes
- decision log
- 該当する docs 更新

## 7. 実験追加時のルール
- 新しい裁量パターンは最初から本体へ直接追加しない
- `docs/experiments/`, `src/experiments/`, `tests/experiments/` を使う
- 比較・レビュー・採用判断を経て本体へ反映する

## 8. 禁止事項
- 設計文書と矛盾する変更を無記録で入れること
- experiments の内容を本体へ直接混ぜること
- worklog / review / decision log を飛ばして大きな変更を確定すること
- docs に残っていない前提を増やすこと
- 初期段階で `triangle_break` を main に直接混ぜること
- 競合ケースを曖昧なまま通して売買候補にすること

## 9. フェーズ別 handoff 条件

### 9.1 共通ルール
- 5.4thinking -> 5.4（VSCode）
  - 判断、受け入れ基準、例外境界、優先順位が決まっていること
- 5.4（VSCode） -> Copilot / Cursor
  - 実装対象、命名、I/O、非対応範囲、確認観点が実装可能な粒度になっていること
- Copilot / Cursor -> 5.3 Codex
  - 1フェーズまたは 1サブフェーズの実装がまとまっていること
  - 途中経過ではなく、横断確認に値する差分になっていること
- 5.3 Codex -> Human
  - docs / 実装 / テスト観点の整合が確認済み、または差分と未解決点が記録済みであること
- Human -> 次フェーズ
  - 採用または保留の判断が済み、次に進める条件が明示されていること

### 9.2 ping-pong を避ける原則
- Copilot / Cursor への指示は、関数単位ではなくフェーズ単位またはモジュール単位でまとめる
- 5.3 Codex の確認は、1回の実装まとまりごとに実施する
- 途中で設計が揺れたら、実装側で無理に埋めずに 5.4thinking または Human に戻す
- 小さな修正を何度も往復するより、1フェーズ実装後に 5.3 Codex で横断確認することを優先する

### 9.3 初期 main のパターン方針
- 初期 main の対象構造は `third_wave_break` のみとする
- `triangle_break` は `experiments` 領域で先行検証する
- 複数パターンが競合した場合は安全側で見送り、理由を残す

## 10. 段階別開発手順（初期版）

### 10.1 Data 実装フェーズ
次に誰に何を依頼するか:
- 5.3 Codex（VSCode auto）: 通常運用の主力として、対象 docs の整合確認とタスク化を進める
- 5.4thinking（チャット/アプリ）: 必要なときだけ、受け入れ基準、一次ソース / キャッシュ方針、例外と失敗結果の境界を確定する
- 5.4（VSCode）: 必要なときだけ、`PriceDataLoader`、`EventDataLoader`、`TimeframeAligner`、`DataValidator` に対して、どの docs を見て何を実装するかを repo 内作業へ落とし込む
- Copilot / Cursor: Data モジュール骨組みと定型処理を実装する
- 5.3 Codex（VSCode auto）: 実装後に文書と差分の横断整合を確認する

Data フェーズの handoff 条件:
- 5.4thinking -> 5.4（VSCode）
  - 受け入れ基準、一次ソース / キャッシュ方針、例外境界が明文化されている
- 5.4（VSCode） -> Copilot / Cursor
  - 対象モジュール、入出力名、確認対象 docs、テスト観点が列挙されている
- Copilot / Cursor -> 5.3 Codex
  - Data 骨組み一式がまとまりとして実装されている
- 5.3 Codex -> Human
  - Data 契約、命名、テスト観点の整合が確認されている

Data 実装後に 5.3 Codex に確認させる項目:
- `docs/04` と実装の入出力名が一致しているか
- `data_valid_flag` / `validation_reason` の扱いが `docs/07` / `docs/10` と一致しているか
- CSV / parquet / pkl の役割が `docs/11_data_source_policy.md` と矛盾しないか
- timezone / 欠損 / H1-H4 集約 / spread / bid-ask / volume の判定観点がテストへ反映されているか

### 10.2 Signal 実装フェーズ
次に誰に何を依頼するか:
- 5.3 Codex（VSCode auto）: 通常運用の主力として、境界契約と命名観点の整合確認・タスク化を進める
- 5.4thinking（チャット/アプリ）: 必要なときだけ、エントリー / イグジット判断の優先順位とトレードオフを確定する
- 5.4（VSCode）: 必要なときだけ、Signal 系モジュールごとの責務、接続順、確認対象 docs を repo 内作業へ落とし込む
- Copilot / Cursor: `DirectionAlignChecker`、`PatternGate`、`EntryRuleEngine`、`ExitRuleEngine`、`SignalAssembler` の定型実装を進める
- 5.3 Codex（VSCode auto）: 実装後に境界契約とテスト観点の整合を確認する

Signal フェーズの handoff 条件:
- 5.4thinking -> 5.4（VSCode）
  - 優先順位、非対応範囲、主要トレードオフが明文化されている
- 5.4（VSCode） -> Copilot / Cursor
  - Signal 系モジュールの責務分割と命名方針が実装可能な粒度になっている
- Copilot / Cursor -> 5.3 Codex
  - Signal フェーズの骨組み実装が一まとまりで揃っている
- 5.3 Codex -> Human
  - I/O 契約、命名、追跡要件、テスト観点の整合が確認されている

Signal 実装後に 5.3 Codex に確認させる項目:
- HTFContext / LTFStructure -> Signal の受け渡しが `docs/04` / `docs/10` と一致しているか
- `signal_type`、`entry_signal`、`exit_signal`、`signal_reason` の命名と意味が `docs/05` / `docs/07` と一致しているか
- `breakout_flag` と `pattern_reason` の追跡要件が崩れていないか

### 10.3 Logger / Evaluator 実装フェーズ
次に誰に何を依頼するか:
- 5.3 Codex（VSCode auto）: 通常運用の主力として、ログ責務分離と評価契約の整合確認・タスク化を進める
- 5.4thinking（チャット/アプリ）: 必要なときだけ、評価スコープ、比較軸、レポート粒度の優先順位を確定する
- 5.4（VSCode）: 必要なときだけ、Logger / Evaluator の責務分離と集計対象を repo 内作業へ落とし込む
- Copilot / Cursor: `DecisionLogger`、`TradeLogger`、`StateLogger`、`EventLogger` と Evaluator の基本集計骨組みを実装する
- 5.3 Codex（VSCode auto）: 実装後にログ責務分離と評価契約の整合を確認する

Logger / Evaluator フェーズの handoff 条件:
- 5.4thinking -> 5.4（VSCode）
  - 評価スコープ、比較軸、粒度優先順位が明文化されている
- 5.4（VSCode） -> Copilot / Cursor
  - ログ責務と集計対象が実装可能な粒度に落ちている
- Copilot / Cursor -> 5.3 Codex
  - Logger / Evaluator の骨組みがフェーズ単位でまとまっている
- 5.3 Codex -> Human
  - 責務分離、指標セット、比較軸、テスト観点の整合が確認されている

Logger / Evaluator 実装後に 5.3 Codex に確認させる項目:
- `state_logs` / `event_logs` / `trade_logs` / `decision_logs` の責務分離が `docs/04` / `docs/10` / `docs/06` と一致しているか
- Evaluator の正式指標セットと比較軸が `docs/04` / `docs/05` / `docs/07` / `docs/10` と一致しているか
- 月次・構造別・signal_type別・filter_reason別集計のテスト観点が欠けていないか

## 11. AIコスト最適化ルール（固定）
### 11.1 役割固定
- 5.4thinking（チャット/アプリ）は最上流の判断専用とする
- 5.4（VSCode）は repo 横断の難所や広域整合のときだけ使う
- 5.3 Codex（VSCode auto）を通常運用の主力にする
- Copilot / Cursor は仕様確定後の機械実装・骨組み作成に使う
- Human が採用 / 保留 / 却下を決める

### 11.2 5.4の使用条件
- 1ファイル修正や単純追記では 5.4 を使わない
- docs 3枚以上に波及する判断や難所だけ 5.4 を使う
- 途中で設計判断が必要になった場合のみ 5.4thinking に戻す

### 11.3 通常運用の優先順
- 通常の docs 追記・整合・実装補助は 5.3 Codex を優先する
- 依頼は 1目的・少数ファイルに分割する
- 小さな修正を多数同時に投げず、まとまり単位で確認する

## 12. Codex /review 使用方針
`/review` は実装前の設計相談ではなく、実装後・採用前の横断確認に使う。

### 12.1 `/review` を使うべき場面
- 1フェーズまたは1サブフェーズの実装が完了した後
- 採用/保留判断の前
- docs / code / tests / ops が同時に変わったとき
- 3ファイル以上にまたがる変更があるとき
- `BacktestRunner` / `PipelineAdapter` / `RiskFilter` / `Signal` / `Execution` の境界に触れたとき
- `pytest` は通ったが、docs契約・I/O・責務分離・副作用を横断確認したいとき
- main / experiments の境界混入が疑われるとき
- 実装済みでない機能を過剰表現していないか確認したいとき

### 12.2 `/review` を使わなくてよい場面
- 1〜2行程度の文言修正
- worklogだけの軽微追記
- `ops/CURRENT_TASKS.md` の軽微整理
- 実装前の設計相談
- 仕様がまだ固まっていない段階
- 1ファイルだけの単純変更で、関連テストも明確な場合

### 12.3 `/review` に渡すべき観点
- `docs/04_module_spec.md` / `docs/05_variable_spec.md` / `docs/10_interface_contract.md` / `docs/17_backtest_design.md` との整合
- I/O契約と実装の一致
- 既存 Backtest / Pipeline / Signal / Execution への副作用
- test coverage の不足
- `ops/CURRENT_TASKS.md` / `ops/worklog/` との整合
- 実装済みでない機能を実装済み扱いしていないか
- main / experiments 境界を壊していないか

### 12.4 subagents の使いどころ
- subagents は通常作業では必須ではない
- 大きな横断変更を専門観点に分けるときだけ使う
- 例:
  - Contract Reviewer: docs契約との整合
  - Test Reviewer: unit/integration test観点
  - Regression Reviewer: `BacktestRunner` / `PipelineAdapter` / `Signal` / `Execution` 副作用
  - Ops Reviewer: `ops/CURRENT_TASKS.md` / `ops/worklog/` / `AGENTS.md` 整合
- 小さい変更で使うと文脈同期コストが増えるため避ける

### 12.5 このrepoでの推奨タイミング
- Risk/Stop v0 のように docs/code/tests/ops が横断的に変わった後は `/review` 推奨
- Session/SR/HTF filter化のように entry集合に影響する変更後は `/review` 推奨
- lot sizing本体、`PipelineAdapter` 変更、`BacktestRunner` 変更後は `/review` 推奨
- 単なる docs 追記や worklog 追記だけなら不要
