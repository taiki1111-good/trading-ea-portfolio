# 2026-05-03 HTFContext v0.2 diagnostic_only implementation

## 実装概要
- `PipelineAdapter` に HTF v2 `diagnostic_only` の最小実装を追加。
- H4 bias / H1 context を M5 window から集約計算し、decision trace へ出力。
- `htf_v2_enabled=False` を既定値とし、既存挙動を維持。

## 重要挙動
- `htf_v2_enabled=True` かつ `htf_v2_policy=diagnostic_only` でも entry を止めない。
- `entry_signal` / `trade_ok` は変更しない。
- `htf_v2_filter_reason` は `diagnostic_only:no_entry_filter` を記録。

## 追加した主な要素
- Config:
  - `htf_v2_enabled`
  - `htf_v2_policy`
  - `htf_v2_h4_ma_fast`
  - `htf_v2_h4_ma_slow`
  - `htf_v2_h1_ma_fast`
  - `htf_v2_slope_window`
- HTF v2 trace列:
  - `h4_bias` / `h1_context` / MA値 / slope / `htf_v2_conflict_flag` / `htf_v2_data_valid_flag` ほか

## future leak 方針
- `m5_decision_time = m5_timestamp + 5min`
- `htf_bar_close_time <= m5_decision_time` の HTF bar のみ参照
- 未確定 H1/H4 は使用しない

## テスト
- `diagnostic_only` で entry 非変更を確認
- H4/H1 判定（up/down/neutral/unknown, aligned/pullback/unknown）を確認
- 未確定 HTF 不参照と必要本数不足時 `unknown` / `data_valid=false` を確認
- decision trace に HTF v2 列が含まれることを確認

## 未解決事項
- `transition` context 判定は deferred（条件定義が未確定）
- `aligned_only` / `pullback_permissive` の本体反映判断は後続

## 注意
- これは収益性確認ではない。
- HTF v2 本採用を意味しない。
