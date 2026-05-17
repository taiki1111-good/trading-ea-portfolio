# 2026-05-15 portfolio v0.1 docs

## 目的
- Phase 9 CSV replay pipeline dry-run minimal completion と Risk/Stop v0 minimal implementation adopted の到達点を、外部向けポートフォリオ v0.1 として説明しやすくする。
- Source of Truth は既存 docs/ops に置き、portfolio 文書は外部説明用の要約に限定する。

## 変更内容
- `docs/09_presentation_notes.md` を現状の Phase 9 / Risk-Stop v0 に合わせて更新した。
- `docs/portfolio/portfolio_overview.md` を追加した。
- `docs/portfolio/architecture_for_portfolio.md` を追加した。
- `docs/portfolio/disclosure_policy.md` を追加した。
- `README.md` に研究・検証用EAフレームワークである旨と `docs/portfolio/` への導線を追加した。

## 非対応範囲
- 実装コード変更なし。
- 売買ロジック変更なし。
- 実 broker / OANDA API / 実注文送信なし。
- 収益性確認、lot sizing 本体、PipelineAdapter planner chain 正式接続、Session/SR/HTF filter化、株式対応実装なし。

## 確認
- markdown 見出し構造を確認した。
- README から `docs/portfolio/` の3ファイルへ辿れることを確認した。
- 変更範囲が docs/ops の文書更新に限定されていることを確認した。
