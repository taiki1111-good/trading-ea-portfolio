# 2026-05-09 risk stop v0 scope design

## 目的
- Phase 9 minimal completion 後の次フェーズとして、Risk/Stop 本体設計前段の docs / ops 整理を固定する。
- 今回は実装ではなく、責務境界・I/O・非対応範囲・受け入れ基準の明文化を目的とする。

## 今回整理した Risk/Stop v0 の対象範囲
- 対象（固定）:
  - `trade_ok`
  - `stop_loss`
  - `take_profit`
  - `risk_reason`
  - `filter_reason`
  - `entry_price`（または `entry_price_candidate` 文脈）
  - `signal_type`
  - `structure_type`
  - `spread`
  - `event_flag`
  - `max_holding_bars` との関係（Backtest exit 条件との接続前提）
  - `fixed_sl_tp` baseline との関係
- 非対象（今回固定しない）:
  - `lot sizing` 本体実装
  - account balance を使った建玉計算
  - `risk_per_trade`
  - 複利・資金曲線連動
  - broker ごとの最小ロット / 最大ロット厳密化
  - 実注文
  - slippage 本格モデル
  - 手数料・スワップ厳密計算
  - ML 最適化、パラメータ最適化
  - live OANDA/API 接続

## lot sizing を除外した理由
- Risk/Stop v0 はまず `trade_ok` と SL/TP 決定責務の境界固定を優先し、lot 計算ロジックを混在させないため。
- `lot` は契約変数として維持しつつ、計算式・残高連動・`risk_per_trade`・broker 制約の詳細は後続で分離して固定するため。
- Phase 9 直後は実装前段の docs 整理を目的としており、売買挙動を変える本体実装を避けるため。

## fixed_sl_tp baseline との関係
- `fixed_sl_tp` は BacktestRunner 本体既定 baseline として維持する。
- Risk/Stop v0 は baseline を壊さず、SL/TP と可否理由の責務境界を docs 上で明確化する。
- 今回は exit policy 採用判断フェーズではない。

## experimental exit と混同しない方針
- `simple_trailing_after_1R` などは本採用ではなく、experimental exit candidate のまま扱う。
- experimental exit 比較と Risk/Stop v0 の責務境界整理は別トラックとして扱う。
- M5/M1 replay の比較結果をもって、今回の Risk/Stop v0 仕様固定と混同しない。

## 更新した docs / ops
- `docs/04_module_spec.md`
  - RiskFilter 下位部品のうち Risk/Stop v0 の対象責務を明記
  - StopLossPlanner / TakeProfitPlanner / PositionSizer / RiskAssembler の v0 境界を追記
- `docs/05_variable_spec.md`
  - `trade_ok` / `stop_loss` / `take_profit` / `risk_reason` / `filter_reason` / `lot` の v0 扱いを明記
  - `lot sizing` 詳細は未確定隔離として追記
- `docs/10_interface_contract.md`
  - Signal -> RiskFilter -> Execution 境界で Risk/Stop v0 の I/O 追跡方針を追記
  - `trade_ok=false` 時の `filter_reason` / `risk_reason` 記録方針を明記
- `docs/17_backtest_design.md`
  - `fixed_sl_tp` baseline 維持と Risk/Stop v0 の関係を追記
  - experimental exit candidate と混同しない方針を明記
- `ops/CURRENT_TASKS.md`
  - 次タスクを Risk/Stop v0 docs 整理中心に更新
  - 実装未着手、`lot sizing` 本体後続保持を明記

## 実装変更有無
- 実装コード変更なし。
- 売買ロジック、PipelineAdapter本体、BacktestRunner本体、Signal、Execution の変更なし。

## 受け入れ基準（Risk/Stop v0 docs整理完了条件）
- Risk/Stop v0 が扱う範囲が明確である。
- `lot sizing` 本体が対象外として分離されている。
- `fixed_sl_tp` baseline を壊さない方針が明記されている。
- experimental exit candidate と混同していない。
- Signal -> RiskFilter -> Execution の境界が曖昧でない。
- `trade_ok` / `stop_loss` / `take_profit` / `risk_reason` / `filter_reason` の役割が追跡可能である。
- 実装に入る前の未解決点が明記されている。
- 収益性確認済み・実運用可能を示す表現がない。
- 実装コードを変更していない。

## 残る未解決点（実装前に判断が必要）
- `PositionSizer` 詳細仕様の固定タイミング（Risk/Stop v1 か別フェーズか）。
- `lot` 未算出時に `trade_ok=true` を許容するかの暫定運用ルール。
- `risk_reason` と `filter_reason` の語彙制約（enum化の要否）。
- `entry_price` と `entry_price_candidate` の命名統一タイミング。
- `max_holding_bars` と Risk 側理由（時間起因停止）の責務境界の厳密化。

## テスト実行有無
- テスト未実行。
- 理由: 変更対象が docs / ops のみで、実装コードに変更がないため。
