# 02 Module Map

## 概要
上位モジュールと下位部品候補の分解を示す。  
上位モジュールは「流れ」を、下位部品は「交換可能な責務」を表す。

```mermaid
flowchart TB
    subgraph M1[Data]
        D1[PriceDataLoader]
        D2[EventDataLoader]
        D3[TimeframeAligner]
        D4[DataValidator]
    end

    subgraph M2[HTFContext]
        H1[TrendDetector]
        H2[ResistanceDetector]
        H3[SupportDetector]
        H4[ContextAssembler]
    end

    subgraph M3[LTFStructure]
        L1[SwingExtractor]
        L2[WaveClassifier]
        L3[TriangleDetector]
        L4[BreakoutDetector]
        L5[StructureAssembler]
    end

    subgraph M4[Signal]
        S1[DirectionAlignChecker]
        S2[PatternGate]
        S3[EntryRuleEngine]
        S4[ExitRuleEngine]
        S5[SignalAssembler]
    end

    subgraph M5[RiskFilter]
        R1[EventFilter]
        R2[SpreadFilter]
        R3[TradeLimitFilter]
        R4[StopLossPlanner]
        R5[TakeProfitPlanner]
        R6[PositionSizer]
        R7[RiskAssembler]
    end

    subgraph M6[Execution]
        E1[OrderBuilder]
        E2[OrderSender]
        E3[FillHandler]
        E4[StateTransitionManager]
    end

    subgraph M7[Logger]
        G1[DecisionLogger]
        G2[TradeLogger]
        G3[StateLogger]
        G4[EventLogger]
    end

    subgraph M8[Evaluator]
        V1[MetricsCalculator]
        V2[StructureAnalyzer]
        V3[FilterAnalyzer]
        V4[ReportAssembler]
    end

    M1 --> M2
    M1 --> M3
    M2 --> M4
    M3 --> M4
    M4 --> M5
    M5 --> M6
    M6 --> M7
    M7 --> M8
```

## 補足
- 図は「候補構成」を示す。実装順・実装粒度は `ops/CURRENT_TASKS.md` を優先する。
- Experiments は本体系と分離運用するため本図から除外した。

## 参照元
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/07_test_plan.md`
- `ops/CURRENT_TASKS.md`
