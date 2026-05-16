from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from handwriting_tool.config import AppConfig
from handwriting_tool.render.export import save_document
from handwriting_tool.render.imperfections import ImperfectionEngine
from handwriting_tool.render.layout import LayoutPlanner
from handwriting_tool.render.renderer import HandwritingRenderer
from handwriting_tool.render.style_extractor import ReferenceStyleExtractor
from handwriting_tool.utils import read_text_file, seed_everything


class HandwritingGenerationPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.style_extractor = ReferenceStyleExtractor(config)
        self.layout_planner = LayoutPlanner(config)
        self.imperfection_engine = ImperfectionEngine(config)
        self.renderer = HandwritingRenderer(config)

    def generate(
        self,
        text_path: str | Path,
        reference_path: str | Path,
        output_path: str | Path,
    ) -> list[Path]:
        seed_everything(self.config.seed)
        text = read_text_file(text_path)
        return self.generate_from_text(text, reference_path, output_path)

    def render_document(
        self,
        text: str,
        reference_path: str | Path,
    ) -> list[object]:
        seed_everything(self.config.seed)
        style = self.style_extractor.extract(reference_path)
        plan = self.layout_planner.plan(text, style)
        plan = self.imperfection_engine.apply(plan)
        return [self.renderer.render_page(page, style) for page in plan.pages]

    def generate_from_text(
        self,
        text: str,
        reference_path: str | Path,
        output_path: str | Path,
    ) -> list[Path]:
        page_images = self.render_document(text, reference_path)
        save_document(page_images, output_path, fmt=self.config.runtime.output_format)
        return [Path(output_path)]

    def clone(self) -> "HandwritingGenerationPipeline":
        return HandwritingGenerationPipeline(deepcopy(self.config))
