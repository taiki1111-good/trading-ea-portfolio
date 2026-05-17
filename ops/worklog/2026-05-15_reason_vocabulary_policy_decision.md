# 2026-05-15 reason vocabulary policy decision

## 1. 目的
- `risk_reason` / `filter_reason` の管理語彙化方針を決める。
- 今回は実装ではなく、docs/ops の判断固定を行う。

## 2. 調査対象
- docs: `docs/05_variable_spec.md`, `docs/10_interface_contract.md`, `docs/17_backtest_design.md`
- ops: `ops/CURRENT_TASKS.md`
- code: `src/risk_filter/`, `src/backtest/pipeline_adapter.py`
- tests: `tests/unit/risk_filter/`, `tests/unit/backtest/test_pipeline_adapter.py`, `tests/integration/test_signal_to_risk_filter.py`

## 3. 現状観測（reason値の実態）
### 3.1 `risk_reason`
- 実質トークン中心。
- 代表値: `fixed_sl_tp`, `placeholder_fixed_lot`, `invalid_lot`, `invalid_stop_loss`, `invalid_take_profit`, `risk_contract_invalid`。
- 連結形式（` | `）で複数理由を保持。

### 3.2 `filter_reason`
- 実質トークン中心 + 一部自由文。
- 代表値: `event_risk`, `spread_too_wide`, `trade_limit_reached`, `risk_contract_invalid`。
- 成功時に現行実装は `all risk filters passed`（空白含む自然文）を返す。
- 一部 `risk_contract_invalid: ...` の詳細付き形式あり。

### 3.3 他reason
- `decision_reason` / `signal_reason` / `pattern_reason` / `htf_context_reason` は説明文中心。
- 人間向けトレースであり、固定語彙での厳密集計対象とは役割が異なる。

## 4. 判断候補の評価
### A. enum化
- メリット: 型安全、誤字防止、集計軸固定。
- デメリット: 既存ログ/テスト/分析スクリプトへの影響が大きい。詳細文脈を持ちにくい。

### B. Reason Catalog + 定数運用
- メリット: 既存文字列運用と互換を保ちつつ、語彙管理を明確化できる。
- デメリット: enumよりは厳密性が弱い。運用規律が必要。

### C. 自由文維持 + prefix/category固定
- メリット: 柔軟、導入コスト低。
- デメリット: 運用次第で再び語彙が散らばりやすい。

### D. 保留
- メリット: 変更リスクゼロ。
- デメリット: 現タスク未解決、集計安定化が進まない。

## 5. 最終判断
- **採用: B（Reason Catalog + 定数運用）**。
- 補助: Cの一部として `category_token[:detail]` 形式を許容。
- 不採用: A（現時点でのenum化）は deferred。

理由:
1. Phase 9直後は構造検証段階で、既存ログ互換を崩す変更を避けるべき。
2. すでに `risk_reason` / `filter_reason` は実質語彙化されており、catalog化で十分に管理可能。
3. 説明文系reason（decision/signal/pattern/htf_context）は自由文を維持した方が追跡性が高い。

## 6. 境界整理
- 管理語彙（集計主軸）:
  - `risk_reason`
  - `filter_reason`
- 説明用自由文（人間向け）:
  - `decision_reason`
  - `signal_reason`
  - `pattern_reason`
  - `htf_context_reason`

## 7. 今回実施した docs/ops 更新
- `docs/05_variable_spec.md`
  - Reason語彙管理方針（2026-05-15）を追加。
- `docs/10_interface_contract.md`
  - RiskFilter境界でのReason Catalog運用と自由文reason境界を追加。
- `ops/CURRENT_TASKS.md`
  - 「enum化要否判断」を完了扱いへ更新。
  - 次フェーズに「Reason Catalog実装準備」を追加。

## 8. 今回あえて実施しないこと
- `src/` 実装コード変更。
- `tests/` 変更。
- 既存reason文字列の一括置換。
- enum導入。

## 9. 次フェーズ実装プロンプト案（今回未実施）
- 目的:
  - `risk_reason` / `filter_reason` のReason Catalogを実装コードへ反映し、文字列揺れを防ぐ。
- スコープ:
  - `src/risk_filter/` に reason定数モジュールを追加。
  - `RiskAssembler` 成功時 `all risk filters passed` を catalog値（例: `all_risk_filters_passed`）へ段階移行。
  - `category_token[:detail]` の正規化ヘルパを追加（破壊的置換なし）。
  - Evaluator/集計側は `:` 前のcategoryで集計可能にする（必要箇所のみ）。
  - 既存ログ互換維持のため、移行期間は旧文字列受理テストを残す。
- 非スコープ:
  - enum化。
  - lot sizing本体。
  - 売買ロジック変更。

## 10. テスト
- 今回は docs/ops 変更のみのため未実行。

