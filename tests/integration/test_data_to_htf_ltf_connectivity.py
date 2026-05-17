from pathlib import Path

from src.data.event_loader import EventDataLoader
from src.data.price_loader import PriceDataLoader
from src.data.validator import DataValidator
from src.data.timeframe_aligner import TimeframeAligner
from src.data.types import EventRecord

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_data_frame_contract_can_be_consumed_by_htf_ltf_alignment():
    price_frame = PriceDataLoader.load_from_csv(str(FIXTURE_DIR / "price_m5_h1_h4_base.csv"), timeframe="M5")
    event_frame = EventDataLoader.load_from_csv(str(FIXTURE_DIR / "event_valid_utc.csv"))

    result = DataValidator.validate(
        price_frame,
        event_frame=event_frame,
        validation_config={
            "event_tolerance_seconds": 120,
            "expected_interval_seconds": 300,
        },
    )

    assert result.data_valid_flag is True
    assert result.validation_reason == ""
    assert len(result.validated_frame) >= 12
    assert all(bar.timestamp.tzinfo is not None for bar in result.validated_frame)
    assert all(bar.open is not None and bar.high is not None and bar.low is not None and bar.close is not None for bar in result.validated_frame)
    assert all(bar.spread >= 0 for bar in result.validated_frame)
    assert all(bar.volume >= 0 for bar in result.validated_frame)

    assert isinstance(result.event_frame, list)
    assert len(result.event_frame) == 1
    assert isinstance(result.event_frame[0], EventRecord)
    assert result.event_frame[0].event_time.tzinfo is not None
    assert isinstance(result.event_frame[0].event_flag, bool)

    # Downstream HTF/LTF 接続の骨組み: Data 出力を LTF -> HTF 揃えに渡せること
    h1_bars = TimeframeAligner.aggregate_ltf_to_htf(result.validated_frame, "H1")
    assert len(h1_bars) >= 1
    align = TimeframeAligner.align(result.validated_frame[:2], h1_bars)

    assert len(align.aligned_htf_context_ref) == 2
    assert "without future reference" in align.align_reason
