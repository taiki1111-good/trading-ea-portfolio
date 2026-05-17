# Disclosure Policy

## 1. 目的
この文書は、`trading-ea` を外部向けポートフォリオとして説明する際に、見せてよい範囲、見せすぎない範囲、禁止表現を整理する。

本プロジェクトは研究・検証用EAフレームワークであり、実運用EAや収益性確認済みシステムとして説明しない。

## 2. 外部に見せてよいもの
- アーキテクチャ
- モジュール責務
- I/O 契約の考え方
- ログ設計
- dry-run / backtest の検証方針
- future leak 防止の考え方
- no real order integrity の確認方針
- テスト方針
- main と experiments の分離方針
- 未実装範囲
- 研究・検証用フレームワークとしての到達点

## 3. 外部に見せすぎないもの
- 細かい売買パラメータ
- entry / exit の具体条件詳細
- 実データ本体
- 収益性を強く示すグラフ
- 未検証の成績数値
- 過去データの期間や条件に強く依存する比較結果
- 本採用前の experimental candidate を完成済みの戦略のように見せる説明

## 4. 禁止表現
以下の表現は使わない。

- 実運用可能
- 収益性確認済み
- OANDA対応済み
- 実注文対応済み
- risk-based lot 本体接続済み
- HTF filter採用済み
- 株式対応済み
- AI自動売買完成
- live ready
- demo operation ready
- broker接続済み

## 5. 推奨表現
以下のように、到達点と非対応範囲を同時に説明する。

- 研究・検証用EAフレームワーク
- 構造検証段階
- CSV replay pipeline dry-run の representative run を確認済み
- dry-run health と no real order integrity を確認
- 収益性確認や実注文接続は対象外
- 株式対応は future extension policy の整理のみ
- experiments は本体未採用の検証候補

## 6. 注意する説明
`dry_run_health_status=pass` は、ログ整合、gap分類、no real order integrity などの dry-run health を示す。収益性、実運用品質、broker接続準備完了を意味しない。

Risk/Stop v0 は、`trade_ok`、lot、SL/TP、理由ログの最小契約を確認するための段階である。lot sizing 本体や資金管理最適化を意味しない。

`docs/18_asset_class_extension_policy.md` は将来の資産クラス拡張方針であり、株式対応の実装や検証を意味しない。
