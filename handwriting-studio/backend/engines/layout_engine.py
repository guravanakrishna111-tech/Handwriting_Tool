from __future__ import annotations

from typing import Dict, List

import cv2
import numpy as np

from engines.imperfection_engine import HumanImperfectionEngine
from engines.variant_engine import CharacterVariantEngine
from models.schemas import PageLayout, PositionedCharacter, StyleProfile


class WritingLayoutEngine:
    PAGE_W = 1240
    PAGE_H = 1754

    def __init__(self, variant_engine: CharacterVariantEngine):
        self.variant_engine = variant_engine

    def layout_text_on_page(self, text: str, style_profile: StyleProfile, imperfection_engine: HumanImperfectionEngine, paper_config: Dict) -> List[PageLayout]:
        preset = paper_config.get("paper_preset", "ruled_notebook")
        ink = paper_config.get("ink_preset", "blue_gel")
        margins = self._margins(preset)
        line_height = max(28, style_profile.avg_char_height * 2.2)
        word_gap = max(10, style_profile.avg_char_width * style_profile.word_spacing_ratio)
        letter_gap = max(1, style_profile.avg_char_width * style_profile.letter_spacing_tightness)
        pages = [PageLayout(self.PAGE_W, self.PAGE_H, preset, ink)]
        x = margins["left"]
        y = margins["top"]
        line_index = 0

        for para_idx, paragraph in enumerate(text.split("\n")):
            words = paragraph.split(" ")
            word_drifts = imperfection_engine.word_drifts(len(words))
            for wi, word in enumerate(words):
                if word == "":
                    x += word_gap
                    continue
                measured = self._measure_word(word, style_profile, letter_gap)
                if x + measured > self.PAGE_W - margins["right"] and x > margins["left"]:
                    x = margins["left"] + imperfection_engine.line_x_drift(line_index)
                    y += line_height
                    line_index += 1
                if y + line_height > self.PAGE_H - margins["bottom"]:
                    pages.append(PageLayout(self.PAGE_W, self.PAGE_H, preset, ink))
                    x = margins["left"]
                    y = margins["top"]
                    line_index = 0
                drift_y = float(word_drifts[wi]) if wi < len(word_drifts) else 0.0
                for ci, char in enumerate(word):
                    prev_ch = word[ci - 1] if ci > 0 else " "
                    next_ch = word[ci + 1] if ci < len(word) - 1 else " "
                    patch, meta = self.variant_engine.get_next_variant(char, prev_ch, next_ch)
                    adj = imperfection_engine.character_adjustment(line_index, ci >= len(word) - 2)
                    patch = self._scale_patch(patch, adj["size_factor"], adj["compress_x"])
                    if adj["overwrite"]:
                        patch = self._overwrite(patch)
                    h, w = patch.shape[:2]
                    pages[-1].characters.append(PositionedCharacter(char, x, y + drift_y + meta["vertical_shift"], patch, meta["rotation"] + adj["extra_rotation"]))
                    tight = -letter_gap * 0.25 if meta["left_tighten"] else 0
                    loose = letter_gap * 0.35 if meta["right_loosen"] else 0
                    x += max(2, w * 0.48 + letter_gap * adj["spacing_factor"] + tight + loose)
                x += word_gap
            x = margins["left"] + imperfection_engine.line_x_drift(line_index)
            y += line_height * (1.65 if paragraph.strip() == "" or para_idx < len(text.split("\n")) - 1 else 1)
            line_index += 1
        return pages

    def _margins(self, preset: str) -> Dict[str, float]:
        if preset == "ruled_notebook":
            return {"left": 118, "right": 70, "top": 95, "bottom": 90}
        if preset == "exam_sheet":
            return {"left": 92, "right": 72, "top": 210, "bottom": 95}
        return {"left": 90, "right": 80, "top": 95, "bottom": 95}

    def _measure_word(self, word: str, style: StyleProfile, letter_gap: float) -> float:
        return len(word) * (style.avg_char_width * 1.18 + letter_gap)

    def _scale_patch(self, patch: np.ndarray, size_factor: float, compress_x: float) -> np.ndarray:
        h, w = patch.shape[:2]
        return cv2.resize(patch, (max(1, int(w * size_factor * compress_x)), max(1, int(h * size_factor))), interpolation=cv2.INTER_LINEAR)

    def _overwrite(self, patch: np.ndarray) -> np.ndarray:
        out = patch.copy()
        ghost = np.zeros_like(out)
        ghost[1:, 1:] = patch[:-1, :-1]
        return np.maximum(out, (ghost * np.random.uniform(0.3, 0.5)).astype(np.uint8))

