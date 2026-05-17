# 2026-04-24 Execution Skeleton Implementation

## 1. 目的
Execution モジュールを dry-run の最小骨組みとして実装し、RiskFilter -> Execution の境界を確認する。Logger / Evaluator の本実装には入らない。

## 2. 実装内容
- `src/execution/types.py`
  - Execution の最小 dataclass / enum 型を定義
  - `order_request`, `order_result`, `fill_price`, `execution_price`, `position_state`, `previous_state`, `next_state`, `execution_reason`, `transition_reason`, `broker_response_raw` を含む
- `src/execution/order_builder.py`
  - `trade_ok`, `signal_type`, `lot`, `stop_loss`, `take_profit`, `entry_price_candidate` を受けて order_request を組み立て
  - `trade_ok=false` や必要値不足時は `order_request=None` と理由を返す
- `src/execution/order_sender.py`
  - dry-run 時に `filled` を疑似返却
  - `dry_run=false` の場合は安全側で `failed` とし、実注文送信は行わない
- `src/execution/fill_handler.py`
  - `filled` の場合に entry_price_candidate を `fill_price` / `execution_price` として返す
  - それ以外は価格を None とする
- `src/execution/state_transition_manager.py`
  - `IDLE + trade_ok=true + filled -> POSITION_OPEN`
  - `rejected/cancelled/failed -> IDLE`
  - その他不整合は `ERROR`
- `tests/unit/execution/` と `tests/integration/test_risk_filter_to_execution.py` を追加

## 3. 結果
- Execution の dry-run 最小骨組みを責務分離して実装
- RiskFilter -> Execution の統合フローを確認
- `pytest -q` で全件通過

## 4. 保留 / TODO
- TODO(TBD): 状態遷移の実運用ルール（ENTRY_PENDING や EXIT_PENDING）の本格実装は別フェーズ
- TODO(TBD): Logger 連携と状態ログ永続化は次段階で追加
- TODO(TBD): `exit_signal` / 決済発注フローの初期骨組み追加は Execution skeleton 後に実装
- TODO(TBD): `docs/06_state_spec.md` の正式遷移（`IDLE -> ENTRY_PENDING -> POSITION_OPEN` など）に対し、現 skeleton は `IDLE` 起点の暫定簡略化。正式遷移列への収束は次フェーズで実施
