# 2026-05-09 risk stop v0 pre impl acceptance

## 目的
- Risk/Stop v0 実装に進む前の最終受け入れ基準を docs / ops に固定する。
- 今回は実装ではなく契約整理のみを行う。

## 今回決めた `lot` / `trade_ok` 方針
- `trade_ok=true` の場合、`lot` / `stop_loss` / `take_profit` は有効値でなければならない。
- `lot` が未算出・空・`<=0`・不正値の場合、`trade_ok=true` は許容しない。
- 上記不整合時は `trade_ok=false` とし、`risk_reason` または `filter_reason` に停止根拠を残す。

## PositionSizer placeholder の扱い
- PositionSizer は将来的に lot sizing 本体を担う。
- Risk/Stop v0 実装時は placeholder として固定lot（または設定値lot）を返す最小方式を許容する。
- placeholder の目的は `RiskFilter -> Execution` 契約を満たすことであり、資金管理最適化ではない。
- placeholder 理由は当面 `risk_reason` に残す（例: `placeholder_fixed_lot`）。
- `position_sizing_reason` など専用新変数は v0 必須としない。

## lot sizing 本体との分離
- 今回も `lot sizing` 本体は対象外。
- 非対応として維持:
  - `account_balance` 連動
  - `risk_per_trade`
  - 複利連動
  - broker 最小/最大lot・刻み制約の厳密化
- 上記は後続フェーズで固定する。

## `risk_reason` / `filter_reason` の扱い
- v0 は自由文字列を維持する。
- 実装・テスト追跡用の推奨トークン例を記録した（正式 enum ではない）。
- 推奨例:
  - `risk_reason`: `fixed_sl_tp`, `placeholder_fixed_lot`, `invalid_stop_loss`, `invalid_take_profit`, `invalid_lot`
  - `filter_reason`: `spread_too_wide`, `event_risk`, `trade_limit_reached`, `risk_contract_invalid`
- enum化や管理語彙化は後続候補。

## `entry_price_candidate` の扱い
- RiskFilter 入力文脈の価格は `entry_price_candidate` を優先語とする。
- Execution 後の確定価格は `entry_price` または `fill_price` として扱う。
- 既存 docs の `entry_price` 表記を即時全置換はしない。
- v0 文脈では候補価格と確定価格を混同しない注意を維持する。

## `max_holding_bars` との境界
- `max_holding_bars` は Backtest / Exit 側の時間退出条件として扱う。
- Risk/Stop v0 の主責務は entry 時点の `trade_ok` / `lot` / `stop_loss` / `take_profit` / `risk_reason` / `filter_reason`。
- 時間起因の exit policy 採用判断は Risk/Stop v0 の主責務にしない。
- `fixed_sl_tp` baseline 維持と整合させる。

## 実装フェーズに進む場合の完了条件（今回未実装）
- StopLossPlanner / TakeProfitPlanner / PositionSizer placeholder / RiskAssembler の最小実装。
- `trade_ok=true` 時に `lot` / `stop_loss` / `take_profit` が有効値。
- `trade_ok=false` 時に `risk_reason` または `filter_reason` が空でない。
- long/short で SL/TP の方向が正しい。
- `lot` 未算出・不正値時は `trade_ok=false`。
- `fixed_sl_tp` baseline を壊さない。
- experimental exit candidate と混同しない。
- unit test を追加し、関連 `pytest` が通る。
- BacktestRunner / PipelineAdapter / Signal / Execution の本体挙動を不必要に変更しない。

## 非対応範囲（今回維持）
- OANDA/API接続、実注文、demo口座接続、broker連携
- PipelineAdapter本体の売買判断変更
- BacktestRunner本体の戦略変更
- HTF/SR/Session/RiskStop/Halt の filter化実装
- 株式拡張、Equity Adapter
- lot sizing本体実装
- account_balance連動、risk_per_trade実装、broker lot制約厳密化
- 収益性評価、パラメータ最適化、ML/HMM/LSTM実装
- Triangle / Trap / reaction SR のmain導入

## 実装変更有無
- 実装コード変更なし。
- docs / ops のみ更新。

## 残る未解決点
- `risk_reason` / `filter_reason` の管理語彙化をいつ開始するか。
- `entry_price_candidate` 命名統一の全体適用タイミング。
- PositionSizer placeholder から本体 lot sizing へ移行する段階条件。

## テスト実行有無
- テスト未実行。
- 理由: 変更対象が docs / ops のみで、実装コードに変更がないため。
