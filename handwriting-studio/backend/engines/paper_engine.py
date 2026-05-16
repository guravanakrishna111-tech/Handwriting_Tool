from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

from models.schemas import PageLayout
from utils.image_utils import rotate_image_alpha


class PaperCompositionEngine:
    colors = {
        "ruled_notebook": (250, 250, 242),
        "plain_a4": (255, 255, 255),
        "exam_sheet": (240, 244, 255),
        "vintage": (245, 240, 220),
    }
    inks = {
        "blue_gel": (26, 58, 110, 245),
        "black_ball": (10, 10, 10, 235),
        "fountain": (28, 28, 58, 242),
        "pencil": (74, 74, 74, 205),
    }

    def render_page(self, page_layout: PageLayout, paper_preset: str, ink_preset: str) -> Image.Image:
        base = Image.new("RGB", (page_layout.width, page_layout.height), self.colors.get(paper_preset, (255, 255, 255)))
        base = self._texture(base, paper_preset)
        draw = ImageDraw.Draw(base)
        if paper_preset == "ruled_notebook":
            self._ruled(draw, page_layout.width, page_layout.height, margin_x=80)
        elif paper_preset == "exam_sheet":
            self._exam(draw, page_layout.width, page_layout.height)
        elif paper_preset == "vintage":
            self._vintage(draw, page_layout.width, page_layout.height)

        page = base.convert("RGBA")
        for positioned in page_layout.characters:
            glyph = self._tint(positioned.image, ink_preset)
            glyph = rotate_image_alpha(glyph, positioned.rotation)
            page.alpha_composite(Image.fromarray(glyph), (int(positioned.x), int(positioned.y)))
        page = page.filter(ImageFilter.GaussianBlur(0.28))
        return page.convert("RGB")

    def _texture(self, image: Image.Image, preset: str) -> Image.Image:
        arr = np.asarray(image).astype(np.float32)
        h, w = arr.shape[:2]
        rng = np.random.default_rng()
        grain = gaussian_filter(rng.normal(0, 1, (h, w)), sigma=9)
        grain = grain / max(float(np.std(grain)), 1e-5) * (3.5 if preset == "vintage" else 2.2)
        yy, xx = np.mgrid[0:h, 0:w]
        dist = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        vignette = 1 - np.clip((dist - 0.35) * 0.06, 0, 0.07)
        lamp = 1 + np.linspace(0.018, -0.018, w)[None, :]
        arr = np.clip((arr + grain[:, :, None]) * vignette[:, :, None] * lamp[:, :, None], 0, 255)
        return Image.fromarray(arr.astype(np.uint8), "RGB")

    def _ruled(self, draw: ImageDraw.ImageDraw, w: int, h: int, margin_x: int = 80) -> None:
        for y in range(112, h - 70, 28):
            draw.line((0, y, w, y), fill=(174, 199, 230), width=1)
        draw.line((margin_x, 0, margin_x, h), fill=(222, 113, 104), width=2)

    def _exam(self, draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
        draw.rectangle((55, 42, w - 55, 168), outline=(115, 141, 178), width=2)
        draw.line((55, 105, w - 55, 105), fill=(150, 170, 200), width=1)
        for x in (360, 760):
            draw.line((x, 42, x, 168), fill=(150, 170, 200), width=1)
        for y in range(220, h - 80, 30):
            draw.line((70, y, w - 70, y), fill=(175, 198, 229), width=1)

    def _vintage(self, draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
        for y in range(120, h - 90, 30):
            draw.line((80, y, w - 80, y), fill=(218, 202, 158), width=1)

    def _tint(self, mask: np.ndarray, ink_preset: str) -> np.ndarray:
        alpha = np.clip(mask, 0, 255).astype(np.uint8)
        color = self.inks.get(ink_preset, self.inks["blue_gel"])
        if ink_preset == "blue_gel":
            alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
        elif ink_preset == "black_ball":
            alpha = (alpha.astype(np.float32) * np.random.uniform(0.86, 1.0, alpha.shape)).clip(0, 255).astype(np.uint8)
        elif ink_preset == "fountain":
            alpha = cv2.dilate(alpha, np.ones((2, 2), np.uint8), iterations=1)
        elif ink_preset == "pencil":
            noise = np.random.normal(0, 18, alpha.shape)
            alpha = np.clip(alpha.astype(np.float32) * 0.85 + noise, 0, 225).astype(np.uint8)
        rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
        rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2] = color[:3]
        rgba[:, :, 3] = np.minimum(alpha, color[3])
        return rgba

