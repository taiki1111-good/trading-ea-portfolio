# アーキテクチャ概要

## システム全体図

```text
Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator
```

## 8つの上位モジュール構成

### 1. Data
- 役割: 価格データやイベント時刻データを読み込み、後段で使える形に整える

### 2. HTFContext
- 役割: 上位足を用いてトレンド方向、抵抗・支持、余地を判定する

### 3. LTFStructure
- 役割: 執行足を用いて波動、ブレイク、パターンなどの構造を判定する

### 4. Signal
- 役割: HTFContext と LTFStructure を統合し、売買候補を判定する

### 5. RiskFilter
- 役割: 取引可否、停止条件、lot、損切り、利確を決定する

### 6. Execution
- 役割: 注文実行、約定管理、状態更新を担当する
- 現状: dry-run / skeleton 中心（実注文・broker接続は未実装）

### 7. Logger
- 役割: 判断理由、状態遷移、注文結果、損益を記録する

### 8. Evaluator
- 役割: ログや結果をもとに成績評価と改善対象の整理を行う

## 実装順序
上流から下流へ順序立てて実装する。

1. Data
2. HTFContext
3. LTFStructure
4. Signal
5. RiskFilter
6. Execution
7. Logger
8. Evaluator

## 設計のポイント
- 上位足環境認識と執行足構造認識を分離する
- 状態管理を明示し、危険な遷移を避ける
- 理由を残せる設計にして、後から追跡しやすくする
- 新しい裁量パターンは experiments 領域で比較し、本体へ直接混ぜない

## 補足
この文書は外部説明用の要約であり、正式なアーキテクチャ定義は `docs/03_architecture.md` と `docs/04_module_spec.md` を参照する。
収益性評価や実運用可能性を主張する文書ではない。
