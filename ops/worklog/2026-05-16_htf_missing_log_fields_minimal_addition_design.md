# 2026-05-16 htf missing log fields minimal addition design

## 設計目的
- HTF diagnostic comparison（strict/permissive 比較）に必要な情報を、既存ログ互換を壊さず最小追加で露出できるようにする。
- `PipelineAdapter` 内部traceに既に存在するHTF項目を、near_live/backtest decision_logsで再利用可能にする設計を固定する。
- 今回は設計のみであり、コード変更・テスト変更は行わない。

## 追加対象ログ
- 第1優先:
  - `near_live_decision_logs.csv`（pipeline dry-run出力）
- 後続確認対象:
  - backtest 側 `decision_logs.csv`
- 方針:
  - 最終的に near_live / backtest で比較可能な列名へ寄せる。

## 行レベルに追加する最小列（固定候補）
- `htf_filter_enabled`
- `htf_timeframe_policy`
- `htf_neutral_policy`
- `htf_trend_dir`
- `htf_bias`
- `htf_direction_aligned`
- `htf_filter_reason`
- `htf_context_reason`

## summary側で集計する項目（候補）
- `neutral_passed_count`
- `neutral_rejected_count`
- `htf_filter_rejected_count`
- `htf_filter_rejected_by_reason`
- `htf_against_entry_count`

## near_live / backtest の扱い
- near_live:
  - まず上記8列を最小追加候補として扱う。
  - strict/permissive 比較に必要な行レベル根拠を確保する。
- backtest:
  - 同等列を出力可能かを後続確認する。
  - 既存 `decision_logs` のtrace互換を見ながら段階適用する。
- 共通方針:
  - near_live/backtest で同名列へ寄せ、比較時の変換コストを下げる。

## 既存列との互換方針
- 既存 `filter_reason` は削除・改名しない。
- `htf_filter_reason` は HTF専用の独立列として追加候補にする。
- `decision_reason` は自由文扱いを維持し、構造化集計の主軸にしない。
- 追加列は additive とし、既存CSV互換を壊さない。
- 既存分析スクリプトが既存列前提でも破綻しないよう、列追加のみで対応する。

## 非対応範囲
- コード変更
- テスト変更
- HTF filter本体実装
- HTF filter ON化
- strict/permissive comparison runner 実装
- PnL / trade_count / entry / exit / `trade_ok` に影響する変更
- OANDA/API
- 実注文
- 収益性確認済みの主張

## Go条件
1. 行レベル最小8列が near_live decision logs へ additive で追加できる設計になっている。
2. summary候補5項目を、既存列破壊なしで集計可能な見通しがある。
3. strict/permissive 比較に必要な「neutral通過/拒否」「HTF拒否理由」を構造化して扱える。
4. near_live/backtest の列名整合方針が明記されている。

## No-Go条件
- 既存列の削除/改名を前提にしないと進めない。
- `decision_reason` 自由文だけに依存した比較設計になる。
- HTF列追加と同時に本体filter ONや比較runner実装まで拡大する。
- PnL/trade_count へ影響する変更を含めないと成立しない設計になる。

## 次に進む判断
- 次フェーズは以下のいずれかを後続判断とする。
1. 最小ログ列追加の実装判断へ進む（additive列追加のみを対象）。
2. 実装前に HTF diagnostic comparison 設計（strict/permissive比較条件と評価フロー）を先に固定する。
