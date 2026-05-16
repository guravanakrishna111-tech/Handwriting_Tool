from __future__ import annotations

import re
from typing import List


def normalize_input_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip("\n")


def paragraphs(text: str) -> List[str]:
    clean = normalize_input_text(text)
    return [p.strip() for p in re.split(r"\n\s*\n", clean) if p.strip()]


def words_preserving_breaks(text: str) -> List[str]:
    return re.findall(r"\n|[^\S\n]+|\S+", text)

