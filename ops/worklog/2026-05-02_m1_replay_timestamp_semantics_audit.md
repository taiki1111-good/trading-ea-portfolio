# 2026-05-02 M1 Replay Timestamp Semantics Audit

## 目的
- M5 trade_logs の `entry_time` semantics と M1 replay 開始時刻のズレを監査し、
  M1 replay に時刻補正オプションを追加する。

## 監査結果（要点）
- `make_m5_backtest_slice_from_dat.py` は `timestamp=floor(5min)` のため、M5 timestamp は bar open time。
- BacktestRunner は「現在バー close で entry」モデル。
- 現状 trade_logs の `entry_time` は decision bar timestamp と解釈され、約定有効時刻とは区別が必要。

## 実装
- `scripts/replay_counterfactual_exits_m1.py`
  - `--entry-time-mode {bar_timestamp,m5_close}`
  - `--entry-timeframe-minutes` を追加
  - `m5_close` 時は `entry_effective_time = entry_time + timeframe` を使用
- 比較集計 `scripts/compare_m1_exit_replay_results.py` に `entry_time_mode` 出力を追加

## docs更新
- `docs/17_backtest_design.md` に timestamp semantics 節を追加
- `docs/10_interface_contract.md` に trade_logs 時刻列 semantics を追加

## 注意
- spread=0.2 pips fallback 前提
- 手数料・スリッページ・スワップ未反映
- 収益性評価ではなく構造検証
