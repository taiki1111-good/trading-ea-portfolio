# 2026-05-15 lot sizing v1 pipeline connection decision

## 目的
- `Lot Sizing v1` calculator を `PipelineAdapter` / `PositionSizer` 本線へ接続するかを判断し、次の安全な進め方を固定する。
- 今回は docs/ops 判断固定のみで、コード変更・テスト変更は行わない。

## 最終判断
- 本線への即時接続は **No-Go / Hold** とする。
- 次フェーズは shadow mode / comparison-only 設計判断へ進める。

## No-Go 理由
1. `fixed_lot` baseline を壊す可能性がある。
2. PnL / trade_count / risk logs の解釈が変化する。
3. `pip_value_per_lot` が手入力前提であり、入力前提差異の影響が大きい。
4. broker別制約厳密化、OANDA/API、実運用要件は未対応。
5. 収益性評価へ論点が広がりやすい。

## 固定方針
- 本線は `fixed_lot` を維持する。
- risk-based lot は診断値として算出・比較する候補に留める。
- PnL / trade_count / entry/exit 判断には影響させない。

## shadow mode / comparison-only 候補
- `fixed_lot`
- `risk_based_raw_lot`
- `risk_based_rounded_lot`
- `risk_based_effective_lot`
- `lot_sizing_reason`
- `clamped_flag`
- `lot_size_diff`

## shadow mode でも非対応
- PnL反映
- trade_count変更
- entry/exit判断変更
- broker制約厳密化
- OANDA/API接続
- 実注文

## Go 条件（接続判断を進める前提）
1. risk-based lot が fixed_lot 比較ログで安定している。
2. invalid / clamp / below_min がログで把握できる。
3. `pip_value_per_lot` 前提が明確である。
4. PnL非反映の診断モードが用意できる。
5. representative fixture で既存 trade_count / PnL が不変である。

## No-Go 条件（継続）
- 本線lotを置換しないと検証できない。
- PnLやtrade_countが変わる。
- broker/OANDA仕様が必要になる。
- pip_value自動計算が必須になる。
- 収益性評価へ論点が広がる。

## 次に渡す設計タスク
- `Lot Sizing v1` shadow mode / comparison-only の I/O、記録列、実行モード境界を docs/ops で固定する。
