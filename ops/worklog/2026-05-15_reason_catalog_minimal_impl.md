# 2026-05-15 reason catalog minimal implementation

## 1. 目的
- docs/opsで決定済みの `Reason Catalog + 定数運用` を最小差分で実装する。
- enum化せず、既存ログ互換を維持しながら `category_token[:detail]` 形式を扱えるようにする。

## 2. 実施内容
### 2.1 Reason Catalog 追加
- `src/risk_filter/reason_catalog.py` を追加。
- canonical category token を文字列定数として定義（enumは未使用）。
- 例:
  - `all_risk_filters_passed`
  - `fixed_sl_tp`
  - `placeholder_fixed_lot`
  - `invalid_lot`
  - `invalid_stop_loss`
  - `invalid_take_profit`
  - `invalid_account_balance`
  - `missing_entry_signal`
  - `unsupported_signal_type`
  - `risk_contract_invalid`

### 2.2 正規化ヘルパ
- `normalize_reason_category(reason: str) -> str` を追加。
- 挙動:
  - `category_token[:detail]` から `category_token` を抽出。
  - 空白/ハイフンを `_` 化して lower に正規化。
  - 旧形式 `all risk filters passed` を `all_risk_filters_passed` に正規化。

### 2.3 既存出力への最小反映
- `RiskAssembler`:
  - reason文字列のハードコードを定数参照へ寄せた。
  - 成功時 `filter_reason` は互換維持のため **`all risk filters passed` を維持**。
  - `risk_contract_invalid: ...` の detail 部は `missing_entry_signal` / `unsupported_signal_type` を使用。
- `PositionSizer`:
  - `placeholder_fixed_lot` / `invalid_lot` を定数参照化。
  - 無効balance時は `invalid_account_balance: ...` を併記。
- `StopLossPlanner` / `TakeProfitPlanner`:
  - `fixed_sl_tp` / `invalid_*` を定数参照化。

## 3. 互換ポリシー
- 既存ログ互換のため、成功時 `filter_reason` は旧形式 (`all risk filters passed`) を出力継続。
- 集計側は `normalize_reason_category()` を使うことで旧/新両形式を同一categoryに寄せられる。
- 売買ロジック、`trade_ok` 判定、PipelineAdapter の判断挙動は変更していない。
- 互換保証の主対象は `category_token` レベルとし、detail 文字列の完全一致は保証対象外とする。
- `risk_contract_invalid` の detail は旧形式（`entry_signal_false` / `non_entry_signal_type=...`）と新形式（`missing_entry_signal` / `unsupported_signal_type=...`）が混在しうる。
- したがって、既存ログの完全一致比較は非推奨とし、`normalize_reason_category()` による category 抽出を前提に運用する。
- `PositionSizer` の失敗理由は `invalid_lot` を維持しつつ detail 併記を許容し、meaning互換を優先する。

## 4. テスト
実行コマンド:
- `pytest -q tests/unit/risk_filter`
- `pytest -q tests/integration/test_signal_to_risk_filter.py`
- `pytest -q tests/unit/backtest/test_pipeline_adapter.py`

結果:
- `tests/unit/risk_filter`: 33 passed
- `tests/integration/test_signal_to_risk_filter.py`: 8 passed
- `tests/unit/backtest/test_pipeline_adapter.py`: 56 passed

追加/更新テスト:
- `tests/unit/risk_filter/test_reason_catalog.py` を新規追加。
  - 新形式/旧形式/`category_token:detail` 抽出を確認。
- `tests/unit/risk_filter/test_position_sizer.py` を更新。
  - `invalid_account_balance` 併記を確認。

## 5. 未解決・後続
- `all risk filters passed` を canonical出力へ切り替える段階移行は未着手（今回は互換優先）。
- Evaluator/分析スクリプト側で category 正規化を共通利用する実装は後続。
- Reason Catalog を他モジュール理由列まで広げるかは後続判断。

