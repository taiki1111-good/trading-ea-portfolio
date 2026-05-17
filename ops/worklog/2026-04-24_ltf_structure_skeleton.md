# 2026-04-24 LTFStructure Skeleton Implementation

## 1. 目的
LTFStructure モジュールを最小ロジック付き骨組みとして実装し、Data -> LTFStructure の接続確認までを行う。Signal / RiskFilter / Execution / Logger / Evaluator の本実装には入らない。

## 2. 実装内容
- `src/ltf_structure/types.py`
  - LTFStructure 用の最小 dataclass / enum 値を定義
  - `SwingConfig`, `WaveConfig`, `BreakoutConfig`, `TriangleConfig`
  - `SwingPoint`, `SwingResult`, `WaveResult`, `BreakoutResult`, `TriangleResult`, `StructureResult`
- `src/ltf_structure/swing_extractor.py`
  - causal 前提の簡易 swing 抽出を実装（window 設定対応、未来参照なし）
- `src/ltf_structure/wave_classifier.py`
  - low-high-higher low / high-low-lower high の簡易 third 候補判定を実装
- `src/ltf_structure/breakout_detector.py`
  - close 基準の long/short breakout 判定を実装
- `src/ltf_structure/triangle_detector.py`
  - 初期 main では未使用として固定の `false/neutral` を返す骨組みを実装
- `src/ltf_structure/assembler.py`
  - third_wave_break の成立条件を統合
  - triangle 競合時は安全側で `none` を返す
- `tests/unit/ltf_structure/`
  - Swing / Wave / Breakout / Triangle / Assembler の unit test を追加
- `tests/integration/test_data_to_ltf_structure.py`
  - Data の PriceFrame を受けて LTFStructure 出力契約を確認する最小 integration test を追加
- `tests/unit/htf_context/__init__.py`, `tests/unit/ltf_structure/__init__.py`
  - pytest 収集時の同名モジュール衝突を回避する package marker を追加

## 3. 結果
- LTFStructure の下位部品を責務分離して実装
- main で返す `structure_type` を `third_wave_break / none` に限定
- triangle_break は初期 main から隔離
- `pytest -q` を実行し全件通過
  - `52 passed in 0.15s`

## 4. 保留 / TODO
- TODO(TBD): triangle 実検出は experiments フローで別管理し、main へは採用判断後に導入する
- TODO(TBD): swing 抽出の厳密化（ZigZag / 非因果判定）は初期 main スコープ外として保留
