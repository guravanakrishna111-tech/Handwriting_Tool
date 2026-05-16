from __future__ import annotations

import math
from statistics import median

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt
from skimage.morphology import skeletonize

from models.schemas import StyleProfile
from utils.image_utils import binarize_strokes, connected_components, read_image, split_text_lines, to_gray


class HandwritingStyleAnalyzer:
    def analyze(self, image_path: str) -> StyleProfile:
        image = read_image(image_path)
        gray = to_gray(image)
        binary = binarize_strokes(image)
        boxes = connected_components(binary)
        areas = np.array([b[4] for b in boxes], dtype=float) if boxes else np.array([1.0])
        med_area = float(np.median(areas))
        letter_boxes = [b for b in boxes if 0.18 * med_area <= b[4] <= 8 * med_area and 4 <= b[2] <= 140 and 7 <= b[3] <= 160]
        if not letter_boxes:
            letter_boxes = boxes[:]

        widths = [b[2] for b in letter_boxes] or [18]
        heights = [b[3] for b in letter_boxes] or [34]
        avg_w, avg_h = float(median(widths)), float(median(heights))

        slant_values = self._slant_angles(binary)
        slant = float(np.clip(np.mean(slant_values) if slant_values else 0.0, -30, 30))
        slant_std = float(np.clip(np.std(slant_values) if len(slant_values) > 2 else 2.0, 0.8, 8.0))

        baseline_var = self._baseline_variance(binary, letter_boxes)
        word_spacing = self._word_spacing_ratio(letter_boxes, avg_w)
        letter_spacing = self._letter_spacing(letter_boxes, avg_w)
        stroke_width = self._stroke_width(binary)
        stroke_pixels = gray[binary > 0]
        pressure = float(np.std(stroke_pixels)) if stroke_pixels.size else 20.0
        uppercase = float(np.mean([h > avg_h * 1.35 for h in heights])) if heights else 0.08
        roundness = self._roundness(binary)
        speed = self._writing_speed(binary, max(len(letter_boxes), 1))

        return StyleProfile(
            slant_angle=slant,
            avg_char_width=avg_w,
            avg_char_height=avg_h,
            baseline_y_variance=baseline_var,
            word_spacing_ratio=word_spacing,
            letter_spacing_tightness=letter_spacing,
            stroke_width=stroke_width,
            pressure_proxy=pressure,
            uppercase_ratio=uppercase,
            roundness_score=roundness,
            writing_speed_estimate=speed,
            slant_std=slant_std,
        )

    def _slant_angles(self, binary: np.ndarray) -> list[float]:
        lines = cv2.HoughLinesP(binary, 1, np.pi / 180, threshold=18, minLineLength=12, maxLineGap=4)
        values: list[float] = []
        if lines is None:
            return values
        for line in lines[:, 0]:
            x1, y1, x2, y2 = line
            dx, dy = x2 - x1, y2 - y1
            if dy == 0:
                continue
            angle_from_vertical = math.degrees(math.atan2(dx, dy))
            if -45 <= angle_from_vertical <= 45:
                values.append(angle_from_vertical)
        return values

    def _baseline_variance(self, binary: np.ndarray, boxes: list[tuple[int, int, int, int, int]]) -> float:
        variances = []
        for y1, y2 in split_text_lines(binary):
            centers = [y + h / 2 for x, y, w, h, a in boxes if y1 <= y + h / 2 <= y2]
            if len(centers) > 2:
                variances.append(float(np.std(centers)))
        return float(np.mean(variances)) if variances else 2.5

    def _word_spacing_ratio(self, boxes, avg_w: float) -> float:
        xs = sorted([(x, x + w) for x, y, w, h, a in boxes], key=lambda p: p[0])
        gaps = [xs[i + 1][0] - xs[i][1] for i in range(len(xs) - 1) if xs[i + 1][0] - xs[i][1] > avg_w * 0.7]
        return float(np.clip(np.median(gaps) / max(avg_w, 1), 1.2, 4.2)) if gaps else 2.2

    def _letter_spacing(self, boxes, avg_w: float) -> float:
        xs = sorted([(x, x + w) for x, y, w, h, a in boxes], key=lambda p: p[0])
        gaps = [max(0, xs[i + 1][0] - xs[i][1]) for i in range(len(xs) - 1)]
        inner = [g for g in gaps if 0 <= g <= avg_w * 0.7]
        return float(np.clip(np.median(inner) / max(avg_w, 1), 0.05, 0.8)) if inner else 0.22

    def _stroke_width(self, binary: np.ndarray) -> float:
        dist = distance_transform_edt(binary > 0)
        skel = skeletonize(binary > 0)
        vals = dist[skel] * 2
        return float(np.mean(vals)) if vals.size else 2.2

    def _roundness(self, binary: np.ndarray) -> float:
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        scores = []
        for c in contours:
            area = cv2.contourArea(c)
            peri = cv2.arcLength(c, True)
            if area > 20 and peri > 0:
                scores.append(4 * math.pi * area / (peri * peri))
        return float(np.clip(np.mean(scores) if scores else 0.35, 0, 1))

    def _writing_speed(self, binary: np.ndarray, char_count: int) -> float:
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return float(np.clip(len([c for c in contours if cv2.contourArea(c) > 8]) / max(char_count, 1), 0.5, 4.0))

