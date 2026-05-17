# 2026-05-03 SR Concept Split: rolling high/low vs reaction SR

## 背景（代表月結果）
- 対象: `oos2_202411_sr_v2_diag_trailing_matched`
- `sr_proximity_flag=True` 側は悪化群ではなかった。
- 特に `support` 近接は代表月で利益源となった。
- よって rolling high/low 近接を単純な危険filterとして使う根拠は不足。

## rolling high/low SR の解釈
- fixed window 高値/安値ベースの近接ラベル。
- 性質は反発型SRよりも breakout近接・余地診断に近い。
- 当面は diagnostic/explanation layer として継続。
- 現時点で実filter化しない。

## reaction SR 候補（別定義）
- 複数回反発した価格帯（price zone）。
- 候補:
  - swing high/low cluster
  - H1/H4 high/low
  - price touch count
  - rejection candle / wick
- 人間裁量の「壁・支え」に近い概念として別扱いにする。

## 判断
- rolling high/low SR と reaction SR を混同しない。
- rolling high/low SR の結果のみで「SRは使えない」と判断しない。
- reaction SR は後続候補として保持し、現時点では未実装。
- Phase 6 へ先に進むか reaction SR 設計を先に行うかは未決。

## 未解決事項
- reaction SR の最小I/O契約を先に固めるか。
- Phase 6 Session/Time filter を優先するか。
- reaction SR の定量化（zone定義・touch/rejection条件）をどう固定するか。
