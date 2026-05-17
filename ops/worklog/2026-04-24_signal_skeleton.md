# 2026-04-24 Signal Skeleton Implementation

## 1. 目的
Signal モジュールを最小ロジック付き骨組みとして実装し、HTFContext + LTFStructure -> Signal の最小接続確認までを行う。RiskFilter / Execution / Logger / Evaluator の本実装には入らない。

## 2. 実装内容
- `src/signal/types.py`
  - Signal 用の最小 dataclass / enum 値を定義
  - `DirectionAlignResult`, `PatternGateResult`, `EntryRuleResult`, `ExitRuleResult`, `SignalResult`, `SignalInput`
- `src/signal/direction_align_checker.py`
  - `htf_bias` と `structure_direction` の最小整合判定を実装
  - neutral は entry 不可、方向不一致時も理由を返す
- `src/signal/pattern_gate.py`
  - 初期 main の許可条件（`third_wave_break` + `structure_candidate=true` + `breakout_flag=true` + `wave_phase=third`）を実装
  - `triangle_break` は experiments 扱いとして拒否
- `src/signal/entry_rule_engine.py`
  - `direction_aligned` + `pattern_allowed` + `structure_direction in {long, short}` のときのみ entry 成立
- `src/signal/exit_rule_engine.py`
  - 初期版骨組みとして `exit_signal=false` 固定を実装
- `src/signal/assembler.py`
  - 下位判定を統合して `entry_signal`, `exit_signal`, `signal_type`, `signal_reason` を返す
  - entry/exit 同時 true は安全側で `none` へフォールバック
- `tests/unit/signal/`
  - DirectionAlignChecker / PatternGate / EntryRuleEngine / ExitRuleEngine / SignalAssembler の unit test を追加
- `tests/integration/test_htf_ltf_to_signal.py`
  - HTFContext + LTFStructure -> Signal の最小接続確認を追加

## 3. 結果
- Signal の下位部品を責務分離して実装
- main で `triangle_break` を entry 候補に混在させない実装を確認
- exit ロジックは初期版として明示的に隔離
- `pytest -q` を実行し全件通過
  - `73 passed in 0.19s`

## 4. 保留 / TODO
- TODO(TBD): ExitRuleEngine の本格 exit 条件は Signal skeleton 受け入れ後に別フェーズで実装
- TODO(TBD): Signal と RiskFilter 境界で `signal_reason` の粒度最適化（必要なら docs と同時更新）
- TODO(TBD): `SignalInput` は将来の境界 DTO 候補として一旦保持し、RiskFilter 実装前判断で「採用継続 or 削除」を決定する
- TODO(TBD): HTFContext の追加項目（`htf_trend_dir` / `htf_trend_strength` / `htf_resistance_ok` / `htf_support_ok`）は、Signal skeleton 段階では「受け渡しのみ維持」とし、判定利用の要否は後続フェーズで明文化する
