from __future__ import annotations

import base64
import io
import math
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def read_image(path: str | Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Unable to read image. Use a JPG or PNG handwriting sample.")
    return img


def to_gray(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()


def binarize_strokes(image: np.ndarray) -> np.ndarray:
    gray = cv2.GaussianBlur(to_gray(image), (3, 3), 0)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    return cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)


def crop_to_content(binary: np.ndarray, pad: int = 4) -> np.ndarray:
    ys, xs = np.where(binary > 0)
    if len(xs) == 0:
        return binary
    x1, x2 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, binary.shape[1])
    y1, y2 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, binary.shape[0])
    return binary[y1:y2, x1:x2]


def normalize_patch(binary_patch: np.ndarray, size: int = 64) -> np.ndarray:
    patch = crop_to_content(binary_patch)
    if patch.size == 0:
        return np.zeros((size, size), dtype=np.uint8)
    h, w = patch.shape[:2]
    scale = min((size - 12) / max(w, 1), (size - 12) / max(h, 1))
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = cv2.resize(patch, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((size, size), dtype=np.uint8)
    x = (size - nw) // 2
    y = size - nh - 6
    canvas[y : y + nh, x : x + nw] = resized
    return canvas


def split_text_lines(binary: np.ndarray) -> List[Tuple[int, int]]:
    projection = (binary > 0).sum(axis=1)
    if projection.max(initial=0) == 0:
        return []
    active = projection > max(2, projection.max() * 0.05)
    lines: List[Tuple[int, int]] = []
    start = None
    for idx, value in enumerate(active):
        if value and start is None:
            start = idx
        elif not value and start is not None:
            if idx - start > 8:
                lines.append((max(0, start - 2), min(binary.shape[0], idx + 2)))
            start = None
    if start is not None and binary.shape[0] - start > 8:
        lines.append((max(0, start - 2), binary.shape[0]))
    return lines


def connected_components(binary: np.ndarray) -> List[Tuple[int, int, int, int, int]]:
    n, _, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    boxes = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area > 5 and w > 1 and h > 2:
            boxes.append((int(x), int(y), int(w), int(h), int(area)))
    return sorted(boxes, key=lambda b: (b[1], b[0]))


def rgba_from_binary(mask: np.ndarray) -> np.ndarray:
    alpha = np.clip(mask, 0, 255).astype(np.uint8)
    return np.dstack([np.zeros_like(alpha), np.zeros_like(alpha), np.zeros_like(alpha), alpha])


def rotate_image_alpha(rgba: np.ndarray, angle: float) -> np.ndarray:
    h, w = rgba.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    matrix[0, 2] += nw / 2 - center[0]
    matrix[1, 2] += nh / 2 - center[1]
    return cv2.warpAffine(rgba, matrix, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def elastic_distort(mask: np.ndarray, alpha: float = 2.0, sigma: float = 8.0) -> np.ndarray:
    rng = np.random.default_rng()
    shape = mask.shape
    dx = gaussian_filter((rng.random(shape) * 2 - 1), sigma) * alpha
    dy = gaussian_filter((rng.random(shape) * 2 - 1), sigma) * alpha
    x, y = np.meshgrid(np.arange(shape[1]), np.arange(shape[0]))
    return cv2.remap(mask, (x + dx).astype(np.float32), (y + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def pil_to_base64_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def base64_preview_from_mask(mask: np.ndarray) -> str:
    img = Image.fromarray(255 - mask).convert("RGB")
    return pil_to_base64_png(img)

