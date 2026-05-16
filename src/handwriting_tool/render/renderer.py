from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from handwriting_tool.config import AppConfig
from handwriting_tool.render.presets import paper_preset
from handwriting_tool.render.spacing import HumanSpacingEngine
from handwriting_tool.render.strokes import StrokeWritingEngine
from handwriting_tool.types import LinePlan, PagePlan, SpanPlan, StyleProfile
from handwriting_tool.utils import clamp


class HandwritingRenderer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.stroke_engine = StrokeWritingEngine(config)
        self.spacing_engine = HumanSpacingEngine(config)

    def render_page(self, page: PagePlan, style: StyleProfile) -> Image.Image:
        layout = self.config.layout
        canvas = self._make_paper(layout.page_width_px, layout.page_height_px)

        y_cursor = layout.margin_top_px
        for line in page.lines:
            line_img = self.render_line(line, style, layout.page_width_px - layout.margin_right_px)
            rotated = line_img.rotate(line.line_angle_deg, resample=Image.Resampling.BICUBIC, expand=False)
            canvas.alpha_composite(rotated, (0, max(0, y_cursor + line.y_offset_px)))
            y_cursor += style.line_height

        skewed = canvas.rotate(random.gauss(0.0, style.page_skew_deg), resample=Image.Resampling.BICUBIC, expand=False)
        skewed = self._add_scan_shadow(skewed)
        return skewed.convert("RGB")

    def render_line(self, line: LinePlan, style: StyleProfile, max_width: int) -> Image.Image:
        width = max_width
        height = max(style.line_height * 2, 180)
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        x_cursor = line.indent_px
        baseline_y = style.line_height

        for span in line.spans:
            if not span.text:
                continue

            if span.kind == "correction" and span.rewrite_mode != "after":
                draw_y = baseline_y - 34 + span.y_offset_px
            else:
                draw_y = baseline_y + span.y_offset_px

            chars = list(span.text)
            previous_char: str | None = None
            for char_index, char in enumerate(chars):
                if char == "\n":
                    continue
                next_char = self._next_visible_char(chars, char_index)
                if (
                    char in ".,;:!?"
                    and self.config.runtime.preserve_exact_text is False
                    and random.random() < self.config.imperfections.missed_punctuation_probability
                ):
                    x_cursor += max(4, int(style.character_spacing_mean))
                    continue

                char_img, advance = self._render_character(char, span, style)
                spacing = self.spacing_engine.adjustment(previous_char, char, next_char, advance, style, line, char_index)
                point_index = int(clamp((x_cursor / max(width, 1)) * (len(line.baseline_points) - 1), 0, len(line.baseline_points) - 1))
                y_offset = int(line.baseline_points[point_index])
                paste_x = int(x_cursor - spacing.overlap_px)
                paste_y = int(draw_y + y_offset + spacing.y_rhythm_px - char_img.height * 0.65)
                layer.alpha_composite(char_img, (paste_x, paste_y))
                if spacing.join and previous_char and not previous_char.isspace():
                    self._draw_connector(layer, int(x_cursor - spacing.overlap_px), int(draw_y + y_offset + spacing.y_rhythm_px), style)
                x_cursor += spacing.advance
                previous_char = char

            if span.cross_out:
                self._draw_cross_out(layer, x_cursor, draw_y)

            if span.kind == "mistake" and span.rewrite_mode == "after":
                x_cursor += int(style.word_spacing_mean * 0.7)

        return layer

    def _render_character(self, char: str, span: SpanPlan, style: StyleProfile) -> tuple[Image.Image, int]:
        font_size = max(20, int(style.base_font_size * span.size_scale * random.uniform(0.92, 1.08)))
        font = self._load_font(style.font_path, font_size)
        return self.stroke_engine.render_character(char, span, style, font)

    def _draw_cross_out(self, layer: Image.Image, x_cursor: int, draw_y: int) -> None:
        draw = ImageDraw.Draw(layer)
        width = random.randint(24, 58)
        y = int(draw_y - random.randint(8, 16))
        start_x = max(0, x_cursor - width)
        end_x = min(layer.width - 1, x_cursor)
        wobble = random.randint(-3, 3)
        draw.line((start_x, y, end_x, y + wobble), fill=(25, 25, 25, 160), width=2)
        if random.random() < 0.4:
            draw.line((start_x, y + 5, end_x, y + 2 + wobble), fill=(25, 25, 25, 110), width=1)

    def _draw_connector(self, layer: Image.Image, x_cursor: int, baseline_y: int, style: StyleProfile) -> None:
        draw = ImageDraw.Draw(layer, "RGBA")
        width = max(1, int(random.gauss(style.stroke_width_mean, style.stroke_width_std * 0.3)))
        length = random.randint(6, 18)
        y = baseline_y - random.randint(18, 30)
        points = [
            (x_cursor - length, y + random.randint(-2, 2)),
            (x_cursor - length // 2, y + random.randint(-4, 3)),
            (x_cursor + random.randint(1, 5), y + random.randint(-2, 2)),
        ]
        draw.line(points, fill=(28, 52, 115, random.randint(60, 120)), width=width, joint="curve")

    def _next_visible_char(self, chars: list[str], index: int) -> str | None:
        for char in chars[index + 1 :]:
            if char != "\n":
                return char
        return None

    def _make_paper(self, width: int, height: int) -> Image.Image:
        preset = paper_preset(self.config.layout.paper_preset)
        base = np.zeros((height, width, 3), dtype=np.float32)
        for channel, value in enumerate(preset.base_rgb):
            base[:, :, channel] = value
        noise = np.random.normal(0.0, 255 * max(self.config.layout.background_noise, preset.grain), size=(height, width, 1))
        vignette = self._vignette(width, height, preset.edge_shadow)
        rgb = np.clip(base + noise - vignette[:, :, None], 0, 255).astype(np.uint8)
        paper = Image.fromarray(rgb, mode="RGB").convert("RGBA")
        draw = ImageDraw.Draw(paper, "RGBA")

        if preset.line_rgb:
            y = self.config.layout.margin_top_px
            while y < height - self.config.layout.margin_bottom_px:
                draw.line((0, y, width, y), fill=(*preset.line_rgb, preset.line_alpha), width=2)
                y += preset.line_gap_px
        if preset.margin_rgb:
            x = self.config.layout.margin_left_px - 46
            draw.line((x, 0, x + random.randint(-2, 2), height), fill=(*preset.margin_rgb, preset.margin_alpha), width=3)

        return paper

    def _vignette(self, width: int, height: int, strength: float) -> np.ndarray:
        y = np.linspace(-1, 1, height)
        x = np.linspace(-1, 1, width)
        xx, yy = np.meshgrid(x, y)
        distance = np.clip(np.sqrt(xx * xx + yy * yy), 0, 1)
        return (distance**2) * 255 * strength

    def _add_scan_shadow(self, image: Image.Image) -> Image.Image:
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow, "RGBA")
        width, height = image.size
        for inset in range(0, 42, 3):
            alpha = max(0, 30 - inset)
            draw.rectangle((inset, inset, width - inset, height - inset), outline=(62, 45, 30, alpha), width=2)
        curled = Image.new("RGBA", image.size, (0, 0, 0, 0))
        curl_draw = ImageDraw.Draw(curled, "RGBA")
        curl_draw.pieslice((width - 190, -40, width + 42, 190), 90, 180, fill=(255, 255, 255, 26))
        composed = Image.alpha_composite(image.convert("RGBA"), shadow)
        return Image.alpha_composite(composed, curled)

    def _load_font(self, font_path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if font_path:
            candidate = Path(font_path)
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size=size)
        return ImageFont.load_default()
