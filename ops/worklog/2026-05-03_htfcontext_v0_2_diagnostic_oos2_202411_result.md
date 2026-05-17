# 2026-05-03 HTFContext v0.2 diagnostic_only OOS-2 2024-11 result

## 概要
HTF v0.2 `diagnostic_only` 代表run（OOS-2 2024-11）結果を記録する。
本記録は結果整理と次設計課題の明文化が目的であり、収益性確認や本体統合判断を目的としない。

## 実行条件
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-10-01_2025-01-01.csv`
- run-id: `oos2_20241101_1201_htf_v2_diag_off_trailing`
- start: `2024-11-01`
- end: `2024-12-01`
- exit-policy: `simple_trailing_after_1R`
- `htf-v2-enabled`
- `htf-v2-policy diagnostic_only`

## 実行結果
- `selected_bars=5925`
- `range=[2024-11-01T00:00:00+00:00, 2024-11-29T16:55:00+00:00]`
- `trade_count=64`
- `total_pnl=0.29010000000004366`
- decision_logs に HTF v2 列が存在することを確認

## HTF v2 分布
- `h4_bias_counts`
  - `unknown=2456`
  - `down=1487`
  - `neutral=1419`
  - `up=499`
- `h1_context_counts`
  - `unknown=3117`
  - `range_or_neutral=1101`
  - `aligned_down=980`
  - `aligned_up=367`
  - `pullback_against_h4=296`

## 解釈（構造検証）
- `diagnostic_only` は entry を止めない前提であり、`trade_count=64` は既存 OOS-2 2024-11 OFF trailing と一致した。
- 代表runでは entry 非変更を概ね確認できた。
- 一方で `h4_bias unknown` 約42%、`h1_context unknown` 約53% と unknown 比率が高い。

## unknown 比率が高い原因候補
- runner が `start/end` スライス後の bars のみを `PipelineAdapter` に渡しており、`start` 以前の warmup 履歴が HTF v2 計算に使われていない可能性。
- H4 MA50 には最低 50 本の H4 足（約 200 時間）相当の履歴が必要であり、月初起点 run で序盤 `unknown` が増えうる。

## 次タスク（Phase 4 設計）
1. HTF v2 warmup handling 方針の設計。
2. start以前履歴を HTF 計算に使うか検討。
3. trade評価期間と indicator warmup期間の分離方針を整理。
4. warmup後の `h4_bias` / `h1_context` 分布を再確認。
5. `aligned_only` / `pullback_permissive` 判断は保留。

## 注意
- backtest再実行は本作業で実施していない。
- 売買ロジック変更・HTF filter有効化・閾値変更は実施していない。
- これは収益性確認ではない。
