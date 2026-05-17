# 2026-05-02 htfcontext comparison design

## 目的
- HTFContext本格導入比較の評価設計を文書化し、entry課題とexit課題を分離して検証する準備を整える。

## 設計整理（要点）
- 比較は本体既定動作へ直結せず、experimental comparison として扱う。
- 最低限の比較軸は 2x2（HTF OFF/ON × fixed/trailing）。
- `simple_trailing_after_1R` は本採用ではなく experimental exit candidate のまま維持する。
- HTF ON の初期定義は direction alignment 中心、support/resistance は段階導入または別比較に分離。
- `neutral` 扱い（strict/permissive/comparison）と H1/H4 方針（H1 only/H4 only/H1&H4/H4+H1）は未確定事項として明示。
- future leak 防止として、M5時点で確定済みHTFバーのみ参照する。
- M5 timestamp=bar open、entry=M5 close の整合確認を比較観点に含める。
- 評価指標と decision_logs のHTF追跡列候補を docs に列挙（今回は実装しない）。

## 前提再確認
- 構造検証フェーズであり、収益性確認ではない。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
- 実 broker / OANDA API / 実注文送信は未実装。
