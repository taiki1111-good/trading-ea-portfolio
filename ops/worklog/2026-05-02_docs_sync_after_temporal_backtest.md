# 2026-05-02 docs sync after temporal backtest

## 目的
- BacktestRunner / PipelineAdapter / temporal third_wave_break / dedup 制御 / 短期実データBT の進捗を README・docs・ops に反映。
- 実装済み項目と TODO 記述の不整合を解消。

## 実施内容
- README の現在段階を更新し、BacktestRunner・PipelineAdapter・temporal・dedup・短期BT比較を反映。
- CURRENT_TASKS を更新し、完了済みTODOを整理。次タスクを再現性確認とログ整備へ移動。
- docs/17 の 14章を更新し、PipelineAdapter 実装済み・decision_logs 未本格を明記。
- docs/04 に detector_chain_temporal の責務境界（LTF部品責務と分離）を追記。
- docs/07 に temporal third_wave_break の追加テスト観点を追記。
- docs/10 に backtest trade_logs の必須/条件付き項目を追記。
- backtest_runner.py の docstring を現状に合わせて更新（ロジック変更なし）。

## 注意
- 実 broker / OANDA API / 実注文送信は未実装のまま。
- 収益性評価済みとは扱わない。
- spread=0.2 pips fallback 前提、手数料・スリッページ・スワップ未反映。
