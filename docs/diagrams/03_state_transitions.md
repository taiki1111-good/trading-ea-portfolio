# 03 State Transitions

## 概要
`position_state` の基本遷移を示す。  
状態遷移は `StateTransitionManager` 経由で扱う前提とする。

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> ENTRY_PENDING: entry_signal && trade_ok
    ENTRY_PENDING --> POSITION_OPEN: order_result=filled
    ENTRY_PENDING --> IDLE: rejected/cancelled/failed

    POSITION_OPEN --> EXIT_PENDING: exit_signal || stop_loss_hit || take_profit_hit
    EXIT_PENDING --> IDLE: exit_filled

    IDLE --> SUSPENDED: event/limit/protection stop
    SUSPENDED --> IDLE: resume condition

    IDLE --> ERROR: unexpected exception
    ENTRY_PENDING --> ERROR: unexpected exception
    POSITION_OPEN --> ERROR: unexpected exception
    EXIT_PENDING --> ERROR: unexpected exception
    SUSPENDED --> ERROR: critical inconsistency

    ERROR --> SUSPENDED: fail-safe transition
```

## 補足
- `ANY -> ERROR` を個別遷移として明示した。
- 初期段階では `ERROR` 後に安全側として `SUSPENDED` へ落とす運用を許容する。

## 参照元
- `docs/06_state_spec.md`
- `docs/10_interface_contract.md`
- `docs/04_module_spec.md`（Execution / StateTransitionManager）
