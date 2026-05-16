from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from handwriting_tool.config import AppConfig
from handwriting_tool.render.presets import ink_preset
from handwriting_tool.types import SpanPlan, StyleProfile
from handwriting_tool.utils import clamp


@dataclass
class StrokeTrajectory:
    points: list[tuple[float, float]]
    pressure: list[float]
    lift_after: bool = True


class StrokeWritingEngine:
    """Converts character prototypes into noisy pen trajectories.

    The prototype mask is only a guide. The visible mark is redrawn as multiple
    pressure-varying vector strokes, so repeated characters do not share an
    identical bitmap.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def render_character(
        self,
        char: str,
        span: SpanPlan,
        style: StyleProfile,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> tuple[Image.Image, int]:
        if char.isspace():
            advance = int(random.gauss(style.word_spacing_mean, style.word_spacing_std))
            return Image.new("RGBA", (max(8, advance), style.line_height), (0, 0, 0, 0)), max(6, advance)

        font_size = max(20, int(style.base_font_size * span.size_scale * random.uniform(0.94, 1.06)))
        if hasattr(font, "path"):
            try:
                font = ImageFont.truetype(str(font.path), size=font_size)  # type: ignore[attr-defined]
            except OSError:
                pass

        mask, bbox = self._prototype_mask(char, font, font_size)
        trajectories = self._trace_mask(mask, style, span)
        ink = ink_preset(self.config.controls.ink_preset)
        layer = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        for trajectory in trajectories:
            if len(trajectory.points) < 2:
                continue
            for idx in range(1, len(trajectory.points)):
                p0 = trajectory.points[idx - 1]
                p1 = trajectory.points[idx]
                pressure = trajectory.pressure[min(idx, len(trajectory.pressure) - 1)]
                width = max(
                    1,
                    int(
                        random.gauss(style.stroke_width_mean, style.stroke_width_std * 0.4)
                        * pressure
                        * ink.pressure_gain
                        * span.darkness_scale
                    ),
                )
                alpha = int(
                    255
                    * clamp(style.stroke_darkness_mean * span.darkness_scale, 0.05, 0.78)
                    * random.uniform(0.74, 1.12)
                )
                if span.visual_dropout or random.random() < self.config.imperfections.faded_stroke_probability * ink.fade:
                    alpha = int(alpha * random.uniform(0.35, 0.72))
                draw.line((p0[0], p0[1], p1[0], p1[1]), fill=(*ink.rgb, alpha), width=width, joint="curve")

        if span.overwrite:
            ghost = layer.transform(
                layer.size,
                Image.Transform.AFFINE,
                (1, 0, random.uniform(-2.4, 2.4), 0, 1, random.uniform(-1.5, 1.5)),
                resample=Image.Resampling.BICUBIC,
            )
            layer = ImageChops.lighter(layer, ghost)

        if random.random() < self.config.imperfections.ink_blot_probability:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=ink.spread_radius + random.uniform(0.1, 0.6)))

        layer = self._crop_to_ink(layer)
        tilt = style.tilt_mean_deg + span.tilt_deg + random.gauss(0.0, style.tilt_std_deg / 5.0)
        shear = math.tan(math.radians(tilt * 0.42))
        transformed = layer.transform(
            (int(layer.width + abs(shear) * layer.height), layer.height),
            Image.Transform.AFFINE,
            (1, shear, 0, 0, 1, 0),
            resample=Image.Resampling.BICUBIC,
        )
        transformed = transformed.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=True)
        advance = max(8, transformed.width + int(random.gauss(style.character_spacing_mean, style.character_spacing_std)))
        return transformed, advance

    def _crop_to_ink(self, layer: Image.Image) -> Image.Image:
        bbox = layer.getbbox()
        if not bbox:
            return layer
        left, top, right, bottom = bbox
        padding = 8
        box = (
            max(0, left - padding),
            max(0, top - padding),
            min(layer.width, right + padding),
            min(layer.height, bottom + padding),
        )
        return layer.crop(box)

    def _prototype_mask(
        self,
        char: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        font_size: int,
    ) -> tuple[Image.Image, tuple[int, int, int, int]]:
        bbox = font.getbbox(char)
        width = max(18, bbox[2] - bbox[0] + 28)
        height = max(font_size * 2, bbox[3] - bbox[1] + 30)
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.text((14 - bbox[0], 10 - bbox[1]), char, fill=255, font=font)
        return mask, bbox

    def _trace_mask(self, mask: Image.Image, style: StyleProfile, span: SpanPlan) -> list[StrokeTrajectory]:
        array = np.asarray(mask, dtype=np.uint8)
        ys, xs = np.where(array > 20)
        if xs.size == 0:
            return []

        consistency = clamp(self.config.controls.letter_consistency, 0.05, 1.0)
        rush = clamp(self.config.controls.exam_rush, 0.0, 1.0)
        shakiness = (1.12 - consistency) * (0.7 + rush * 0.8)
        rows = sorted(set(int(y) for y in np.linspace(ys.min(), ys.max(), num=max(5, min(18, mask.height // 5)))))
        trajectories: list[StrokeTrajectory] = []

        for y in rows:
            row = np.where(array[y] > 20)[0]
            if row.size < 2:
                continue
            segments = self._row_segments(row)
            for left, right in segments:
                if right - left < 3:
                    continue
                point_count = max(3, min(9, (right - left) // 5))
                points = []
                pressures = []
                for idx in range(point_count):
                    t = idx / max(1, point_count - 1)
                    x = left + (right - left) * t
                    wave = math.sin(t * math.pi) * random.uniform(-1.4, 1.4)
                    points.append((x + random.gauss(0, shakiness), y + wave + random.gauss(0, shakiness * 0.65)))
                    pressures.append(clamp(random.gauss(1.0, style.pressure_variance * 0.22), 0.45, 1.7))
                if random.random() < rush * 0.35:
                    points = points[::2] or points
                    pressures = pressures[: len(points)]
                trajectories.append(StrokeTrajectory(points=points, pressure=pressures))

        if not trajectories:
            trajectories.append(
                StrokeTrajectory(
                    points=[(float(xs.min()), float(ys.mean())), (float(xs.max()), float(ys.mean()))],
                    pressure=[1.0, 1.0],
                )
            )
        return trajectories

    def _row_segments(self, row: np.ndarray) -> list[tuple[int, int]]:
        breaks = np.where(np.diff(row) > 2)[0]
        starts = [0, *[int(idx + 1) for idx in breaks]]
        ends = [*[int(idx) for idx in breaks], len(row) - 1]
        return [(int(row[start]), int(row[end])) for start, end in zip(starts, ends)]
