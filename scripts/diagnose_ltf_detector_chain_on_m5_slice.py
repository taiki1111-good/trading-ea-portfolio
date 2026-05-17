#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import timezone
from pathlib import Path
from typing import Any

from src.backtest.pipeline_adapter import PipelineAdapterConfig
from src.data.price_loader import PriceDataLoader
from src.htf_context.assembler import ContextAssembler
from src.htf_context.resistance_detector import ResistanceDetector
from src.htf_context.support_detector import SupportDetector
from src.htf_context.trend_detector import TrendDetector
from src.htf_context.types import ResistanceConfig, SupportConfig, TrendConfig
from src.ltf_structure.assembler import StructureAssembler
from src.ltf_structure.breakout_detector import BreakoutDetector
from src.ltf_structure.swing_extractor import SwingExtractor
from src.ltf_structure.triangle_detector import TriangleDetector
from src.ltf_structure.types import BreakoutConfig, SwingConfig, TriangleConfig, WaveConfig
from src.ltf_structure.wave_classifier import WaveClassifier
from src.signal.direction_align_checker import DirectionAlignChecker
from src.signal.pattern_gate import PatternGate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose LTF detector chain behavior on M5 slice.")
    parser.add_argument("--input-csv", required=True, help="PriceDataLoader-compatible M5 CSV.")
    parser.add_argument("--output-dir", required=True, help="Output directory for diagnosis files.")
    parser.add_argument("--max-bars", type=int, default=None, help="Optional max bars to diagnose.")
    return parser.parse_args()


def decide_fail_stage(
    swing_count: int,
    wave_phase: str,
    breakout_flag: bool,
    wave_direction: str,
    breakout_direction: str,
    structure_candidate: bool,
    direction_aligned: bool,
    pattern_allowed: bool,
) -> str:
    if swing_count < 3:
        return "insufficient_swing"
    if wave_phase != "third":
        return "wave_not_third"
    if not breakout_flag:
        return "no_breakout"
    if wave_direction != breakout_direction:
        return "direction_mismatch_wave_breakout"
    if not structure_candidate:
        return "no_structure_candidate"
    if not direction_aligned:
        return "htf_direction_mismatch"
    if not pattern_allowed:
        return "pattern_gate_rejected"
    return "detector_chain_entry_candidate"


