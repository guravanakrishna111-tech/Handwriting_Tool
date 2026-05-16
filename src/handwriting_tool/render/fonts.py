from __future__ import annotations

from pathlib import Path


HANDWRITING_FONT_CANDIDATES = [
    "segoesc.ttf",
    "Inkfree.ttf",
    "BRUSHSCI.ttf",
    "LucidaHandwritingItalic.ttf",
    "comic.ttf",
]


def get_font_candidates() -> list[Path]:
    search_roots = [
        Path("C:/Windows/Fonts"),
        Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
    ]
    discovered: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for name in HANDWRITING_FONT_CANDIDATES:
            path = root / name
            if path.exists():
                discovered.append(path)
    return discovered


def choose_reference_font(prefer_handwriting_fonts: bool = True) -> str | None:
    if not prefer_handwriting_fonts:
        return None
    candidates = get_font_candidates()
    if not candidates:
        return None
    return str(candidates[0])

