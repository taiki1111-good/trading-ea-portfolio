# 18_asset_class_extension_policy

## 1. 目的
- 現行EAをFX専用実装に閉じ込めず、将来的に株式などへ拡張できるようにする方針を整理する。
- 現時点では株式対応を実装しない。
- 作り直しを避けるため、Core Framework と Asset Adapter の分離方針を残す。

## 2. 基本方針
- Core Framework は市場非依存に保つ。
- FX固有仕様は FX Adapter に閉じ込める。
- 株式固有仕様は将来 Equity Adapter として追加する。
- 既存のFX用backtestやData方針は壊さない。
- asset class ごとのデータ・単位・市場制度・約定前提は混在させない。

## 3. 想定する階層構造
本章は将来拡張時の概念構成を示す。現時点で実装済みを意味しない。

Core Framework:
- Data Contract
- Feature Contract
- HTFContext
- LTFStructure
- Signal
- RiskFilter
- Execution / Simulation
- Logger
- Evaluator

FX Adapter:
- FXDataLoader
- PipUnitPolicy
- SpreadPolicy
- EconomicEventPolicy
- FXExecutionPolicy

Equity Adapter:
- EquityOHLCVLoader
- MarginBalanceLoader
- OrderBookLoader
- TimeAndSalesLoader
- CorporateActionAdjuster
- EquitySessionCalendar
- EquityLiquidityFeatureBuilder
- EquityExecutionPolicy

## 4. Coreに残すべきもの
- 時系列データをfuture leakなしで処理する方針
- モジュール間I/O契約
- 理由ログ
- state_logs / trade_logs / decision_logs / event_logs の分離
- Evaluatorによる比較・検証
- 構造検証と収益性確認を分ける方針
- experiments と main の境界

## 5. Asset Adapterに閉じ込めるべきもの
FX固有:
- pips
- lot
- spread pips
- bid/ask再構成
- 経済指標イベント
- 24時間に近い市場時間
- FX broker前提

株式固有:
- tick size
- 呼値
- 株数
- 単元株
- 市場セッション
- 寄り付き / 前引け / 後場 / 大引け
- 出来高
- 売買代金
- 信用残
- 板
- 歩み値
- 決算
- 適時開示
- 分割・併合・配当調整
- ストップ高 / ストップ安
- 空売り規制
- 流動性制約

## 6. 株式拡張時に追加候補となるFeature群
以下は将来候補であり、実装済み・検証済みを意味しない。

Price / Volume:
- volume
- turnover
- vwap
- gap_ratio
- range_atr_norm

Liquidity:
- bid_ask_spread
- spread_ratio
- best_bid
- best_ask
- bid_size
- ask_size
- order_book_imbalance
- depth_imbalance

Time and Sales:
- trade_price
- trade_size
- aggressor_side
- large_trade_flag
- buy_sell_pressure

Margin / Supply-Demand:
- margin_buy_balance
- margin_sell_balance
- short_interest
- margin_balance_change
- borrow_pressure

Market Context:
- index_trend
- sector_trend
- market_breadth
- relative_strength
- liquidity_state

Corporate / Event:
- earnings_event_flag
- disclosure_event_flag
- corporate_action_adjusted_flag
- event_severity

## 7. 既存モジュールとの対応
本章は現在のモジュール責務を維持したまま、株式拡張時の解釈余地を示す。

Data:
- OHLCV、信用残、板、歩み値、イベント、コーポレートアクションを扱う将来余地を持つ。

HTFContext:
- 日足・週足・指数・セクター・地合いを扱う将来余地を持つ。

LTFStructure:
- ブレイク、押し目、三角持ち合い、ギャップ後の構造などに拡張可能。

Signal:
- チャート構造、出来高、流動性、信用需給、板・歩み値由来特徴量を統合する将来余地を持つ。

RiskFilter:
- 板薄、流動性不足、決算前、急騰直後、信用過熱、寄り直後などを停止条件として扱う将来余地を持つ。

Execution:
- 成行、指値、寄成、引成、約定難易度、スリッページ、部分約定などを扱う将来余地を持つ。

Logger:
- チャート理由だけでなく、出来高・板・信用残・歩み値に基づく判断理由を残す将来余地を持つ。

Evaluator:
- 銘柄別、セクター別、流動性別、地合い別、イベント有無別の評価に拡張できる余地を持つ。

## 8. 作り直しを避けるための禁止事項
- FXのpips前提をCoreに固定する
- lotを株数として曖昧に流用する
- spreadをFXと株式で同じ意味として扱う
- 株式固有特徴量をSignalへ直接無秩序に渡す
- USDJPY専用DataFrameに株式列を雑に継ぎ足す
- 株式対応をmainロジックに混ぜる
- asset_classごとの単位・市場時間・約定前提を区別しない
- volumeや板情報を単なる任意列として扱い、意味契約を定義しない

## 9. 現時点でやらないこと
- 株式用DataLoaderの実装
- 株式用backtestの実装
- 板・歩み値の取得処理
- 信用残データの取得処理
- 株式用Signalの実装
- 株式用Executionの実装
- 実broker接続
- 収益性評価
- 銘柄選定モデル
- ML/HMM/LSTM等の実装

## 10. 将来の導入順序案
本章は実装計画ではなく、将来の整理順序案である。

Phase A:
- AssetClass policy の文書化
- 共通Data ContractとFX固有Data Contractの分離方針整理

Phase B:
- Equity data acceptance policy の追加
- OHLCV / corporate action / session calendar の受け入れ基準整理

Phase C:
- Equity Feature Contract の追加
- volume, liquidity, margin balance, order book, time and sales の特徴量契約整理

Phase D:
- Equity Backtest assumptions の追加
- 株式の約定モデル、手数料、スリッページ、寄り付き/大引けの扱いを整理

Phase E:
- Equity Adapter の実装検討
- ただし、現時点では実装対象外

## 11. 既存docsとの関係
- `docs/03_architecture.md` の責務分離方針に従う。
- `docs/04_module_spec.md` のモジュール契約方針に従う。
- `docs/05_variable_spec.md` の変数契約方針と整合させる。
- `docs/10_interface_contract.md` の境界契約を壊さない。
- `docs/11_data_source_policy.md` は現状FX/Dukascopy中心であり、株式用には将来別ポリシーが必要。
- `docs/17_backtest_design.md` のfuture leak防止・構造検証方針は株式にも継承する。
