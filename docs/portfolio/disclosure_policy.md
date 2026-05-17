# Disclosure Policy

## 1. 目的
この文書は、`trading-ea` を外部向けポートフォリオとして説明する際に、実装済み・検証済み・未実装の範囲を分けて伝えるための方針を整理する。

本プロジェクトは、設計・検証・説明可能性を重視した研究/検証用EAフレームワークである。実際の取引システムとの接続や注文送信機能は実装しておらず、収益性の確認を主張しない。

## 2. 外部説明の中心にするもの
- アーキテクチャ
- モジュール責務
- I/O 契約の考え方
- ログ設計
- dry-run（実注文を行わない検証実行）/ backtest の検証方針
- future leak 防止の考え方
- no-real-order integrity（実注文が発生していないことの整合確認）の確認方針
- テスト方針
- main と experiments の分離方針
- 未実装範囲
- 研究・検証用フレームワークとしての到達点

## 3. 外部説明の中心にしないもの
- 細かい売買パラメータ
- entry / exit の具体条件詳細
- 実データ本体
- 収益性を強く示すグラフ
- 未検証の成績数値
- 過去データの期間や条件に強く依存する比較結果
- 本採用前の experimental candidate を完成済みの戦略のように見せる説明

## 4. 表現方針
外部説明では、強い成果表現だけを先に出さず、到達点と未実装範囲を同じ文脈で説明する。

避ける表現の例:
- 運用準備が完了しているように見える表現
- 収益性を確認したように見える表現
- 注文送信機能まで対応しているように見える表現
- 取引システム接続済み
- risk-based lot 本体接続済み
- HTF filter採用済み
- 株式対応済み
- AI自動売買完成
- live ready
- demo operation ready

推奨する説明:
- 研究・検証用EAフレームワーク
- 構造検証段階
- CSV replay pipeline dry-run の representative run を確認済み
- dry-run health と no-real-order integrity を確認
- 収益性確認や注文送信機能は対象外
- 株式対応は future extension policy の整理のみ
- experiments は本体未採用の検証候補

## 5. 注意する説明
`dry_run_health_status=pass` は、ログ整合、gap分類、no-real-order integrity などの dry-run health を示す。収益性、実運用品質、取引システム接続準備完了を意味しない。

Risk/Stop v0 は、`trade_ok`、lot、SL/TP、理由ログの最小契約を確認するための段階である。lot sizing 本体や資金管理最適化を意味しない。

`docs/18_asset_class_extension_policy.md` は将来の資産クラス拡張方針であり、株式対応の実装や検証を意味しない。
