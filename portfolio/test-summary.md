# テスト計画概要

## テスト戦略
各モジュールの実装段階ごとにテストを挟み、下位部品の正しさと隣接モジュールとの接続を確認する。
加えて、dry-run / diagnostic / shadow comparison の出力整合を確認し、判断過程の説明可能性を担保する。

## テストレベル別の実施内容

### 1. 下位部品単体テスト
各モジュールを構成する部品単位で、契約と責務を確認する。

主な例:
- Data の整合処理
- HTFContext の方向・余地判定
- LTFStructure の構造認識
- RiskFilter の停止条件判定
- Execution の状態遷移管理

### 2. 上位モジュール結合テスト
下位部品を組み上げた単位で、上位モジュールとしての出力整合を確認する。

### 3. モジュール間結合テスト
隣接する上位モジュール同士が正しく接続できるかを確認する。

検証対象:
- Data -> HTFContext
- Data -> LTFStructure
- HTFContext + LTFStructure -> Signal
- Signal -> RiskFilter
- RiskFilter -> Execution
- Execution -> Logger
- Logger -> Evaluator

### 4. 小規模な通し確認
一部のデータを用いて、上流から下流まで最低限流せるかを確認する。

### 4.1 dry-run / diagnostic / shadow comparison 確認
- CSV replay pipeline dry-run の representative run で no-real-order 整合を確認する
- HTF diagnostic comparison v0 で OFF/permissive/strict の差分を確認する
- lot sizing shadow comparison で fixed baseline と risk-based lot の差分を確認する（comparison-only）

### 5. 境界値確認
閾値の直前・直後で挙動が想定通りかを確認する。

例:
- spread 閾値
- 最大取引回数
- 連敗停止条件
- イベント停止窓

### 6. 状態遷移確認
- IDLE
- ENTRY_PENDING
- POSITION_OPEN
- EXIT_PENDING
- SUSPENDED
- ERROR

など各状態が正しく遷移するかを確認する。

## テスト実施スケジュール
- 各モジュール実装後、単体テストを実施
- 次のモジュール実装前に結合テストを実施
- 全モジュールの骨組み接続後に通し確認を実施
- ロジック追加時にシナリオテストと比較確認を追加する

## 補足
この文書は外部説明用の要約であり、正式なテスト方針は `docs/07_test_plan.md` を参照する。
収益性評価、実注文、OANDA/API 接続の確認を目的とした文書ではない。
