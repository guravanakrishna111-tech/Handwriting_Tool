from __future__ import annotations

import math
import random
from dataclasses import dataclass

from handwriting_tool.config import AppConfig
from handwriting_tool.types import LinePlan, StyleProfile
from handwriting_tool.utils import clamp


CONNECTABLE_PAIRS = {
    "th",
    "he",
    "an",
    "re",
    "er",
    "in",
    "ng",
    "st",
    "on",
    "en",
    "ed",
    "ll",
    "oo",
    "tt",
    "ch",
    "sh",
}

NARROW_CHARS = set("ilI.,'`!|")
WIDE_CHARS = set("mwMW")
OPEN_LEFT = set("acdegopq")
OPEN_RIGHT = set("bcdehklot")


@dataclass
class PlacementAdjustment:
    advance: float
    overlap_px: float
    join: bool
    y_rhythm_px: float


class HumanSpacingEngine:
    """Pair-aware spacing model for handwriting flow.

    The renderer still draws one character image at a time, but placement is
    driven by local context, writing speed, slant, writer rhythm, and line
    fatigue instead of fixed glyph advances.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._phase = random.uniform(0, math.tau)

    def adjustment(
        self,
        previous_char: str | None,
        char: str,
        next_char: str | None,
        intrinsic_advance: float,
        style: StyleProfile,
        line: LinePlan,
        char_index: int,
    ) -> PlacementAdjustment:
        if char.isspace():
            return PlacementAdjustment(
                advance=self.word_gap(previous_char, next_char, style, line, char_index),
                overlap_px=0.0,
                join=False,
                y_rhythm_px=0.0,
            )

        rush = clamp(self.config.controls.exam_rush, 0.0, 1.0)
        careful = clamp(self.config.controls.writing_carefulness, 0.0, 1.0)
        consistency = clamp(self.config.controls.letter_consistency, 0.0, 1.0)
        pair = f"{char}{next_char or ''}".lower()
        previous_pair = f"{previous_char or ''}{char}".lower()

        compression = 1.0 - rush * 0.18 + careful * 0.04
        shape_bias = self._shape_bias(char, next_char)
        slant_bias = -abs(style.tilt_mean_deg) * 0.045
        rhythm = math.sin(self._phase + char_index * 0.72) * (1.0 - consistency) * 2.8
        fatigue_tightening = -line.fatigue * (1.8 + rush * 2.2)
        random_jitter = random.gauss(0.0, (1.25 - consistency) * (2.0 - careful))

        join = self.should_join(char, next_char, previous_char)
        overlap = 0.0
        if join:
            overlap = random.uniform(1.5, 6.0) + rush * 3.0 + max(0.0, -slant_bias)
        elif previous_pair in CONNECTABLE_PAIRS:
            overlap = random.uniform(0.5, 2.2)

        if pair in {"rn", "nn", "mn", "mm"}:
            shape_bias -= random.uniform(2.0, 4.8)
        if pair in {"il", "li", "ll"}:
            shape_bias += random.uniform(0.4, 2.4)

        advance = intrinsic_advance * compression + shape_bias + slant_bias + rhythm + fatigue_tightening + random_jitter - overlap
        lower_bound = intrinsic_advance * (0.42 if join else 0.54)
        upper_bound = intrinsic_advance * (0.92 + careful * 0.18)
        y_rhythm = math.sin(self._phase * 0.5 + char_index * 0.38) * (1.2 + line.fatigue * 2.6)
        return PlacementAdjustment(
            advance=clamp(advance, lower_bound, upper_bound),
            overlap_px=max(0.0, overlap),
            join=join,
            y_rhythm_px=y_rhythm,
        )

    def word_gap(
        self,
        previous_char: str | None,
        next_char: str | None,
        style: StyleProfile,
        line: LinePlan,
        char_index: int,
    ) -> float:
        rush = clamp(self.config.controls.exam_rush, 0.0, 1.0)
        careful = clamp(self.config.controls.writing_carefulness, 0.0, 1.0)
        rhythm = math.sin(self._phase + char_index * 0.47) * style.word_spacing_std * 0.45
        crowded_ending = -line.fatigue * random.uniform(2.0, 7.0)
        base = random.gauss(style.word_spacing_mean, max(1.4, style.word_spacing_std))
        gap = base * (1.0 - rush * 0.28 + careful * 0.10) + rhythm + crowded_ending
        if previous_char and previous_char in ",.;:":
            gap += random.uniform(2.0, 7.0)
        if next_char and next_char.isupper():
            gap += random.uniform(1.0, 4.0)
        return clamp(gap, style.word_spacing_mean * 0.38, style.word_spacing_mean * 1.85)

    def should_join(self, char: str, next_char: str | None, previous_char: str | None = None) -> bool:
        if not next_char or not char.isalpha() or not next_char.isalpha():
            return False
        pair = f"{char}{next_char}".lower()
        rush = clamp(self.config.controls.exam_rush, 0.0, 1.0)
        consistency = clamp(self.config.controls.letter_consistency, 0.0, 1.0)
        probability = 0.18 + rush * 0.28 + (1.0 - consistency) * 0.16
        if pair in CONNECTABLE_PAIRS:
            probability += 0.38
        if char in OPEN_RIGHT or next_char in OPEN_LEFT:
            probability += 0.12
        if previous_char and previous_char.isspace():
            probability -= 0.08
        return random.random() < clamp(probability, 0.05, 0.82)

    def _shape_bias(self, char: str, next_char: str | None) -> float:
        bias = 0.0
        if char in WIDE_CHARS:
            bias -= random.uniform(2.0, 5.5)
        if char in NARROW_CHARS:
            bias -= random.uniform(0.5, 3.0)
        if next_char in NARROW_CHARS:
            bias -= random.uniform(0.2, 1.8)
        if next_char in WIDE_CHARS:
            bias += random.uniform(0.3, 2.8)
        return bias
