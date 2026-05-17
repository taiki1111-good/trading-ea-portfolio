# 2026-05-02 htf filter v1 interface spec

## 目的
- HTF filter v1 実装前に、設定インターフェース・判定優先順位・decision_logs最小列を確定する。

## 確定仕様
- v1対象: H1 only + direction alignment only
- v1対象外: H4判定、support/resistance 判定
- config:
  - `htf_filter_enabled: bool`
  - `htf_timeframe_policy: H1_only`
  - `htf_neutral_policy: permissive | strict`
- 既定動作:
  - `htf_filter_enabled=false`（既存互換維持）
  - HTF filter ON は明示フラグ時のみ有効
- 判定優先:
  - `htf_bias` 主判定
  - `htf_trend_dir` は補助ログ
  - `htf_bias` 欠損/判定不能時のみ `htf_trend_dir` 暫定fallbackを許容し、理由を `htf_filter_reason` に記録

## decision_logs 最小列（実装前固定）
- `htf_filter_enabled`
- `htf_timeframe_policy`
- `htf_neutral_policy`
- `htf_bias`
- `htf_trend_dir`
- `htf_direction_aligned`
- `htf_filter_reason`
- `htf_context_reason`

## メモ
- 本件は構造検証フェーズの仕様整理であり、収益性確認ではない。
- `simple_trailing_after_1R` は本採用ではなく experimental exit candidate のまま。