def write_summary_md(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# LTF Detector Chain Diagnosis Summary",
        "",
        f"- generated_at_utc: {summary['generated_at_utc']}",
        f"- total_bars: {summary['total_bars']}",
        f"- bars_with_swing_points: {summary['bars_with_swing_points']}",
        f"- bars_wave_phase_third: {summary['bars_wave_phase_third']}",
        f"- bars_breakout_true: {summary['bars_breakout_true']}",
        f"- bars_structure_candidate_true: {summary['bars_structure_candidate_true']}",
        f"- bars_direction_aligned_true: {summary['bars_direction_aligned_true']}",
        f"- bars_pattern_allowed_true: {summary['bars_pattern_allowed_true']}",
        f"- bars_wave_third_and_breakout_true: {summary['bars_wave_third_and_breakout_true']}",
        f"- bars_wave_breakout_direction_match: {summary['bars_wave_breakout_direction_match']}",
        f"- bars_breakout_true_but_wave_unknown: {summary['bars_breakout_true_but_wave_unknown']}",
        f"- bars_wave_third_but_no_breakout: {summary['bars_wave_third_but_no_breakout']}",
        f"- bars_breakout_after_recent_third_3: {summary['bars_breakout_after_recent_third_3']}",
        f"- bars_breakout_after_recent_third_5: {summary['bars_breakout_after_recent_third_5']}",
        f"- bars_breakout_after_recent_third_10: {summary['bars_breakout_after_recent_third_10']}",
        f"- direction_match_after_recent_third_3: {summary['direction_match_after_recent_third_3']}",
        f"- direction_match_after_recent_third_5: {summary['direction_match_after_recent_third_5']}",
        f"- direction_match_after_recent_third_10: {summary['direction_match_after_recent_third_10']}",
        f"- temporal_third_break_candidate_count_3: {summary['temporal_third_break_candidate_count_3']}",
        f"- temporal_third_break_candidate_count_5: {summary['temporal_third_break_candidate_count_5']}",
        f"- temporal_third_break_candidate_count_10: {summary['temporal_third_break_candidate_count_10']}",
        f"- temporal_direction_match_count_3: {summary['temporal_direction_match_count_3']}",
        f"- temporal_direction_match_count_5: {summary['temporal_direction_match_count_5']}",
        f"- temporal_direction_match_count_10: {summary['temporal_direction_match_count_10']}",
        f"- detector_chain_entry_candidate_count: {summary['detector_chain_entry_candidate_count']}",
        f"- fail_stage_counts: {summary['fail_stage_counts']}",
        "",
        "## Notes",
        "- This is detector-chain behavior diagnosis only.",
        "- Not a profitability evaluation.",
        "- No future bars are used per step (`window = bars[:i+1]`).",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bars = PriceDataLoader.load_from_csv(args.input_csv, timeframe="M5")
    if args.max_bars is not None:
        bars = bars[: max(0, args.max_bars)]

    cfg = PipelineAdapterConfig()
    rows: list[dict[str, Any]] = []
    fail_counts: Counter[str] = Counter()
    wave_phase_history: list[str] = []
    wave_direction_history: list[str] = []

    for i, _bar in enumerate(bars):
        window = bars[: i + 1]
        current_bar = window[-1]

        trend_result = TrendDetector.detect(
            window,
            TrendConfig(lookback=cfg.trend_lookback, min_strength=cfg.trend_min_strength),
        )
        resistance_result = ResistanceDetector.detect(
            window,
            ResistanceConfig(lookback=cfg.support_resistance_lookback, min_distance=cfg.min_distance),
        )
        support_result = SupportDetector.detect(
            window,
            SupportConfig(lookback=cfg.support_resistance_lookback, min_distance=cfg.min_distance),
        )
        htf_context = ContextAssembler.assemble(
            trend_result=trend_result,
            resistance_result=resistance_result,
            support_result=support_result,
        )

        swing_result = SwingExtractor.extract(window, SwingConfig(window=cfg.swing_window, causal=cfg.swing_causal))
        wave_result = WaveClassifier.classify(
            swing_result.swing_points,
            WaveConfig(min_swing_points=cfg.min_swing_points),
        )
        breakout_result = BreakoutDetector.detect(
            window,
            swing_result.swing_points,
            BreakoutConfig(use_close=cfg.breakout_use_close),
        )
        triangle_result = TriangleDetector.detect(
            ltf_price_frame=window,
            swing_points=swing_result.swing_points,
            triangle_config=TriangleConfig(lookback=cfg.triangle_lookback, tolerance=cfg.triangle_tolerance),
        )
        structure_result = StructureAssembler.assemble(
            wave_phase=wave_result.wave_phase,
            wave_direction=wave_result.wave_direction,
            breakout_flag=breakout_result.breakout_flag,
            breakout_direction=breakout_result.breakout_direction,
            triangle_flag=triangle_result.triangle_flag,
            sub_reasons=[
                htf_context.htf_context_reason,
                swing_result.swing_reason,
                wave_result.wave_reason,
                breakout_result.breakout_reason,
                triangle_result.triangle_reason,
            ],
        )
        direction_result = DirectionAlignChecker.check(
            htf_bias=htf_context.htf_bias,
            structure_direction=structure_result.structure_direction,
            htf_context_reason=htf_context.htf_context_reason,
            pattern_reason=structure_result.pattern_reason,
        )
        pattern_gate_result = PatternGate.check(
            structure_type=structure_result.structure_type,
            structure_candidate=structure_result.structure_candidate,
            breakout_flag=breakout_result.breakout_flag,
            wave_phase=wave_result.wave_phase,
            pattern_reason=structure_result.pattern_reason,
        )

        latest_swing_type = ""
        latest_swing_price = ""
        if swing_result.swing_points:
            latest = swing_result.swing_points[-1]
            latest_swing_type = latest.swing_type
            latest_swing_price = latest.price

        fail_stage = decide_fail_stage(
            swing_count=len(swing_result.swing_points),
            wave_phase=wave_result.wave_phase,
            breakout_flag=breakout_result.breakout_flag,
            wave_direction=wave_result.wave_direction,
            breakout_direction=breakout_result.breakout_direction,
            structure_candidate=structure_result.structure_candidate,
            direction_aligned=direction_result.direction_aligned,
            pattern_allowed=pattern_gate_result.pattern_allowed,
        )
        fail_counts[fail_stage] += 1

        recent_third_direction_map: dict[int, str] = {}
        recent_third_within_map: dict[int, bool] = {}
        for lookback_bars in (3, 5, 10):
            start_idx = max(0, i - lookback_bars + 1)
            recent_direction = ""
            found = False
            for history_idx in range(i, start_idx - 1, -1):
                if history_idx == i:
                    phase = wave_result.wave_phase
                    direction = wave_result.wave_direction
                else:
                    phase = wave_phase_history[history_idx]
                    direction = wave_direction_history[history_idx]
                if phase == "third":
                    found = True
                    recent_direction = direction
                    break
            recent_third_within_map[lookback_bars] = found
            recent_third_direction_map[lookback_bars] = recent_direction

        wave_third_and_breakout_true = wave_result.wave_phase == "third" and breakout_result.breakout_flag
        wave_breakout_direction_match = (
            wave_third_and_breakout_true
            and wave_result.wave_direction in {"long", "short"}
            and wave_result.wave_direction == breakout_result.breakout_direction
        )
        breakout_true_but_wave_unknown = breakout_result.breakout_flag and wave_result.wave_phase == "unknown"
        wave_third_but_no_breakout = wave_result.wave_phase == "third" and not breakout_result.breakout_flag

        breakout_after_recent_third_3 = breakout_result.breakout_flag and recent_third_within_map[3]
        breakout_after_recent_third_5 = breakout_result.breakout_flag and recent_third_within_map[5]
        breakout_after_recent_third_10 = breakout_result.breakout_flag and recent_third_within_map[10]

        rows.append(
            {
                "index": i,
                "timestamp": current_bar.timestamp.astimezone(timezone.utc).isoformat(),
                "close": current_bar.close,
                "swing_count": len(swing_result.swing_points),
                "latest_swing_type": latest_swing_type,
                "latest_swing_price": latest_swing_price,
                "wave_phase": wave_result.wave_phase,
                "wave_direction": wave_result.wave_direction,
                "breakout_flag": breakout_result.breakout_flag,
                "breakout_direction": breakout_result.breakout_direction,
                "breakout_level": breakout_result.breakout_level,
                "breakout_reason": breakout_result.breakout_reason,
                "wave_third_and_breakout_true": wave_third_and_breakout_true,
                "wave_breakout_direction_match": wave_breakout_direction_match,
                "breakout_true_but_wave_unknown": breakout_true_but_wave_unknown,
                "wave_third_but_no_breakout": wave_third_but_no_breakout,
                "recent_third_candidate_within_3_bars": recent_third_within_map[3],
                "recent_third_candidate_within_5_bars": recent_third_within_map[5],
                "recent_third_candidate_within_10_bars": recent_third_within_map[10],
                "breakout_after_recent_third_3": breakout_after_recent_third_3,
                "breakout_after_recent_third_5": breakout_after_recent_third_5,
                "breakout_after_recent_third_10": breakout_after_recent_third_10,
                "recent_third_direction_3": recent_third_direction_map[3],
                "recent_third_direction_5": recent_third_direction_map[5],
                "recent_third_direction_10": recent_third_direction_map[10],
                "triangle_flag": triangle_result.triangle_flag,
                "structure_type": structure_result.structure_type,
                "structure_direction": structure_result.structure_direction,
                "structure_candidate": structure_result.structure_candidate,
                "htf_bias": htf_context.htf_bias,
                "direction_aligned": direction_result.direction_aligned,
                "pattern_allowed": pattern_gate_result.pattern_allowed,
                "fail_stage": fail_stage,
            }
        )
        wave_phase_history.append(wave_result.wave_phase)
        wave_direction_history.append(wave_result.wave_direction)

    diagnosis_csv = output_dir / "ltf_detector_diagnosis.csv"
    with diagnosis_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "index",
            "timestamp",
            "close",
            "swing_count",
            "latest_swing_type",
            "latest_swing_price",
            "wave_phase",
            "wave_direction",
            "breakout_flag",
            "breakout_direction",
            "breakout_level",
            "breakout_reason",
            "wave_third_and_breakout_true",
            "wave_breakout_direction_match",
            "breakout_true_but_wave_unknown",
            "wave_third_but_no_breakout",
            "recent_third_candidate_within_3_bars",
            "recent_third_candidate_within_5_bars",
            "recent_third_candidate_within_10_bars",
            "breakout_after_recent_third_3",
            "breakout_after_recent_third_5",
            "breakout_after_recent_third_10",
            "recent_third_direction_3",
            "recent_third_direction_5",
            "recent_third_direction_10",
            "triangle_flag",
            "structure_type",
            "structure_direction",
            "structure_candidate",
            "htf_bias",
            "direction_aligned",
            "pattern_allowed",
            "fail_stage",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "generated_at_utc": datetime_now_utc_iso(),
        "total_bars": len(rows),
        "bars_with_swing_points": sum(1 for r in rows if int(r["swing_count"]) > 0),
        "bars_wave_phase_third": sum(1 for r in rows if r["wave_phase"] == "third"),
        "bars_breakout_true": sum(1 for r in rows if bool(r["breakout_flag"]) is True),
        "bars_structure_candidate_true": sum(1 for r in rows if bool(r["structure_candidate"]) is True),
        "bars_direction_aligned_true": sum(1 for r in rows if bool(r["direction_aligned"]) is True),
        "bars_pattern_allowed_true": sum(1 for r in rows if bool(r["pattern_allowed"]) is True),
        "bars_wave_third_and_breakout_true": sum(1 for r in rows if bool(r["wave_third_and_breakout_true"]) is True),
        "bars_wave_breakout_direction_match": sum(1 for r in rows if bool(r["wave_breakout_direction_match"]) is True),
        "bars_breakout_true_but_wave_unknown": sum(1 for r in rows if bool(r["breakout_true_but_wave_unknown"]) is True),
        "bars_wave_third_but_no_breakout": sum(1 for r in rows if bool(r["wave_third_but_no_breakout"]) is True),
        "bars_breakout_after_recent_third_3": sum(1 for r in rows if bool(r["breakout_after_recent_third_3"]) is True),
        "bars_breakout_after_recent_third_5": sum(1 for r in rows if bool(r["breakout_after_recent_third_5"]) is True),
        "bars_breakout_after_recent_third_10": sum(1 for r in rows if bool(r["breakout_after_recent_third_10"]) is True),
        "direction_match_after_recent_third_3": sum(
            1
            for r in rows
            if bool(r["breakout_after_recent_third_3"]) is True
            and r["recent_third_direction_3"] in {"long", "short"}
            and r["recent_third_direction_3"] == r["breakout_direction"]
        ),
        "direction_match_after_recent_third_5": sum(
            1
            for r in rows
            if bool(r["breakout_after_recent_third_5"]) is True
            and r["recent_third_direction_5"] in {"long", "short"}
            and r["recent_third_direction_5"] == r["breakout_direction"]
        ),
        "direction_match_after_recent_third_10": sum(
            1
            for r in rows
            if bool(r["breakout_after_recent_third_10"]) is True
            and r["recent_third_direction_10"] in {"long", "short"}
            and r["recent_third_direction_10"] == r["breakout_direction"]
        ),
        "temporal_third_break_candidate_count_3": sum(
            1
            for r in rows
            if bool(r["breakout_flag"]) is True
            and bool(r["recent_third_candidate_within_3_bars"]) is True
        ),
        "temporal_third_break_candidate_count_5": sum(
            1
            for r in rows
            if bool(r["breakout_flag"]) is True
            and bool(r["recent_third_candidate_within_5_bars"]) is True
        ),
        "temporal_third_break_candidate_count_10": sum(
            1
            for r in rows
            if bool(r["breakout_flag"]) is True
            and bool(r["recent_third_candidate_within_10_bars"]) is True
        ),
        "temporal_direction_match_count_3": sum(
            1
            for r in rows
            if bool(r["breakout_flag"]) is True
            and bool(r["recent_third_candidate_within_3_bars"]) is True
            and r["recent_third_direction_3"] in {"long", "short"}
            and r["recent_third_direction_3"] == r["breakout_direction"]
        ),
        "temporal_direction_match_count_5": sum(
            1
            for r in rows
            if bool(r["breakout_flag"]) is True
            and bool(r["recent_third_candidate_within_5_bars"]) is True
            and r["recent_third_direction_5"] in {"long", "short"}
            and r["recent_third_direction_5"] == r["breakout_direction"]
        ),
        "temporal_direction_match_count_10": sum(
            1
            for r in rows
            if bool(r["breakout_flag"]) is True
            and bool(r["recent_third_candidate_within_10_bars"]) is True
            and r["recent_third_direction_10"] in {"long", "short"}
            and r["recent_third_direction_10"] == r["breakout_direction"]
        ),
        "detector_chain_entry_candidate_count": int(fail_counts.get("detector_chain_entry_candidate", 0)),
        "fail_stage_counts": dict(fail_counts),
    }

    summary_csv = output_dir / "ltf_detector_diagnosis_summary.csv"
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        for k, v in summary.items():
            writer.writerow({"metric": k, "value": v})

    summary_md = output_dir / "ltf_detector_diagnosis_summary.md"
    write_summary_md(summary_md, summary)

    print(f"[done] diagnosis_csv={diagnosis_csv}")
    print(f"[done] summary_md={summary_md}")
    print(f"[done] summary_csv={summary_csv}")
    print(f"[summary] total_bars={summary['total_bars']}, detector_chain_entry_candidate_count={summary['detector_chain_entry_candidate_count']}")
    return 0


def datetime_now_utc_iso() -> str:
    from datetime import datetime

    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
