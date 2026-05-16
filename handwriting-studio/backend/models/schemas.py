from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


@dataclass
class StyleProfile:
    slant_angle: float
    avg_char_width: float
    avg_char_height: float
    baseline_y_variance: float
    word_spacing_ratio: float
    letter_spacing_tightness: float
    stroke_width: float
    pressure_proxy: float
    uppercase_ratio: float
    roundness_score: float
    writing_speed_estimate: float
    slant_std: float = 2.0

    def summary(self) -> Dict[str, Any]:
        direction = "right" if self.slant_angle > 1 else "left" if self.slant_angle < -1 else "neutral"
        pressure = "firm" if self.pressure_proxy > 45 else "medium" if self.pressure_proxy > 22 else "light"
        flow = "flowing" if self.letter_spacing_tightness < 0.35 and self.roundness_score > 0.35 else "careful"
        return {
            "slant": round(self.slant_angle, 1),
            "slant_label": f"{abs(round(self.slant_angle))} deg {direction}",
            "pressure": pressure,
            "style": flow,
            "avg_char_width": round(self.avg_char_width, 1),
            "avg_char_height": round(self.avg_char_height, 1),
            "baseline_variance": round(self.baseline_y_variance, 2),
            "word_spacing_ratio": round(self.word_spacing_ratio, 2),
        }


@dataclass
class PositionedCharacter:
    char: str
    x: float
    y: float
    image: Any
    rotation: float = 0.0
    scale: float = 1.0
    opacity: float = 1.0


@dataclass
class PageLayout:
    width: int
    height: int
    paper_preset: str
    ink_preset: str
    characters: List[PositionedCharacter] = field(default_factory=list)


class GenerationSettings(BaseModel):
    carefulness: float = Field(0.55, ge=0.0, le=1.0)
    fatigue_rate: float = Field(0.25, ge=0.0, le=1.0)
    ink_flow: float = Field(0.78, ge=0.0, le=1.0)
    margin_discipline: float = Field(0.72, ge=0.0, le=1.0)
    paper_preset: str = "ruled_notebook"
    ink_preset: str = "blue_gel"


class GenerateRequest(BaseModel):
    session_id: str
    text: str
    settings: GenerationSettings = Field(default_factory=GenerationSettings)


class RegenerateRequest(BaseModel):
    session_id: str
    page_index: int = Field(..., ge=0)
    seed: Optional[int] = None

