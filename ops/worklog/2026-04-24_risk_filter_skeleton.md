# 2026-04-24 RiskFilter Skeleton Implementation

## 1. 目的
RiskFilter モジュールを最小ロジック付き骨組みとして実装し、Signal -> RiskFilter の境界契約を確認する。Execution / Logger / Evaluator の本実装には入らない。

## 2. 実装内容
- `src/risk_filter/types.py`
  - RiskFilter の最小 dataclass / config / result型を定義
  - `trade_ok`, `lot`, `stop_loss`, `take_profit`, `risk_reason`, `filter_reason`, `event_risk_flag`, `spread_ok`, `limit_ok`, `max_trade_reached_flag`, `sub_reasons` を含む
- `src/risk_filter/event_filter.py`
  - `event_flag` をそのまま `event_risk_flag` に反映する最小ロジックを実装
  - 外部ニュースAPI などには依存しない
- `src/risk_filter/spread_filter.py`
  - `spread <= max_spread_pips` を許容し、`spread < 0` を不正として拒否
- `src/risk_filter/trade_limit_filter.py`
  - `daily_trade_count >= max_daily_trades` または `losing_streak >= max_losing_streak` で拒否する判定のみを実装
- `src/risk_filter/position_sizer.py`
  - 固定 lot 返却の最小ロジックを実装
- `src/risk_filter/stop_loss_planner.py`
  - `signal_type` に応じて固定距離の stop_loss を raw price で返却
- `src/risk_filter/take_profit_planner.py`
  - `signal_type` に応じて固定距離の take_profit を raw price で返却
- `src/risk_filter/assembler.py`
  - Signal 出力と下位部品結果を統合し、`trade_ok` / `lot` / `stop_loss` / `take_profit` / `risk_reason` / `filter_reason` を返す
  - `trade_ok=true` の場合にのみ lot/stop_loss/take_profit を維持する設計にした

## 3. 結果
- RiskFilter の下位部品責務を分離して実装
- Signal -> RiskFilter の最小 integration test で long / short entry の正常パスと停止条件を確認
- `pytest -q` で全件通過
  - `97 passed in 0.26s`

## 4. 保留 / TODO
- TODO(TBD): RiskFilter の本格資金管理、ATR ベース SL/TP を別フェーズで追加
- TODO(TBD): `signal_type=exit` を RiskFilter でどのように扱うかは次フェーズで明文化
- TODO(TBD): 外部イベント種別の詳細判定は EventFilter の将来拡張候補として分離

## 5. 横断レビュー観点（確認済み）
- Signal -> RiskFilter 契約と一致している
- RiskFilter -> Execution 契約を先取りしすぎていない
- `trade_ok=false` の理由が `filter_reason` に残る
- `trade_ok=true` のとき `lot / stop_loss / take_profit` が有効値になる
- `spread` は pips 単位
- `event_flag` は価格方向判断ではなく停止判定専用
- 本格資金管理 / ATR / broker 制約には踏み込んでいない
