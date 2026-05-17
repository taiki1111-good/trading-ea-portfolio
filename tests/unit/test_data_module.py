import unittest
from pathlib import Path
from datetime import datetime, timezone

from src.data.event_loader import EventDataLoader
from src.data.price_loader import PriceDataLoader
from src.data.validator import DataValidator
from src.data.timeframe_aligner import TimeframeAligner
from src.data.types import EventRecord, PriceBar

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class TestDataModule(unittest.TestCase):
    """High-level Data contract tests.

    This file verifies the Data 層の全体契約を軽く確認し、
    詳細な部品テストは `tests/unit/data/` に移譲します。
    """

    def test_price_loader_reads_valid_csv_and_normalizes_utc(self):
        path = FIXTURE_DIR / "price_minimal.csv"
        price_frame = PriceDataLoader.load_from_csv(str(path), timeframe="H1")

        self.assertEqual(len(price_frame), 2)
        self.assertIsInstance(price_frame[0], PriceBar)
        self.assertEqual(price_frame[0].timestamp, datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(price_frame[0].open, 1.1000)

    def test_event_loader_reads_valid_csv_and_normalizes_utc(self):
        path = FIXTURE_DIR / "event_minimal.csv"
        event_frame = EventDataLoader.load_from_csv(str(path))

        self.assertEqual(len(event_frame), 1)
        self.assertEqual(event_frame[0].event_type, "cpi")
        self.assertEqual(event_frame[0].event_time, datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc))

    def test_data_validator_returns_failure_on_invalid_price_sequence(self):
        price_frame = [
            PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.1, high=1.2, low=1.0, close=1.15, spread=0.2, volume=100),
            PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.05, spread=0.2, volume=100),
        ]
        result = DataValidator.validate(price_frame)

        self.assertFalse(result.data_valid_flag)
        self.assertIn("strictly ascending", result.validation_reason)

    def test_validator_matches_events_and_preserves_output_contract(self):
        price_frame = [
            PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.2, low=1.0, close=1.1, spread=0.2, volume=100),
            PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.1, high=1.3, low=1.0, close=1.2, spread=0.2, volume=100),
        ]
        event = [
            EventRecord(
                event_time=datetime(2024, 1, 1, 0, 0, 30, tzinfo=timezone.utc),
                event_type="cpi",
                event_flag=False,
            )
        ]
        result = DataValidator.validate(price_frame, event_frame=event, validation_config={"event_tolerance_seconds": 60})

        self.assertTrue(result.data_valid_flag)
        self.assertEqual(result.validation_reason, "")
        self.assertTrue(result.event_frame[0].event_flag)

    def test_timeframe_aligner_aligns_without_future_reference(self):
        ltf = [
            PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.1, low=0.9, close=1.05, spread=0.2, volume=100),
            PriceBar(timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc), open=1.05, high=1.15, low=1.0, close=1.1, spread=0.2, volume=80),
        ]
        htf = [
            PriceBar(timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), open=1.0, high=1.2, low=0.9, close=1.1, spread=0.2, volume=200),
        ]
        result = TimeframeAligner.align(ltf, htf)

        self.assertEqual(len(result.aligned_htf_context_ref), 2)
        self.assertIn("without future reference", result.align_reason)


if __name__ == "__main__":
    unittest.main()
