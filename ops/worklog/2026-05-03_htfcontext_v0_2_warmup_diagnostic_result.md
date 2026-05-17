# 2026-05-03 HTFContext v0.2 warmup diagnostic result

## 概要
OOS-2 2024-11 の HTF v2 `diagnostic_only` を warmupありで実行した代表run結果を記録する。
本記録は結果整理と次設計課題整理が目的であり、収益性確認や本体統合判断を目的としない。

## 実行条件
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-10-01_2025-01-01.csv`
- run-id: `oos2_20241101_1201_htf_v2_diag_off_trailing_warmup`
- output-dir: `logs/backtest_runs/oos2_20241101_1201_htf_v2_diag_off_trailing_warmup`
- start: `2024-11-01T00:00:00Z`
- end: `2024-12-01T00:00:00Z`
- warmup-start: `2024-10-01T00:00:00Z`
- exit-policy: `simple_trailing_after_1R`
- max-holding-bars: `50`
- `htf-v2-enabled`
- `htf-v2-policy: diagnostic_only`

## 実行結果
- `selected_bars=5925`
- `indicator_input_bars=12365`
- `warmup_bar_count=6440`
- `trade_count=64`
- `total_pnl=0.29010000000004366`
- `elapsed_seconds=459.08`

## metadata（抜粋）
- `warmup_start=2024-10-01T00:00:00Z`
- `evaluation_start=2024-11-01T00:00:00Z`
- `evaluation_end=2024-12-01T00:00:00Z`
- `evaluation_bar_count=5925`
- `indicator_input_start=2024-10-01T00:00:00+00:00`
- `indicator_input_end=2024-11-29T16:55:00+00:00`
- `htf_v2_enabled=true`
- `htf_v2_policy=diagnostic_only`

## warmupあり分布
- 全 decision row（`rows=5861`）
  - `h4_bias`: `neutral=2927`, `down=1725`, `up=1209`
  - `h1_context`: `range_or_neutral=2349`, `aligned_down=1087`, `unknown=1041`, `aligned_up=850`, `pullback_against_h4=534`
  - `htf_v2_data_valid_flag`: `True=4820`, `False=1041`
  - `htf_v2_conflict_flag`: `True=3924`, `False=1937`
- entry候補64件
  - `h4_bias`: `neutral=35`, `up=15`, `down=14`
  - `h1_context`: `range_or_neutral=25`, `unknown=14`, `aligned_up=14`, `aligned_down=6`, `pullback_against_h4=5`

## warmupなし/あり unknown 比率比較
- 全decision `h4_bias unknown`
  - warmupなし: `2456/5861 = 41.9%`
  - warmupあり: `0/5861 = 0.0%`
- 全decision `h1_context unknown`
  - warmupなし: `3117/5861 = 53.2%`
  - warmupあり: `1041/5861 = 17.8%`
- entry候補 `h4_bias unknown`
  - warmupなし: `27/64 = 42.2%`
  - warmupあり: `0/64 = 0.0%`
- entry候補 `h1_context unknown`
  - warmupなし: `36/64 = 56.3%`
  - warmupあり: `14/64 = 21.9%`

## 解釈（構造検証）
- warmup対応で H4 unknown はほぼ解消し、H1 unknown も大幅に改善した。
- 前回のunknown多発は warmup不足影響が大きい。
- `diagnostic_only` で `trade_count=64` / `total_pnl=0.2901` を維持し、entry非変更を再確認した。

## 次課題（semantics review）
1. `htf_v2_direction_allowed` の意味定義確認。
2. `htf_v2_conflict_flag` の意味定義確認。
3. `diagnostic_only` 時でも hypothetical allowed を出すべきか判断。
4. `neutral/range_or_neutral` を conflict扱いするか再整理。
5. `aligned_only` / `pullback_permissive` 判断は保留。

## 未解決事項
- `aligned_up` / `aligned_down` でも `htf_v2_direction_allowed=False` が見える行の意味整理。
- `neutral + range_or_neutral` で `conflict_flag=True` が多い理由と定義妥当性。

## 注意
- backtest再実行・HTF計算ロジック変更・PipelineAdapter変更・売買ロジック変更は行っていない。
- これは収益性確認ではない。
