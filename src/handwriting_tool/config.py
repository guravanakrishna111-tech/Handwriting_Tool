from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StyleConfig:
    base_font_size: int = 48
    line_height: int = 96
    character_spacing_mean: float = 1.0
    character_spacing_std: float = 1.8
    word_spacing_mean: float = 12.0
    word_spacing_std: float = 4.0
    baseline_jitter: float = 6.0
    stroke_darkness_mean: float = 0.12
    stroke_darkness_std: float = 0.08
    stroke_width_mean: float = 2.0
    stroke_width_std: float = 0.8
    tilt_mean_deg: float = -3.0
    tilt_std_deg: float = 4.5
    page_skew_deg: float = 0.8
    line_left_indent_jitter: int = 10


@dataclass
class LayoutConfig:
    dpi: int = 300
    page_width_px: int = 2480
    page_height_px: int = 3508
    margin_left_px: int = 220
    margin_right_px: int = 180
    margin_top_px: int = 220
    margin_bottom_px: int = 220
    lines_per_page_hint: int = 28
    max_chars_per_line_hint: int = 52
    background_noise: float = 0.015
    paper_preset: str = "ruled"
    margin_discipline: float = 0.62


@dataclass
class ImperfectionConfig:
    enabled: bool = True
    typo_probability: float = 0.05
    correction_probability: float = 0.9
    uncorrected_error_probability: float = 0.02
    crossout_probability: float = 0.75
    rewrite_above_probability: float = 0.45
    repeated_letter_probability: float = 0.15
    missing_letter_probability: float = 0.2
    swapped_letter_probability: float = 0.35
    punctuation_offset_px: int = 4
    line_misalignment_px: int = 12
    size_jitter_std: float = 0.08
    tilt_jitter_std_deg: float = 3.0
    darkness_jitter_std: float = 0.08
    line_baseline_drift_px: float = 8.0
    ink_blot_probability: float = 0.02
    missed_punctuation_probability: float = 0.0
    overwritten_letter_probability: float = 0.03
    faded_stroke_probability: float = 0.035
    fatigue_progression: float = 0.25


@dataclass
class StudioControlsConfig:
    writing_carefulness: float = 0.62
    exam_rush: float = 0.38
    writer_fatigue: float = 0.35
    ink_flow: float = 0.58
    letter_consistency: float = 0.48
    margin_discipline: float = 0.62
    mood_variation: float = 0.25
    handedness: str = "right"
    ink_preset: str = "blue_gel"


@dataclass
class RuntimeConfig:
    prefer_handwriting_fonts: bool = True
    export_intermediate_pngs: bool = False
    output_format: str = "pdf"
    preserve_exact_text: bool = True
    enable_ocr_check: bool = False


@dataclass
class AppConfig:
    seed: int = 7
    style: StyleConfig = field(default_factory=StyleConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    imperfections: ImperfectionConfig = field(default_factory=ImperfectionConfig)
    controls: StudioControlsConfig = field(default_factory=StudioControlsConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)


def _deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _dataclass_to_dict(config: AppConfig) -> dict[str, Any]:
    return {
        "seed": config.seed,
        "style": vars(config.style),
        "layout": vars(config.layout),
        "imperfections": vars(config.imperfections),
        "controls": vars(config.controls),
        "runtime": vars(config.runtime),
    }


def load_config(path: str | Path | None = None) -> AppConfig:
    config = AppConfig()
    if path is None:
        return config

    raw = _load_mapping(Path(path))

    merged = _deep_merge(_dataclass_to_dict(config), raw)
    return AppConfig(
        seed=merged["seed"],
        style=StyleConfig(**merged["style"]),
        layout=LayoutConfig(**merged["layout"]),
        imperfections=ImperfectionConfig(**merged["imperfections"]),
        controls=StudioControlsConfig(**merged.get("controls", {})),
        runtime=RuntimeConfig(**merged["runtime"]),
    )


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        import json

        return json.loads(text)

    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            continue

        key, raw_value = stripped.split(":", 1)
        value = raw_value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        current = stack[-1][1]
        if not value:
            nested: dict[str, Any] = {}
            current[key] = nested
            stack.append((indent, nested))
            continue

        current[key] = _parse_scalar(value)

    return root


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("'\"")
