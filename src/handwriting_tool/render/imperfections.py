from __future__ import annotations

import random
import string

from handwriting_tool.config import AppConfig
from handwriting_tool.types import DocumentPlan, LinePlan, SpanPlan
from handwriting_tool.utils import tokenize_preserving_whitespace


class ImperfectionEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def apply(self, plan: DocumentPlan) -> DocumentPlan:
        if not self.config.imperfections.enabled:
            return plan

        for page in plan.pages:
            for line in page.lines:
                line.spans = self._mutate_line(line)
        return plan

    def _mutate_line(self, line: LinePlan) -> list[SpanPlan]:
        spans: list[SpanPlan] = []
        for token in tokenize_preserving_whitespace(line.source_text):
            if token.isspace() or not any(ch.isalpha() for ch in token):
                spans.append(self._make_span(token))
                continue

            if random.random() > self.config.imperfections.typo_probability:
                spans.append(self._make_span(token))
                continue

            mistake = self._make_typo(token)
            if mistake == token:
                spans.append(self._make_span(token))
                continue

            corrected = self.config.runtime.preserve_exact_text or random.random() < self.config.imperfections.correction_probability
            if corrected:
                rewrite_mode = "above" if random.random() < self.config.imperfections.rewrite_above_probability else "after"
                spans.append(
                    self._make_span(
                        mistake,
                        kind="mistake",
                        cross_out=random.random() < self.config.imperfections.crossout_probability,
                        rewrite_mode=rewrite_mode,
                    )
                )
                spans.append(self._make_span(token, kind="correction", y_offset_px=-16 if rewrite_mode == "above" else 0, size_scale=0.96))
            else:
                spans.append(self._make_span(mistake, kind="mistake"))
        return spans

    def _make_typo(self, token: str) -> str:
        chars = list(token)
        alpha_positions = [idx for idx, char in enumerate(chars) if char.isalpha()]
        if len(alpha_positions) < 2:
            return token

        strategy_roll = random.random()
        if strategy_roll < self.config.imperfections.swapped_letter_probability:
            pivot = random.choice(alpha_positions[:-1])
            chars[pivot], chars[pivot + 1] = chars[pivot + 1], chars[pivot]
            return "".join(chars)

        if strategy_roll < self.config.imperfections.swapped_letter_probability + self.config.imperfections.missing_letter_probability:
            drop = random.choice(alpha_positions)
            del chars[drop]
            return "".join(chars)

        if strategy_roll < (
            self.config.imperfections.swapped_letter_probability
            + self.config.imperfections.missing_letter_probability
            + self.config.imperfections.repeated_letter_probability
        ):
            dup = random.choice(alpha_positions)
            chars.insert(dup, chars[dup])
            return "".join(chars)

        idx = random.choice(alpha_positions)
        chars[idx] = random.choice(string.ascii_lowercase)
        return "".join(chars)

    def _make_span(
        self,
        text: str,
        *,
        kind: str = "text",
        cross_out: bool = False,
        rewrite_mode: str | None = None,
        y_offset_px: int = 0,
        size_scale: float = 1.0,
    ) -> SpanPlan:
        return SpanPlan(
            text=text,
            kind=kind,
            cross_out=cross_out,
            rewrite_mode=rewrite_mode,
            y_offset_px=y_offset_px,
            size_scale=size_scale * random.gauss(1.0, self.config.imperfections.size_jitter_std),
            tilt_deg=random.gauss(0.0, self.config.imperfections.tilt_jitter_std_deg),
            darkness_scale=random.gauss(1.0, self.config.imperfections.darkness_jitter_std),
            visual_dropout=random.random() < self.config.imperfections.faded_stroke_probability,
            overwrite=random.random() < self.config.imperfections.overwritten_letter_probability,
        )
