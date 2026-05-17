# 戦略拡張方針（future extension）

## 1. 文書の目的
本書は、`trading-ea` における将来の戦略拡張方針を整理するための方針文書である。
現行の continuation 系戦略（例: `third_wave_break`, `triangle_break`）に加えて、continuation の失敗を次戦略の入力として扱う拡張方向を明確化する。

本書は design/policy の整理を目的とし、実装済み・採用済み・収益性確認済みを意味しない。
本リポジトリは研究・検証用EAであり、実運用EAではない。

## 2. 非対応範囲（今回の方針整理で行わないこと）
- 本体売買ロジック変更なし
- BacktestRunner 統合なし
- 収益性評価なし
- 実 broker / OANDA / API / 実注文なし
- `Signal` / `RiskFilter` / `PipelineAdapter` / `Execution` の本体挙動変更なし

## 3. 戦略分類（future extension）

### 3.1 Continuation Strategy
- `third_wave_break`
- `triangle_break`
- second-wave trend-follow
- breakout continuation

補足:
- 継続方向へ伸びる局面を扱う既存系統。
- 初期 main / experiments 境界は既存方針を維持する。

### 3.2 Failed Continuation Strategy
- `failed_second_wave_short`
- `failed_continuation_short`
- `triangle_breakout_failure_short`
- `bull_trap_short`
- 既存ロング戦略の失敗を逆方向シグナル候補として扱う

設計思想:
- 中核は「ショート戦略を足すこと」ではなく、「Continuation の失敗を別戦略の入力にすること」。
- 二波目ロング成功 -> continuation
- 二波目ロング失敗 -> `failed_continuation_short`
- 三角上抜け成功 -> breakout continuation
- 三角上抜け失敗 -> `triangle_breakout_failure_short`
- 天井や底を当てるのではなく、失敗確認後の retest / breakdown を扱う。

### 3.3 Distribution / Breakdown Strategy
- `distribution_breakdown_short`
- `breakdown_retest_short`
- `neckline_break_short`
- 高値圏の二山、上抜け失敗、ネックライン割れ、戻り失敗を扱う

補足:
- 分配局面や上昇終盤の崩れを、確認後に扱う将来候補。
- 予測先行ではなく、構造崩れ確認を重視する。

### 3.4 Accumulation / Base Breakout Strategy
- 底当てではなく、底形成後の再上昇を扱う

補足:
- 反転点の当てものではなく、ベース形成と再上昇確認を前提にする。

### 3.5 Commander Strategy Selection
戦略選択は銘柄名そのものではなく、以下の組み合わせで行う将来方針とする。
- 銘柄特性
- 現在局面
- 戦略成功/失敗履歴

局面別の許可戦略・抑制戦略（方針表）:

| 局面 | 許可戦略（候補） | 抑制戦略（候補） |
|---|---|---|
| 上昇初期 | `second-wave trend-follow`, breakout continuation | `failed_continuation_short` |
| 上昇中盤 | `third_wave_break`, breakout continuation | `neckline_break_short` |
| 上昇終盤 | `failed_continuation_short`, `bull_trap_short` | 追随型 continuation の過剰追加 |
| 分配 | `distribution_breakdown_short`, `breakdown_retest_short` | 強気 continuation |
| 下落 | `breakdown_retest_short`, continuation short（将来候補） | 強気 breakout continuation |
| 底形成 | base breakout 系の事後確認型 | 底当て逆張り |

注意:
- 上表は strategy selection policy の設計方針であり、現行実装の有効化を意味しない。

## 4. Exit / Risk の発展課題（整合メモ）
- `fixed_sl_tp` は baseline として維持する。
- 将来候補:
  - partial take profit
  - ATR trailing
  - swing-based stop
  - trend_break_exit
  - hybrid_exit

整合条件:
- 上記は `docs/17_backtest_design.md` の既存 exit 方針と矛盾しない範囲で、段階比較として扱う。
- 既存 baseline を置換せず、比較可能性を優先する。

## 5. 運用上の扱い
- 本書は future extension policy であり、実装計画の即時着手を意味しない。
- main と experiments の分離方針を維持する。
- 本体導入時は別途、契約文書（`docs/04`, `docs/05`, `docs/10`, `docs/17`）と `ops/CURRENT_TASKS.md` の更新を前提にする。
