import unittest
from pathlib import Path

from src.data.price_loader import PriceDataLoader
from src.htf_context.assembler import ContextAssembler
from src.htf_context.resistance_detector import ResistanceDetector
from src.htf_context.support_detector import SupportDetector
from src.htf_context.trend_detector import TrendDetector
from src.htf_context.types import ResistanceConfig, SupportConfig, TrendConfig

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class TestDataToHTFContext(unittest.TestCase):
    def test_data_price_frame_is_accepted_by_htf_context(self):
        path = FIXTURE_DIR / "price_minimal.csv"
        price_frame = PriceDataLoader.load_from_csv(str(path), timeframe="H1")

        trend_result = TrendDetector.detect(price_frame, TrendConfig(lookback=2, min_strength=0.0))
        resistance_result = ResistanceDetector.detect(price_frame, ResistanceConfig(lookback=2, min_distance=0.01))
        support_result = SupportDetector.detect(price_frame, SupportConfig(lookback=2, min_distance=0.01))
        context_result = ContextAssembler.assemble(trend_result, resistance_result, support_result)

        self.assertIn(trend_result.htf_trend_dir, {"up", "down", "neutral"})
        self.assertGreaterEqual(trend_result.htf_trend_strength, 0.0)
        self.assertLessEqual(trend_result.htf_trend_strength, 1.0)
        self.assertIsInstance(resistance_result.htf_resistance_ok, bool)
        self.assertIsInstance(support_result.htf_support_ok, bool)
        self.assertIn(context_result.htf_bias, {"long_bias", "short_bias", "neutral"})
        self.assertTrue(context_result.htf_context_reason)


if __name__ == "__main__":
    unittest.main()
