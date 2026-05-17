# 2026-05-16 htf filter v1 pre-implementation contract decision

## 目的
- Session / SR / HTF filter化の優先順位（HTF -> Session -> SR）に基づき、HTF filter v1 の実装前契約を固定する。
- 今回は契約整理のみを対象とし、HTF filter を本体ONにしない。

## v1 の対象範囲
- 初期対象: **H1 only**
- 後続候補:
  - H4 統合
  - SR 判定との統合
  - Session filter との統合

## ON/OFF の既定方針
- 既定値は `htf_filter_enabled=false` とする。
- 明示フラグ指定時のみ ON とする。
- 既存 backtest / dry-run の互換性を壊さない。

## neutral policy（v1契約）
- `permissive`: neutral は通す。
- `strict`: neutral は見送る。
- 初回から片方を本採用に固定しない。
- strict / permissive は comparison 条件として併置し、比較可能性を優先する。

## entry方向ごとの通過 / 拒否条件
- long entry:
  - HTF up なら通す。
  - HTF down なら拒否。
  - HTF neutral は neutral policy に従う。
- short entry:
  - HTF down なら通す。
  - HTF up なら拒否。
  - HTF neutral は neutral policy に従う。

## 必要な最小ログ項目（候補）
- `htf_filter_enabled`
- `htf_timeframe_policy`
- `htf_neutral_policy`
- `htf_trend_dir`
- `htf_bias`
- `htf_direction_aligned`
- `htf_filter_reason`
- `neutral_passed_count`
- `neutral_rejected_count`
- `htf_filter_rejected_count`
- `htf_filter_rejected_by_reason`

## 評価指標
- `trade_count` 差分だけで判断しない。
- `entry集合差分`
- `rejected_count`
- `rejected_by_reason`
- `htf_direction_aligned count`
- `htf_against_entry count`
- `neutral_passed_count`
- `neutral_rejected_count`
- `win_rate`
- `average_pnl`
- `total_pnl`
- `exit_reason counts`
- 月別比較
- Q1/Q2比較

## Go条件
1. `htf_filter_enabled=false` 既定で既存互換を維持できる。
2. strict/permissive の比較条件が同一実行条件で再現可能。
3. `rejected_count` / `rejected_by_reason` / neutral通過・拒否が追跡可能。
4. `trade_count` 以外の指標（entry集合差分、pnl系、exit理由、月別/Q1Q2）で説明可能。
5. HTFの影響を Session/SR 統合なしで単独評価できる。

## No-Go条件
- trade_count差分のみで採用判断しようとしている。
- strict/permissive の比較条件が揃わない。
- `htf_filter_reason` や rejected理由が欠けて説明不能。
- H4/SR/Session を同時投入し、影響分解不能になる。
- 収益性確認済みのような扱いへ論点が拡散する。

## 今回の非対応範囲
- HTF filter 本体実装
- `PipelineAdapter` / `BacktestRunner` / `Signal` / `RiskFilter` / `Execution path` の変更
- 本体filter ON
- PnL / trade_count / entry / exit / `trade_ok` に影響する変更
- H4統合
- SR統合
- Session統合
- OANDA/API
- 実注文
- 収益性確認済みの主張

## 次に進む判断
- 次フェーズは以下のいずれかを後続判断とする。
1. HTF diagnosticログ確認を先行し、ログ項目の欠落/過不足を確定する。
2. HTF filter v1 diagnostic comparison 設計（strict/permissive比較条件と実行条件）を固定する。
