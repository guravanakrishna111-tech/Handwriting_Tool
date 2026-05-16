from __future__ import annotations

import random
import string
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from handwriting_tool.config import AppConfig
from handwriting_tool.render.layout import LayoutPlanner
from handwriting_tool.render.renderer import HandwritingRenderer
from handwriting_tool.types import PagePlan, StyleProfile


class SyntheticHandwritingDataset(Dataset):
    def __init__(self, config: AppConfig, samples: int = 1000, max_length: int = 48) -> None:
        self.config = config
        self.samples = samples
        self.max_length = max_length
        self.layout = LayoutPlanner(config)
        self.renderer = HandwritingRenderer(config)

    def __len__(self) -> int:
        return self.samples

    def __getitem__(self, index: int) -> dict[str, torch.Tensor | str]:
        text = self._random_text()
        style = self._sample_style(index)
        plan = self.layout.plan(text, style)
        image = self.renderer.render_page(PagePlan(page_index=0, lines=plan.pages[0].lines[:1]), style).convert("L")
        cropped = np.asarray(image, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(cropped).unsqueeze(0)
        return {
            "image": tensor,
            "text": text,
            "style_vector": torch.tensor(
                [
                    style.character_spacing_mean,
                    style.word_spacing_mean,
                    style.baseline_jitter,
                    style.stroke_darkness_mean,
                    style.stroke_width_mean,
                    style.tilt_mean_deg,
                ],
                dtype=torch.float32,
            ),
        }

    def _random_text(self) -> str:
        words = []
        for _ in range(random.randint(4, 10)):
            length = random.randint(2, min(9, self.max_length))
            word = "".join(random.choice(string.ascii_lowercase) for _ in range(length))
            words.append(word)
        return " ".join(words)

    def _sample_style(self, seed: int) -> StyleProfile:
        random.seed(seed)
        return StyleProfile(
            reference_path=Path("synthetic"),
            font_path=None,
            base_font_size=random.randint(38, 56),
            line_height=random.randint(84, 106),
            character_spacing_mean=random.uniform(-0.5, 2.5),
            character_spacing_std=random.uniform(0.8, 2.5),
            word_spacing_mean=random.uniform(8.0, 16.0),
            word_spacing_std=random.uniform(2.0, 5.0),
            baseline_jitter=random.uniform(3.0, 10.0),
            stroke_darkness_mean=random.uniform(0.08, 0.25),
            stroke_darkness_std=random.uniform(0.03, 0.1),
            stroke_width_mean=random.uniform(1.0, 3.0),
            stroke_width_std=random.uniform(0.3, 1.0),
            tilt_mean_deg=random.uniform(-9.0, 8.0),
            tilt_std_deg=random.uniform(2.0, 6.0),
            page_skew_deg=random.uniform(-1.5, 1.5),
            line_left_indent_jitter=random.randint(2, 16),
        )

