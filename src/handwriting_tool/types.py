from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StyleProfile:
    reference_path: Path
    font_path: str | None
    base_font_size: int
    line_height: int
    character_spacing_mean: float
    character_spacing_std: float
    word_spacing_mean: float
    word_spacing_std: float
    baseline_jitter: float
    stroke_darkness_mean: float
    stroke_darkness_std: float
    stroke_width_mean: float
    stroke_width_std: float
    tilt_mean_deg: float
    tilt_std_deg: float
    page_skew_deg: float
    line_left_indent_jitter: int
    average_word_gap_px: float = 12.0
    punctuation_drop: float = 0.0
    pressure_variance: float = 0.35
    correction_tendency: float = 0.2
    handedness: str = "right"


@dataclass
class SpanPlan:
    text: str
    kind: str = "text"
    cross_out: bool = False
    rewrite_mode: str | None = None
    y_offset_px: int = 0
    size_scale: float = 1.0
    tilt_deg: float = 0.0
    darkness_scale: float = 1.0
    visual_dropout: bool = False
    overwrite: bool = False


@dataclass
class LinePlan:
    source_text: str
    spans: list[SpanPlan]
    baseline_points: list[float]
    indent_px: int
    y_offset_px: int = 0
    line_angle_deg: float = 0.0
    fatigue: float = 0.0


@dataclass
class PagePlan:
    page_index: int
    lines: list[LinePlan] = field(default_factory=list)


@dataclass
class DocumentPlan:
    pages: list[PagePlan] = field(default_factory=list)
