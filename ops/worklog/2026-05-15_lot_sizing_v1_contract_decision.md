# 2026-05-15 lot sizing v1 contract decision

## 目的
- `Lot Sizing v1` isolated calculator 実装前に、formula/config/invalid/rounding/clamp を docs/ops に固定する。
- 今回はコード実装・テスト実装を行わず、実装前契約の固定のみを対象とする。

## 前提
- `Lot Sizing v1` は独立フェーズとして採用済み。
- 初期実装は isolated calculator + unit test に限定。
- `PipelineAdapter` / `BacktestRunner` / main path には接続しない。
- `fixed_lot` baseline、`PositionSizer` placeholder、現行 planner chain 本線挙動は維持。

## formula（固定）
- `lot = account_balance * risk_per_trade / (stop_loss_distance_pips * pip_value_per_lot)`

## 入力（固定）
- `account_balance`
- `risk_per_trade`
- `stop_loss_distance_pips`
- `pip_value_per_lot`
- `lot_step`
- `min_lot`
- `max_lot`
- `rounding_mode`

## 出力（固定）
- `lot`
- `raw_lot`
- `rounded_lot`
- `clamped_flag`
- `size_reason`

## rounding方針（固定）
- 初期は `floor` 固定。
- 理由は指定リスクを超えないため。
- `round` / `ceil` は非対応。

## clamp方針（固定）
- `raw_lot` / `rounded_lot` が `max_lot` を超える場合は `max_lot` に clamp 可。
- `rounded_lot < min_lot` の場合は `min_lot` へ引き上げず invalid。
- 理由は `min_lot` へ引き上げると指定リスクを超える可能性があるため。

## invalid条件（固定）
- `account_balance <= 0`
- `risk_per_trade <= 0`
- `risk_per_trade >= 1`
- `stop_loss_distance_pips <= 0`
- `pip_value_per_lot <= 0`
- `lot_step <= 0`
- `min_lot <= 0`
- `max_lot <= 0`
- `min_lot > max_lot`
- bool / NaN / inf
- `rounded_lot < min_lot`

## 非対応範囲（固定）
- `PipelineAdapter` 接続
- `PositionSizer` 置換
- backtest PnL 変更
- trade_count 変更
- OANDA/API
- broker別厳密制約
- 通貨ペア別pip価値自動計算
- 収益性評価
- 売買ロジック変更

## 接続判断の扱い
- `PipelineAdapter` 接続は後続判断のまま維持する。
- `Lot Sizing v1` 初期完了は isolated calculator + unit test で判定する。

## 次実装へ渡す最小方針
- isolated calculator を新規追加する。
- 上記 formula/config/invalid/rounding/clamp を unit test で固定する。
- `PipelineAdapter` / `BacktestRunner` / `PositionSizer` 本線は変更しない。
