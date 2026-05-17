# 2026-05-02 HTF v1 April Neutral Permissive Diagnostic

## 概要
- 目的: HTF filter v1 の 2024-04 単月観察を、Q1/Q2 全月比較前の比較設計上の注意として記録する。
- 位置づけ: 構造検証。収益性確認ではない。
- 前提維持:
  - spread=0.2 pips fallback
  - 手数料・スリッページ・スワップ未反映
  - 実 broker / OANDA API / 実注文送信は未実装
  - HTF filter v1 は H1 only + direction alignment only
  - `simple_trailing_after_1R` は本採用ではなく experimental exit candidate

## 観察（2024-04 単月, fixed_sl_tp）
- HTF OFF: `trade_count=80`
- HTF ON strict: `trade_count=80`（OFF と entry 集合一致）
- HTF ON permissive: `trade_count=84`
- permissive only の 9 件は、すべて `htf_bias=neutral` かつ `htf_neutral_policy=permissive` 通過由来
- permissive only の一部は OFF 側 entry に対して 5 分前倒しで発生
- 差し引きで permissive は `+4 trades`

## 比較設計への反映
- `HTF filter ON/OFF` だけではなく `HTF alignment policy comparison` として比較する。
- `trade_count` だけで判断しない。
- 最低限の比較軸:
  - entry 集合差分（共通 / only）
  - entry 時刻前倒し有無
  - `neutral_passed_count` / `neutral_rejected_count`

## 実行方針メモ
- 重い backtest 実行はユーザーがローカル PowerShell で行う。
- Codex は実行コマンド整理、実行後のログ読取手順整理、比較表作成手順整理を担当する。

## 未解決
- Q1/Q2 全月・6条件で同様傾向が再現するかは未確認（別タスク）。
- entry 集合差分の自動集計を比較表へ標準化する実装は未着手。
