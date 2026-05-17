# 04 Data Pipeline

## 概要
Data モジュール内でのデータ形式、整形、検証、受け渡しを示す。  
`CSV / parquet / pkl` の役割はデータソース方針に従い、検証結果は `data_valid_flag` と `validation_reason` で表現する。

```mermaid
flowchart TB
    subgraph SRC[Data Sources]
        CSV[CSV: 一次ソース候補]
        PQ[parquet: 正規化済み高速処理用]
        PKL[pkl: 作業キャッシュ]
        EVT[Event CSV]
    end

    CSV --> PL[PriceDataLoader]
    EVT --> EL[EventDataLoader]

    PQ -. role-based input .-> PL
    PKL -. cache input .-> PL

    PL --> TA[TimeframeAligner\n(H1/H4 ルール適用位置)]
    EL --> DV[DataValidator]
    TA --> DV

    DV -->|valid| OUT[Data Output\n(timestamp/OHLC/spread/volume/event_time/event_flag)]
    DV -->|invalid| NG[data_valid_flag=false\nvalidation_reason=...]

    OUT --> NEXT[HTFContext / LTFStructure]
    NG --> STOP[進行停止または安全側制御]
```

## 補足
- `parquet` / `pkl` は方針上の役割を示す。実装状況は `CURRENT_TASKS` とテストの進捗に従う。
- `H1/H4` の未来参照禁止は `TimeframeAligner` と受け入れ基準テストの対象。
- 入力契約違反・継続不能障害は例外、検証NGは失敗結果で返す。

## 参照元
- `docs/04_module_spec.md`（Data）
- `docs/10_interface_contract.md`（Data 出力契約）
- `docs/11_data_source_policy.md`
- `docs/07_test_plan.md`（Data 契約テスト）
