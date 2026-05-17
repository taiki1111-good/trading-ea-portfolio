# 2026-05-03 Session v0.2 diagnostic trade analysis result

## 目的
- Session v2 diagnostic_only の代表run結果を記録し、実filter化の可否判断を整理する。
- backtest再実行や売買ロジック変更は行わず、既存ログ後処理結果の記録に限定する。

## 前提
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- Session v2 は diagnostic_only（entryは止めない）。
- `session_label` は UTC固定近似で DST厳密補正なし。
- `hour_utc` summary の `true/false` 混入問題は修正済み。

## 対象run
- `run_id`: `oos2_202411_session_v2_diag_trailing_matched`
- `trade_count`: `64`
- `total_pnl`: `0.29010000000004366`

## 集計結果
### session_label
- london: `trade_count=14`, `total_pnl=0.0653`, `average_pnl=0.0046642857`, `win_rate=0.857143`
- london_ny_overlap: `trade_count=11`, `total_pnl=0.0717`, `average_pnl=0.0065181818`, `win_rate=0.727273`
- low_liquidity: `trade_count=4`, `total_pnl=0.0101`, `average_pnl=0.002525`, `win_rate=0.75`
- new_york: `trade_count=9`, `total_pnl=0.0438`, `average_pnl=0.0048666667`, `win_rate=1.0`
- tokyo: `trade_count=26`, `total_pnl=0.0992`, `average_pnl=0.0038153846`, `win_rate=0.846154`

### session_risk_flag
- false: `trade_count=60`, `total_pnl=0.2800`, `average_pnl=0.0046666667`, `win_rate=0.85`
- true: `trade_count=4`, `total_pnl=0.0101`, `average_pnl=0.002525`, `win_rate=0.75`

### hour_utc（観測）
- 16時: `trade_count=7`, `total_pnl=0.0623`, `average_pnl=0.0089`, `win_rate=0.714286`
- 9時: `trade_count=4`, `total_pnl=0.0337`, `average_pnl=0.008425`, `win_rate=1.0`
- 8時: `trade_count=4`, `total_pnl=0.0285`, `average_pnl=0.007125`, `win_rate=1.0`
- 6時: `trade_count=3`, `total_pnl=-0.0018`, `average_pnl=-0.0006`, `win_rate=0.333333`
- 12時/14時: 各 `trade_count=1`, 各 `total_pnl=-0.0010`（件数不足）

### day_of_week
- friday: `trade_count=12`, `total_pnl=0.0904`, `average_pnl=0.0075333333`, `win_rate=0.75`
- monday: `trade_count=12`, `total_pnl=0.0686`, `average_pnl=0.0057166667`, `win_rate=0.916667`
- sunday: `trade_count=7`, `total_pnl=0.0351`, `average_pnl=0.0050142857`, `win_rate=1.0`
- thursday: `trade_count=10`, `total_pnl=0.0237`, `average_pnl=0.00237`, `win_rate=1.0`
- tuesday: `trade_count=11`, `total_pnl=0.0242`, `average_pnl=0.0022`, `win_rate=0.727273`
- wednesday: `trade_count=12`, `total_pnl=0.0481`, `average_pnl=0.0040083333`, `win_rate=0.75`

## 解釈
- session別では全体として全ラベルがプラスで、即時除外すべき時間帯は確認できない。
- `low_liquidity` と `session_risk_flag=true` は件数が少なく、悪化群とは断定できない。
- 一部 `hour_utc` に弱い値はあるが、件数不足で filter 化判断根拠としては不十分。
- day_of_week別も全曜日プラスで、代表月単独では時間制限導入の根拠が弱い。

## 判断
- 現時点では Session v2 を実filter化しない。
- Session v2 は `diagnostic/explanation layer` として継続する。
- 代表月単独で本採用/棄却判断を行わない。
- DST未補正のUTC固定近似ラベルのため、本採用filter検討前に再評価が必要。

## 未解決事項
- 複数月で同様傾向が再現するか。
- Session v2を先に深掘りするか、Phase 7 Risk managementへ進むか。
- DST厳密補正の導入タイミング。
- `low_liquidity` 定義の厳密化要否。

## 注意
- これは構造診断記録であり、収益性確認ではない。
