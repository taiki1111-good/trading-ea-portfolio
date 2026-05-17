# 2026-05-02 htf filter v1 spec

## 目的
- HTFContext本格導入比較に向けて、HTF filter v1 の仕様・比較条件・ログ列最小案を文書化する。

## v1仕様（確定方針）
- H1 only + direction alignment のみを対象とする。
- H4利用は v1対象外（次段階候補）。
- support/resistance 判定は v1対象外（次段階候補）。
- `simple_trailing_after_1R` は本採用ではなく experimental exit candidate のまま扱う。

## 比較条件
- HTF OFF + fixed
- HTF OFF + trailing
- HTF ON(H1 only, neutral permissive) + fixed
- HTF ON(H1 only, neutral permissive) + trailing
- HTF ON(H1 only, neutral strict) + fixed
- HTF ON(H1 only, neutral strict) + trailing

## 追跡・評価
- trade_count 減少だけで判断せず、除外entry理由を追跡する。
- decision_logs のHTF追跡列最小候補を docs へ反映（実装は次工程）。

## 前提
- 構造検証フェーズであり、収益性確認ではない。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
- 実 broker / OANDA API / 実注文送信は未実装。
