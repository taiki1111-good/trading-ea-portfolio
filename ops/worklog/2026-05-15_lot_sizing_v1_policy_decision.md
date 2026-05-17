# 2026-05-15 lot sizing v1 policy decision

## 目的
- lot sizing本体フェーズを独立させるかを判断し、docs/ops に固定する。
- 今回は実装コード・テスト・PipelineAdapter を変更しない。

## 最終判断
- lot sizing本体フェーズは独立させる（フェーズ名: `Lot Sizing v1`）。
- ただし今すぐ `PipelineAdapter` 本線へ接続しない。
- `fixed_lot` baseline は維持する。
- 初期実装は isolated calculator / unit test / contract に限定する。
- `PipelineAdapter` 接続は後続判断とする。

## 判断理由
1. `PositionSizer` は placeholder であり、現時点で本線へ risk-based lot sizing を入れると影響範囲が広い。
2. lot sizing本体はまず数式・設定・invalid・rounding/clamp の契約固定が必要。
3. isolated calculator なら unit test だけで仕様固定でき、pipeline挙動を壊さずに進められる。
4. `fixed_lot` baseline を維持することで、既存の backtest/pipeline 比較基準を保持できる。

## Lot Sizing v1 初期スコープ
- risk-based lot calculation の設計
- config項目案
- I/O contract
- invalid条件
- rounding / clamp 方針
- unit test方針
- fixed_lot baseline との関係
- PipelineAdapter接続条件

## 入力候補（calculator）
- `account_balance`
- `risk_per_trade`
- `stop_loss_distance`
- `pip_value`
- `lot_step`
- `min_lot`
- `max_lot`
- rounding policy

## 出力候補（calculator）
- `lot`
- `size_reason`（reason catalog token）
- invalid判定結果（reasonで表現）

## 非対応範囲
- PipelineAdapter本線接続
- backtest PnLの変更
- 実運用lot制約
- OANDA/API接続
- 実注文
- broker別制約厳密化
- 収益性評価
- 売買ロジック変更

## Go 条件
1. formula が docs/ops に固定されている。
2. config項目が固定されている。
3. invalid条件が固定されている。
4. `fixed_lot` baseline を壊さない。
5. unit test だけで検証できる。
6. `PipelineAdapter` 未接続でも完了扱いにできる。

## No-Go 条件
- broker仕様に依存しすぎる設計になる。
- PnL や trade_count が変わる前提になる。
- `PipelineAdapter` に接続しないと成立しない設計になる。
- 実運用制約までスコープが広がる。
- 収益性評価へ論点が広がる。

## 次実装に渡す最小方針
- `PositionSizer` 既存placeholderは維持したまま、別モジュール（または独立関数）で lot calculator を実装する。
- unit test で式、invalid、rounding/clamp、境界値を固定する。
- `PipelineAdapter`・BacktestRunner・売買ロジックは変更しない。
