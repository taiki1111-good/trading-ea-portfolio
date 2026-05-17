# 2026-05-03 HTFContext v0.2 Design Start

## なぜ Phase 4 に進むか
- Minimum Core v0.1 は structural validation complete として閉鎖済み。
- Phase 2 Halt/Risk diagnostic では A〜F 全シナリオで `net_counterfactual_effect_pips` がマイナスとなり、Phase 3 integration は No-Go。
- Halt Filter は一時保留し、Roadmap順序に従って Phase 4 HTFContext v0.2 設計へ進む。

## Halt/Risk の扱い
- Halt Filter F は将来の複数月確認候補として保留。
- ただし当面の本線タスクは HTFContext v0.2 設計。
- 本記録は収益性確認ではなく、実装前設計整理。

## HTFContext v0.2 で決めるべき事項
1. H4 bias 定義（`up/down/neutral/unknown`）と判定根拠。
2. H1 context 定義（`aligned_*`, `pullback_against_h4`, `range_or_neutral`, `transition`, `unknown`）。
3. H4/H1 組み合わせルール（許可・慎重・抑制の初期解釈）。
4. future leak 防止仕様（確定足のみ参照、lookahead禁止、M5 close整合）。
5. I/O contract とログ列（`htf_v2_*`, `h4_bias*`, `h1_context*`）の固定。
6. 実装前テスト観点（OFF/H1-only/H4+H1 比較、entry集合差分、conflict/reject追跡）。

## 注意
- 今回は HTFContext 実装・PipelineAdapter 統合は行わない。
- HTF 条件を本採用扱いしない。
- 結果を見て逐次調整しない。
