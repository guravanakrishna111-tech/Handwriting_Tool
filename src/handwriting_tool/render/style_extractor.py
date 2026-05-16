from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from handwriting_tool.config import AppConfig
from handwriting_tool.render.fonts import choose_reference_font
from handwriting_tool.types import StyleProfile
from handwriting_tool.utils import clamp


class ReferenceStyleExtractor:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def extract(self, reference_path: str | Path) -> StyleProfile:
        path = Path(reference_path)
        image = Image.open(path).convert("L")
        array = np.asarray(image, dtype=np.float32) / 255.0

        ink_mask = array < 0.85
        ink_pixels = array[ink_mask]
        darkness_mean = float(1.0 - ink_pixels.mean()) if ink_pixels.size else self.config.style.stroke_darkness_mean
        darkness_std = float(ink_pixels.std()) if ink_pixels.size else self.config.style.stroke_darkness_std
        pressure_variance = float(clamp(darkness_std * 4.0, 0.12, 0.75))

        binary = ink_mask.astype(np.float32)
        horizontal_density = binary.mean(axis=1)
        line_rows = np.where(horizontal_density > horizontal_density.mean() + horizontal_density.std() * 0.6)[0]
        if line_rows.size > 1:
            spacing = np.diff(line_rows)
            spacing = spacing[(spacing > 5) & (spacing < 200)]
            line_height = int(np.median(spacing)) if spacing.size else self.config.style.line_height
        else:
            line_height = self.config.style.line_height

        baseline_jitter = float(self._estimate_baseline_jitter(binary))
        tilt_mean = float(self._estimate_slant(binary))

        stroke_width = self._estimate_stroke_width(binary)
        font_path = choose_reference_font(self.config.runtime.prefer_handwriting_fonts)

        style_cfg = self.config.style
        return StyleProfile(
            reference_path=path,
            font_path=font_path,
            base_font_size=style_cfg.base_font_size,
            line_height=max(72, line_height),
            character_spacing_mean=style_cfg.character_spacing_mean,
            character_spacing_std=style_cfg.character_spacing_std,
            word_spacing_mean=style_cfg.word_spacing_mean,
            word_spacing_std=style_cfg.word_spacing_std,
            baseline_jitter=clamp(baseline_jitter or style_cfg.baseline_jitter, 2.0, 16.0),
            stroke_darkness_mean=clamp(darkness_mean, 0.05, 0.4),
            stroke_darkness_std=clamp(darkness_std, 0.02, 0.15),
            stroke_width_mean=clamp(stroke_width, 1.0, 4.0),
            stroke_width_std=style_cfg.stroke_width_std,
            tilt_mean_deg=clamp(tilt_mean, -12.0, 12.0),
            tilt_std_deg=style_cfg.tilt_std_deg,
            page_skew_deg=style_cfg.page_skew_deg,
            line_left_indent_jitter=style_cfg.line_left_indent_jitter,
            average_word_gap_px=style_cfg.word_spacing_mean,
            punctuation_drop=self.config.imperfections.missed_punctuation_probability,
            pressure_variance=pressure_variance,
            correction_tendency=self.config.imperfections.correction_probability,
            handedness=self.config.controls.handedness,
        )

    def _estimate_baseline_jitter(self, binary: np.ndarray) -> float:
        positions = []
        for start in range(0, binary.shape[1], 32):
            end = min(binary.shape[1], start + 32)
            column_block = binary[:, start:end]
            if column_block.sum() < 8:
                continue
            rows = np.where(column_block.sum(axis=1) > 0)[0]
            if rows.size:
                positions.append(float(rows.max()))
        if len(positions) < 3:
            return self.config.style.baseline_jitter
        return np.std(positions) / 3.0

    def _estimate_slant(self, binary: np.ndarray) -> float:
        if binary.sum() < 20:
            return self.config.style.tilt_mean_deg
        y, x = np.where(binary > 0)
        x = x - x.mean()
        y = y - y.mean()
        covariance = np.cov(np.stack([x, y]))
        eigvals, eigvecs = np.linalg.eigh(covariance)
        axis = eigvecs[:, np.argmax(eigvals)]
        angle = np.degrees(np.arctan2(axis[1], axis[0])) - 90.0
        return angle * 0.35

    def _estimate_stroke_width(self, binary: np.ndarray) -> float:
        if binary.sum() < 20:
            return self.config.style.stroke_width_mean
        vertical = np.abs(np.diff(binary, axis=0)).mean()
        horizontal = np.abs(np.diff(binary, axis=1)).mean()
        edge_density = max(vertical + horizontal, 1e-3)
        return float(clamp(1.8 / edge_density, 1.0, 4.0))
