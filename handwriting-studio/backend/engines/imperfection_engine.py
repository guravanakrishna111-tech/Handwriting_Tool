from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class HumanImperfectionEngine:
    carefulness: float
    fatigue_rate: float
    ink_flow: float
    margin_discipline: float
    line_drifts: list[float] = field(default_factory=list)

    def line_x_drift(self, line_index: int) -> float:
        while len(self.line_drifts) <= line_index:
            prev = self.line_drifts[-1] if self.line_drifts else 0.0
            self.line_drifts.append(float(np.clip(prev + np.random.normal(0, 2 * (1 - self.margin_discipline)), -15, 15)))
        return self.line_drifts[line_index]

    def character_adjustment(self, line_index: int, word_end: bool = False) -> dict:
        size_factor = 1.0 - (self.fatigue_rate * line_index * 0.008)
        spacing_factor = 1.0 + (self.fatigue_rate * line_index * 0.005)
        size_noise = float(np.random.normal(1.0, 0.04 * (1 - self.carefulness)))
        rushed = word_end and np.random.random() < 0.15 * (1 - self.carefulness)
        return {
            "size_factor": max(0.82, size_factor * size_noise),
            "spacing_factor": min(1.22, spacing_factor),
            "compress_x": float(np.random.uniform(0.85, 0.95)) if rushed else 1.0,
            "extra_rotation": float(np.random.uniform(1, 3)) if rushed else 0.0,
            "overwrite": np.random.random() < 0.002,
        }

    def word_drifts(self, word_count: int) -> np.ndarray:
        if word_count <= 0:
            return np.array([])
        drift = np.cumsum(np.random.normal(0, 0.8 * (1 - self.carefulness), word_count))
        return np.clip(drift, -6, 6)

    def apply_line_imperfections(self, line_image: np.ndarray, line_index: int, word_count: int) -> np.ndarray:
        out = line_image.copy()
        if np.random.random() < 0.01 * (1 - self.ink_flow):
            h, w = out.shape[:2]
            x1 = np.random.randint(0, max(1, w - 12))
            y1 = np.random.randint(0, max(1, h - 8))
            y2 = min(h, y1 + np.random.randint(5, 18))
            x2 = min(w, x1 + np.random.randint(12, 42))
            out[y1:y2, x1:x2] = (out[y1:y2, x1:x2] * np.random.uniform(0.6, 0.85)).astype(np.uint8)
        if np.random.random() < 0.003 * (1 - self.ink_flow) * max(word_count, 1):
            ys, xs = np.where(out > 0)
            if xs.size:
                i = np.random.randint(0, xs.size)
                cv2.ellipse(out, (int(xs[i]), int(ys[i])), (np.random.randint(2, 5), np.random.randint(2, 5)), 0, 0, 360, 255, -1)
        return out
