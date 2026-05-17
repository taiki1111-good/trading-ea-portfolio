# 2026-05-16 htf diagnostic comparison design

## 設計目的
- HTF filter v1 の strict/permissive 比較を、実装前に「比較条件・入力列・評価指標・手順」で固定する。
- 売買ロジック追加ではなく、HTF判断を説明可能な比較実験として扱うための設計を明文化する。
- 今回は設計のみであり、HTF filter 本体実装・ON化・comparison runner 実装は行わない。

## 比較対象
- 同一入力期間
- 同一 entry 候補生成条件
- 同一 exit policy
- 差分は HTF 条件のみ
- 補足:
  - 現段階は設計固定のみ（実行実装は後続）

## 比較条件（最小）
1. HTF OFF
2. HTF ON + H1 only + neutral permissive
3. HTF ON + H1 only + neutral strict

## 入力ログ
- 主入力:
  - `near_live_decision_logs.csv`
- 参照補助（後続候補）:
  - backtest / trade_logs 系（PnL系指標を扱う場合）

## 必須列（near_live decision logs）
- `timestamp`
- `entry_signal`
- `trade_ok`
- `signal_type`
- `htf_filter_enabled`
- `htf_timeframe_policy`
- `htf_neutral_policy`
- `htf_trend_dir`
- `htf_bias`
- `htf_direction_aligned`
- `htf_filter_reason`
- `htf_context_reason`
- `filter_reason`
- `decision_reason`

## 評価指標
### near_live 単体で扱える指標
- `trade_count`（比較時は run summary との整合前提）
- `entry_signal_true_count`
- `trade_ok_true_count`
- `entry集合差分`
- `htf_filter_rejected_count`
- `htf_filter_rejected_by_reason`
- `neutral_passed_count`
- `neutral_rejected_count`
- `htf_direction_aligned count`
- `htf_against_entry count`
- 月別比較
- Q1/Q2比較

### near_live 単体では未確定（別ログ接続が必要）
- `win_rate`
- `average_pnl`
- `total_pnl`
- `exit_reason counts`

補足:
- 上記PnL系は backtest/trade_logs との接続が必要であり、near_live 単体では確定指標として扱わない。

## 実行フロー案
1. near_live ログで HTF 列の存在と reason 分布を確認する。
2. OFF / permissive / strict の比較条件を固定する。
3. comparison runner または analysis script の最小設計へ進む。
4. 代表期間で比較を実施する。
5. 月別 / Q1-Q2 比較へ拡張する。
6. 本体filter化判断はさらに後続で扱う。

## Go条件
1. 3条件（OFF/permissive/strict）が同一入力・同一exit前提で比較可能。
2. 必須列が比較ログに安定して出力される。
3. `entry集合差分` と rejected理由を構造化して説明できる。
4. near_live単体で扱える指標と、別ログ接続が必要な指標が分離されている。
5. 本体filter化判断を急がず、比較結果の解釈手順が先に固定されている。

## No-Go条件
- 条件差分がHTF以外（entry/exit/他filter）に混入する。
- `decision_reason` 自由文だけで比較し、構造化指標が不足する。
- PnL系を near_live 単体で確定扱いする。
- comparison設計なしで本体ON判断へ進む。
- 収益性確認済みのような扱いに論点が拡散する。

## 今回の非対応範囲
- コード変更
- テスト変更
- HTF filter本体実装
- HTF filter ON化
- comparison runner実装
- summary候補5項目の実装
- backtest decision_logs 側の同等列追加
- PnL / trade_count / entry / exit / `trade_ok` に影響する変更
- OANDA/API
- 実注文
- 収益性確認済みの主張

## 次に進む判断
- 次フェーズは、HTF diagnostic comparison runner/analysis script の最小実装判断へ進む。
- その際は「まず near_live 単体指標を固定し、PnL系は別ログ接続フェーズで扱う」順序を維持する。
