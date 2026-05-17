from pathlib import Path

from src.data.price_loader import PriceDataLoader
from src.ltf_structure.assembler import StructureAssembler
from src.ltf_structure.breakout_detector import BreakoutDetector
from src.ltf_structure.swing_extractor import SwingExtractor
from src.ltf_structure.triangle_detector import TriangleDetector
from src.ltf_structure.types import BreakoutConfig, SwingConfig
from src.ltf_structure.wave_classifier import WaveClassifier

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_data_frame_contract_can_be_consumed_by_ltf_structure():
    price_frame = PriceDataLoader.load_from_csv(str(FIXTURE_DIR / "price_m5_valid_utc.csv"), timeframe="M5")

    swing_result = SwingExtractor.extract(price_frame, SwingConfig(window=2, causal=True))
    wave_result = WaveClassifier.classify(swing_result.swing_points)
    breakout_result = BreakoutDetector.detect(price_frame, swing_result.swing_points, BreakoutConfig(use_close=True))
    triangle_result = TriangleDetector.detect(price_frame, swing_result.swing_points)
    structure_result = StructureAssembler.assemble(
        wave_phase=wave_result.wave_phase,
        wave_direction=wave_result.wave_direction,
        breakout_flag=breakout_result.breakout_flag,
        breakout_direction=breakout_result.breakout_direction,
        triangle_flag=triangle_result.triangle_flag,
        sub_reasons=[
            swing_result.swing_reason,
            wave_result.wave_reason,
            breakout_result.breakout_reason,
            triangle_result.triangle_reason,
        ],
    )

    assert isinstance(swing_result.swing_points, list)
    assert swing_result.swing_reason
    assert wave_result.wave_phase in {"first", "second", "third", "unknown"}
    assert wave_result.wave_direction in {"long", "short", "neutral"}
    assert isinstance(breakout_result.breakout_flag, bool)
    assert breakout_result.breakout_direction in {"long", "short", "neutral"}
    assert structure_result.structure_type in {"third_wave_break", "none"}
    assert structure_result.structure_direction in {"long", "short", "neutral"}
    assert isinstance(structure_result.structure_candidate, bool)
    assert structure_result.pattern_reason
    assert structure_result.structure_type != "triangle_break"
