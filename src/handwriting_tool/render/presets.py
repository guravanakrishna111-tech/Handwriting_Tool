from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperPreset:
    name: str
    base_rgb: tuple[int, int, int]
    grain: float
    line_rgb: tuple[int, int, int] | None = None
    line_alpha: int = 34
    line_gap_px: int = 96
    margin_rgb: tuple[int, int, int] | None = None
    margin_alpha: int = 42
    edge_shadow: float = 0.16


@dataclass(frozen=True)
class InkPreset:
    name: str
    rgb: tuple[int, int, int]
    spread_radius: float
    pressure_gain: float
    fade: float


PAPER_PRESETS: dict[str, PaperPreset] = {
    "ruled": PaperPreset(
        name="Ruled notebook",
        base_rgb=(248, 243, 231),
        grain=0.018,
        line_rgb=(92, 135, 178),
        line_alpha=30,
        margin_rgb=(204, 92, 92),
        margin_alpha=34,
    ),
    "plain_a4": PaperPreset(name="Plain A4", base_rgb=(250, 249, 244), grain=0.012, edge_shadow=0.09),
    "exam_sheet": PaperPreset(
        name="Exam sheet",
        base_rgb=(246, 248, 238),
        grain=0.014,
        line_rgb=(112, 151, 126),
        line_alpha=24,
        line_gap_px=112,
        margin_rgb=(112, 151, 126),
        margin_alpha=26,
    ),
    "vintage": PaperPreset(
        name="Vintage paper",
        base_rgb=(239, 224, 190),
        grain=0.024,
        line_rgb=(139, 107, 67),
        line_alpha=20,
        edge_shadow=0.22,
    ),
}


INK_PRESETS: dict[str, InkPreset] = {
    "blue_gel": InkPreset(name="Blue gel pen", rgb=(27, 63, 143), spread_radius=0.42, pressure_gain=1.15, fade=0.05),
    "black_ball": InkPreset(name="Black ball pen", rgb=(30, 28, 25), spread_radius=0.22, pressure_gain=0.9, fade=0.1),
    "fountain": InkPreset(name="Fountain pen", rgb=(22, 35, 82), spread_radius=0.72, pressure_gain=1.35, fade=0.03),
    "pencil": InkPreset(name="Pencil", rgb=(86, 82, 76), spread_radius=0.18, pressure_gain=0.58, fade=0.2),
}


def paper_preset(key: str) -> PaperPreset:
    return PAPER_PRESETS.get(key, PAPER_PRESETS["ruled"])


def ink_preset(key: str) -> InkPreset:
    return INK_PRESETS.get(key, INK_PRESETS["blue_gel"])
