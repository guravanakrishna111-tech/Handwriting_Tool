from __future__ import annotations

import random
import re
from pathlib import Path

import numpy as np


WORD_TOKEN_PATTERN = re.compile(r"\s+|[^\s]+")


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def read_text_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def tokenize_preserving_whitespace(text: str) -> list[str]:
    return WORD_TOKEN_PATTERN.findall(text)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))

