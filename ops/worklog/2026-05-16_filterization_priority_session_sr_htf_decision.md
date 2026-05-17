# 2026-05-16 filterization priority decision (Session / SR / HTF)

## 目的
- Phase 9 / Risk-Stop v0 / Lot Sizing v1 shadow comparison v0 の区切り後に、diagnostic_only から本体filter化候補へ進む前の優先順位を固定する。
- 今回は判断整理のみを対象とし、実装変更は行わない。

## 比較対象
- HTF filterization
- Session filterization
- SR filterization

## 推奨優先順位
1. HTF
2. Session
3. SR

---

## 1) HTF filterization（第1優先）
### 目的
- 上位環境（direction/bias）との整合を entry 判定に反映し、entry側課題とexit側課題を切り分けやすくする。

### 利点
- 「なぜ entry したか / 見送ったか」を構造的に説明しやすい。
- exit比較（fixed/trailing等）と独立に、entry集合差分を観測しやすい。
- 既存の HTF diagnostic 文脈を活用でき、優先判断の一貫性を保ちやすい。

### リスク
- neutral扱い（strict/permissive）で結果解釈がぶれやすい。
- trade_count変化だけを見て誤判断しやすい。
- 実装を急ぐと `Signal`/`PipelineAdapter` 境界で責務混在のリスクがある。

### diagnostic_only から本体filter化へ進める条件
- HTF ON/OFF で entry集合差分と rejected理由が再現可能に記録される。
- `rejected_count` / `rejected_by_reason` が説明可能で、reason分布が極端に不安定でない。
- 月別比較と Q1/Q2 比較で、一貫した傾向確認ができる。
- trade_count差分のみでなく、`win_rate` / `average_pnl` / `total_pnl` / `exit_reason counts` を併記して判断できる。

### 今回の非対応範囲
- HTF filter の実装ON
- `PipelineAdapter` / `BacktestRunner` / `Signal` / `RiskFilter` / `Execution` のコード変更
- 収益性確定判断

---

## 2) Session filterization（第2優先）
### 目的
- 時間帯・曜日要因を用いて、低品質時間の entry を抑制できるかを評価する。

### 利点
- 集計軸（hour/day/session_label）が比較的分かりやすく、診断観点を作りやすい。
- diagnostic_only からの段階移行（ラベル -> 候補filter）を設計しやすい。

### リスク
- 時間帯効果と戦略構造課題（HTF/SR/entry品質）が混ざりやすい。
- DSTや市場特性の扱い未固定だと、比較結果の説明力が下がる。
- 早期本体化で「時間帯で隠れた過学習」に見えるリスクがある。

### diagnostic_only から本体filter化へ進める条件
- diagnostic_only 時点で reason分布と session別統計が安定して取得できる。
- 月別比較 / Q1-Q2 比較で同方向の傾向確認ができる。
- rejected理由が「時間帯由来」と説明でき、他要因と切り分け可能。
- trade_count差分だけでなく、entry集合差分・`exit_reason counts` を含めて評価できる。

### 今回の非対応範囲
- Session filter の ON
- DST厳密実装
- broker時間/OANDA時間連動

---

## 3) SR filterization（第3優先）
### 目的
- 抵抗・支持近接による entry 回避を本体判断へ反映できるかを評価する。

### 利点
- 価格構造由来の見送り理由を強化できる可能性がある。
- 方向整合だけでは防げない局面の補助軸になりうる。

### リスク
- SR定義（rolling/reaction/閾値）が揺れやすく、比較不能化しやすい。
- 初手で本体化すると、HTF/Session要因と絡み、原因分解が困難になりやすい。
- reason語彙の増加で解析軸が不安定になりやすい。

### diagnostic_only から本体filter化へ進める条件
- SR定義と閾値の固定（少なくとも v1）が完了している。
- rejected理由の説明可能性があり、未定義語彙の乱立がない。
- 月別比較 / Q1-Q2 比較で傾向再現が取れる。
- trade_countだけでなく、entry集合差分・`win_rate`・`average_pnl`・`total_pnl`・`exit_reason counts` を確認できる。

### 今回の非対応範囲
- SR filter 実装ON
- reaction SR 本採用
- SR定義の最終確定実装

---

## 評価指標（共通）
- `trade_count` 差分だけで判断しない。
- `entry集合差分`
- `rejected_count`
- `rejected_by_reason`
- `win_rate`
- `average_pnl`
- `total_pnl`
- `exit_reason counts`
- 月別比較
- Q1/Q2比較
- diagnostic_only 時点の reason分布

## 今回の非対応範囲（全体）
- 本体filter化実装（HTF/Session/SR のいずれも ON にしない）
- `PipelineAdapter` / `BacktestRunner` / `Signal` / `RiskFilter` / `Execution path` 変更
- PnL / trade_count / entry / exit / trade_ok に影響する変更
- OANDA/API、実注文、broker連携
- 収益性確認済みの主張

## 次のGo条件（次フェーズ入口）
- 優先順位に基づき、まず HTF filter v1 の実装前契約（ON条件、neutral方針、評価/ログ項目、非対応範囲）を固定できること。
- もしくは、HTF diagnosticログの追加確認を先に実施し、契約固定に必要な根拠を揃えること。
