from __future__ import annotations

import random
import textwrap

from handwriting_tool.config import AppConfig
from handwriting_tool.types import DocumentPlan, LinePlan, PagePlan, SpanPlan, StyleProfile


class LayoutPlanner:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def plan(self, text: str, style: StyleProfile) -> DocumentPlan:
        wrap_width = self.config.layout.max_chars_per_line_hint
        raw_lines = []
        for paragraph in text.splitlines():
            if not paragraph.strip():
                raw_lines.append("")
                continue
            raw_lines.extend(textwrap.wrap(paragraph, width=wrap_width, break_long_words=False, break_on_hyphens=False))

        pages: list[PagePlan] = []
        current_page = PagePlan(page_index=0)
        for index, line_text in enumerate(raw_lines):
            if len(current_page.lines) >= self.config.layout.lines_per_page_hint:
                pages.append(current_page)
                current_page = PagePlan(page_index=len(pages))

            absolute_line = len(pages) * self.config.layout.lines_per_page_hint + len(current_page.lines)
            fatigue = min(1.0, absolute_line / max(1, len(raw_lines))) * self.config.controls.writer_fatigue
            margin_jitter = int(style.line_left_indent_jitter * (1.35 - self.config.controls.margin_discipline) * (1.0 + fatigue))
            baseline_points = self._sample_baseline(style)
            indent = self.config.layout.margin_left_px + random.randint(
                -margin_jitter,
                margin_jitter,
            )
            line = LinePlan(
                source_text=line_text,
                spans=[SpanPlan(text=line_text)],
                baseline_points=baseline_points,
                indent_px=indent,
                y_offset_px=random.randint(
                    -self.config.imperfections.line_misalignment_px,
                    self.config.imperfections.line_misalignment_px,
                ),
                line_angle_deg=random.gauss(0.0, style.page_skew_deg / 2.0 + fatigue * 0.28),
                fatigue=fatigue,
            )
            current_page.lines.append(line)

        if current_page.lines:
            pages.append(current_page)
        return DocumentPlan(pages=pages)

    def _sample_baseline(self, style: StyleProfile) -> list[float]:
        points: list[float] = []
        drift = self.config.imperfections.line_baseline_drift_px
        anchor = random.uniform(-drift, drift)
        for idx in range(8):
            local = random.uniform(-style.baseline_jitter, style.baseline_jitter)
            wave = drift * 0.35 * ((idx / 7.0) - 0.5)
            points.append(anchor + local + wave)
        return points
