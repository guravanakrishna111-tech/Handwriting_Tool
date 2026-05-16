from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from models.schemas import StyleProfile


class CharacterVariantEngine:
    round_chars = set("oceaOQCG")
    ascenders = set("hklbdftABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def __init__(self, variants: Dict[str, List[np.ndarray]], style_profile: StyleProfile):
        self.variants = variants
        self.style = style_profile
        self.usage_counts = defaultdict(int)
        self.queues = {k: deque(range(len(v))) for k, v in variants.items() if v}

    def get_next_variant(self, char: str, context_prev: Optional[str], context_next: Optional[str]) -> Tuple[np.ndarray, dict]:
        key = char if char in self.variants else self._fallback_key(char)
        queue = self.queues.setdefault(key, deque(range(len(self.variants[key]))))
        idx = queue.popleft()
        queue.append(idx)
        self.usage_counts[key] += 1
        patch = self.variants[key][idx].copy()
        meta = {
            "left_tighten": context_prev in self.round_chars,
            "right_loosen": context_next in self.ascenders,
            "word_end_lean": context_next in (None, " ", "\n", ".", ",", ";", ":", "!", "?"),
            "vertical_shift": float(np.random.normal(0, max(0.4, self.style.baseline_y_variance * 0.3))),
            "rotation": float(np.random.normal(0, self.style.slant_std)),
            "scale": float(np.random.uniform(0.93, 1.07)),
        }
        if meta["word_end_lean"]:
            meta["rotation"] += float(np.random.uniform(0.5, 1.5))
        patch = self._perturb(patch, meta)
        return patch, meta

    def _fallback_key(self, char: str) -> str:
        if char.isspace():
            return " "
        if char.isupper() and "A" in self.variants:
            return "A"
        if char.isdigit() and "1" in self.variants:
            return "1"
        return next((k for k in "etaoinshrdlucm" if k in self.variants), next(iter(self.variants)))

    def _perturb(self, patch: np.ndarray, meta: dict) -> np.ndarray:
        h, w = patch.shape[:2]
        sx = float(np.random.uniform(0.96, 1.04))
        sy = meta["scale"]
        resized = cv2.resize(patch, (max(1, int(w * sx)), max(1, int(h * sy))), interpolation=cv2.INTER_LINEAR)
        matrix = cv2.getRotationMatrix2D((resized.shape[1] / 2, resized.shape[0] / 2), meta["rotation"], 1.0)
        return cv2.warpAffine(resized, matrix, (resized.shape[1], resized.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

