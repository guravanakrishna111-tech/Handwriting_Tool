from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import cv2
import numpy as np
from skimage.metrics import structural_similarity

from models.schemas import StyleProfile
from utils.image_utils import binarize_strokes, connected_components, elastic_distort, normalize_patch, read_image, split_text_lines


class CharacterExtractor:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:!?'-()"

    def extract_character_variants(self, image_path: str, style_profile: StyleProfile) -> Dict[str, List[np.ndarray]]:
        binary = binarize_strokes(read_image(image_path))
        patches: Dict[str, List[np.ndarray]] = defaultdict(list)
        for y1, y2 in split_text_lines(binary):
            line = binary[y1:y2, :]
            for word in self._segment_words(line, style_profile):
                chars = self._segment_characters(word, style_profile)
                for char_patch in chars:
                    normalized = normalize_patch(self._perspective_normalize(char_patch), 64)
                    identity = self._estimate_identity(normalized, style_profile)
                    if identity and len(patches[identity]) < 12:
                        patches[identity].append(normalized)

        grouped = {ch: self._group_similar(vals)[:5] for ch, vals in patches.items() if vals}
        pool = [p for vals in grouped.values() for p in vals]
        if not pool:
            pool = [self._fallback_patch()]

        for idx, ch in enumerate(self.alphabet):
            if ch not in grouped:
                grouped[ch] = [pool[idx % len(pool)].copy()]
            while len(grouped[ch]) < 2:
                grouped[ch].append(self._synthetic_variant(grouped[ch][0]))
            grouped[ch] = grouped[ch][:5]
        grouped[" "] = [np.zeros((64, 32), dtype=np.uint8)]
        grouped["\n"] = [np.zeros((1, 1), dtype=np.uint8)]
        return grouped

    def _segment_words(self, line: np.ndarray, style: StyleProfile) -> List[np.ndarray]:
        projection = (line > 0).sum(axis=0)
        active_cols = np.where(projection > 0)[0]
        if active_cols.size == 0:
            return []
        gaps = []
        start = int(active_cols[0])
        last = start
        threshold = max(10, int(style.avg_char_width * style.word_spacing_ratio * 0.65))
        for col in active_cols[1:]:
            if col - last > threshold:
                gaps.append((start, last + 1))
                start = int(col)
            last = int(col)
        gaps.append((start, last + 1))
        return [line[:, max(0, a - 2) : min(line.shape[1], b + 2)] for a, b in gaps if b - a > 3]

    def _segment_characters(self, word: np.ndarray, style: StyleProfile) -> List[np.ndarray]:
        boxes = connected_components(word)
        if not boxes:
            return []
        boxes = self._merge_marks(boxes, style)
        patches: List[np.ndarray] = []
        for x, y, w, h, area in boxes:
            if w > style.avg_char_width * 1.7:
                patches.extend(self._watershed_split(word[y : y + h, x : x + w], style))
            else:
                patches.append(word[max(0, y - 2) : min(word.shape[0], y + h + 2), max(0, x - 2) : min(word.shape[1], x + w + 2)])
        return patches

    def _merge_marks(self, boxes, style):
        boxes = sorted(boxes, key=lambda b: b[0])
        merged = []
        used = set()
        for i, box in enumerate(boxes):
            if i in used:
                continue
            x, y, w, h, area = box
            if area < style.avg_char_width * style.avg_char_height * 0.08:
                below = [j for j, b in enumerate(boxes) if j != i and abs((b[0] + b[2] / 2) - (x + w / 2)) < style.avg_char_width * 0.45 and b[1] > y]
                if below:
                    j = below[0]
                    bx, by, bw, bh, ba = boxes[j]
                    nx, ny = min(x, bx), min(y, by)
                    merged.append((nx, ny, max(x + w, bx + bw) - nx, max(y + h, by + bh) - ny, area + ba))
                    used.add(j)
                    continue
            merged.append(box)
        return merged

    def _watershed_split(self, patch: np.ndarray, style: StyleProfile) -> List[np.ndarray]:
        cols = (patch > 0).sum(axis=0)
        if cols.size == 0:
            return [patch]
        low = np.where(cols <= max(1, cols.max() * 0.18))[0]
        cuts = [c for c in low if style.avg_char_width * 0.45 < c < patch.shape[1] - style.avg_char_width * 0.25]
        if not cuts:
            estimated = max(2, int(round(patch.shape[1] / max(style.avg_char_width, 8))))
            cuts = [int(i * patch.shape[1] / estimated) for i in range(1, estimated)]
        pieces, prev = [], 0
        for cut in cuts[:3]:
            if cut - prev > 4:
                pieces.append(patch[:, prev:cut])
            prev = cut
        if patch.shape[1] - prev > 4:
            pieces.append(patch[:, prev:])
        return pieces or [patch]

    def _perspective_normalize(self, patch: np.ndarray) -> np.ndarray:
        coords = cv2.findNonZero(patch)
        if coords is None or len(coords) < 4:
            return patch
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle += 90
        if abs(angle) < 1:
            return patch
        h, w = patch.shape[:2]
        matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle * 0.15, 1)
        return cv2.warpAffine(patch, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    def _estimate_identity(self, patch: np.ndarray, style: StyleProfile) -> str:
        ys, xs = np.where(patch > 0)
        if xs.size == 0:
            return ""
        w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        aspect = w / max(h, 1)
        density = np.mean(patch > 0)
        top = ys.min() / 64
        if h < 15 and aspect < 0.8:
            return "."
        if aspect < 0.35:
            return "il1t"[int(density * 20) % 4]
        if aspect > 1.15:
            choices = "mwW"
            return choices[int((aspect * 10 + density * 100) % len(choices))]
        if h > 45 and top < 0.18:
            return "bdfhklABCDEFGHIJKLMNOPQRSTUVWXYZ"[int((aspect + density) * 100) % 32]
        if density > 0.22:
            choices = "aeos"
            return choices[int((density * 100 + h) % len(choices))]
        return self.alphabet[int((aspect * 31 + density * 97 + h) % len(self.alphabet))]

    def _group_similar(self, patches: List[np.ndarray]) -> List[np.ndarray]:
        result: List[np.ndarray] = []
        for patch in patches:
            if all(structural_similarity(patch, old, data_range=255) < 0.86 for old in result):
                result.append(patch)
        return result or patches[:1]

    def _synthetic_variant(self, patch: np.ndarray) -> np.ndarray:
        angle = float(np.random.uniform(-2, 2))
        matrix = cv2.getRotationMatrix2D((patch.shape[1] / 2, patch.shape[0] / 2), angle, 1)
        out = cv2.warpAffine(patch, matrix, (patch.shape[1], patch.shape[0]), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        out = elastic_distort(out, alpha=1.2, sigma=7)
        if np.random.random() < 0.5:
            out = cv2.dilate(out, np.ones((2, 2), np.uint8), iterations=1)
        else:
            out = cv2.erode(out, np.ones((2, 2), np.uint8), iterations=1)
        return out

    def _fallback_patch(self) -> np.ndarray:
        patch = np.zeros((64, 64), dtype=np.uint8)
        cv2.ellipse(patch, (32, 35), (14, 20), -8, 0, 330, 255, 4)
        cv2.line(patch, (43, 18), (43, 52), 255, 3)
        return patch
