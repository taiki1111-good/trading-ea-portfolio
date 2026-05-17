# AGENTS.md

## 1. Purpose
- このファイルは、`trading-ea` repo で作業する AI agent 向けの入口ルールである。
- この repo は設計先行の研究用EAプロジェクトである。
- 実運用EA、収益性確認済みシステム、broker接続済みシステムとして扱わない。

## 2. Source of Truth
- 作業前に次を読む: `README.md`, `ops/CURRENT_TASKS.md`, `ops/AGENT_WORKFLOW.md`, `docs/03_architecture.md`, `docs/04_module_spec.md`, `docs/05_variable_spec.md`, `docs/07_test_plan.md`, `docs/10_interface_contract.md`, `docs/17_backtest_design.md`。
- 現在状況の第一参照は `ops/CURRENT_TASKS.md`。
- agent/human の役割分担と作業フローの正本は `ops/AGENT_WORKFLOW.md`。
- `docs/04_module_spec.md` / `docs/05_variable_spec.md` / `docs/10_interface_contract.md` / `docs/17_backtest_design.md` と矛盾する変更は、記録なしで行わない。

## 3. Current Project Constraints
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- Phase 9 CSV replay pipeline dry-run minimal completion reached。
- Risk/Stop v0 minimal implementation exists。
- `PositionSizer` は placeholder。
- lot sizing 本体は未実装。
- `account_balance` / `risk_per_trade` / 複利 / broker lot制約厳密化は後続。
- Session/SR/HTF filter化は未実装。
- 株式拡張は future extension であり、実装未着手。
- 詳細な最新状況は `ops/CURRENT_TASKS.md` を参照する。

## 4. Hard Prohibitions
- real broker connectivity を追加しない。
- OANDA/API connectivity を追加しない。
- real order sending を追加しない。
- live readiness を主張しない。
- profitability を主張しない。
- demo operation readiness を主張しない。
- experiments を main logic に直接混ぜない。
- `triangle_break` を明示承認なしに main に入れない。
- lot sizing 本体を明示承認なしに実装しない。
- equity expansion を明示承認なしに実装しない。
- BacktestRunner / PipelineAdapter / Signal / Execution の挙動を、docs確認と記録なしに変更しない。
- `docs/04` / `docs/05` / `docs/10` / `docs/17` の契約を無記録で変更しない。

## 5. Implementation Rules
- minimal diff を優先する。
- 実装前に relevant docs と `ops/CURRENT_TASKS.md` を読む。
- main と experiments を分離する。
- 変更した挙動には test を追加・更新する。
- 意味のある変更では `ops/worklog/` を更新する。
- 状態が変わる場合は `ops/CURRENT_TASKS.md` を更新する。
- durable decision の場合だけ `ops/DECISION_LOG.md` を更新する。

## 6. Risk/Stop v0 Rules
- `trade_ok=true` には valid `lot`, `stop_loss`, `take_profit` が必要。
- invalid `lot`, `stop_loss`, `take_profit` は `trade_ok=false` にする。
- `PositionSizer` は placeholder only。
- fixed lot は placeholder としてのみ許容する。
- lot sizing body は deferred。
- `risk_reason` / `filter_reason` は v0 では string のまま。
- reason token は推奨値として使えるが、正式 enum ではない。
- `entry_price_candidate` は RiskFilter 入力価格。
- `entry_price` / `fill_price` は Execution 後の概念。
- `max_holding_bars` は Backtest / Exit 側の時間退出条件であり、Risk/Stop v0 の主責務ではない。

## 7. Testing Rules
- code change 時は relevant tests を実行する。
- 可能なら `$env:PYTHONPATH='.'` の後に `pytest -q` を実行する。
- focused change では targeted test -> full pytest の順を推奨する。
- テスト未実行の場合は理由を報告する。

## 8. Reporting Format
- 作業後は次の順で報告する。
1. changed files
2. what changed
3. what did not change
4. tests run and results
5. docs/ops updates
6. remaining unresolved points
7. next recommended step
- commit summary は user から明示要求がある場合のみ出す。

## 9. Documentation Rules
- `docs/` は設計・契約。
- `ops/CURRENT_TASKS.md` は現在状況と次タスク。
- `ops/worklog/` は作業記録。
- `ops/DECISION_LOG.md` は durable decision のみ。
- minor implementation change で docs を過剰更新しない。
- major behavior change を undocumented にしない。

## 10. Agent Workflow
- 詳細な agent/human 役割分担は `ops/AGENT_WORKFLOW.md` に従う。
- upstream design decision -> implementation -> cross-file consistency review -> human approval の順を守る。
- 小さな ping-pong を避け、1フェーズまたは1サブフェーズ単位で進める。
- For Codex `/review` usage, follow `ops/AGENT_WORKFLOW.md`. Use `/review` after a completed phase or sub-phase when cross-file consistency must be checked before adoption. Do not use it for small text-only edits or unresolved design discussions.

## Non-scope
- 実装コード変更
- テスト変更
- OANDA/API接続
- 実注文
- demo口座接続
- broker連携
- PipelineAdapter本体の売買判断変更
- BacktestRunner本体の戦略変更
- HTF/SR/Session/RiskStop/Halt filter化実装
- 株式拡張
- Equity Adapter
- lot sizing本体実装
- account_balance連動
- risk_per_trade実装
- broker lot制約厳密化
- 収益性評価
- パラメータ最適化
- ML/HMM/LSTM実装
- Triangle / Trap / reaction SR のmain導入
- experimental exit candidate の本採用
