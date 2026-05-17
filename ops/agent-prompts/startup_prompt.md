# startup prompt（作業開始用）

あなたは `trading-ea` リポジトリで作業する AI agent です。  
以下のルールに従って開始してください。

## 1) 作業前に読むべきファイル（順序）
1. `AGENT_INDEX.md`
2. `REPO_MAP.md`
3. `docs/00_how_to_continue.md`
4. `ops/VS_CODE_SETUP.md`
5. `docs/02_requirements.md`
6. `docs/03_architecture.md`
7. `docs/04_module_spec.md`
8. `docs/05_variable_spec.md`
9. `docs/06_state_spec.md`
10. `docs/07_test_plan.md`
11. `docs/08_development_plan.md`
12. `ops/AGENT_WORKFLOW.md`
13. `ops/CURRENT_TASKS.md`

## 2) 設計・実装ルール
- architecture を勝手に発明しない。既存 SoT（`docs/02` から `docs/08`）を優先する。
- docs と ops を主知識源とし、会話履歴だけに依存しない。
- `.vscode/settings.json` と `.vscode/extensions.json` を repo 固有の環境定義として尊重する。
- low coupling / high cohesion を守る。モジュール境界を越える責務混入を避ける。
- 命名・I/O・状態遷移は既存仕様に合わせる。独自語彙を増やさない。

## 3) 変更時の必須確認
- 変更対象コードだけでなく、関連 docs 更新要否を確認する。
- 仕様影響がある場合は、更新対象 docs を列挙する（例: `docs/04`, `docs/05`, `docs/06`, `docs/07`, `docs/08`）。
- テスト影響（追加/修正/不要）を明記する。

## 4) 出力ルール
- 最初に「対象」「前提」「実施内容」を短く示す。
- 変更がある場合は「変更ファイル一覧」「未解決事項」「次アクション」を示す。
- 仕様判断が必要な点は、実装と分離して明示する。
