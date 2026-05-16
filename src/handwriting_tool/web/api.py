from __future__ import annotations

import base64
import uuid
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from handwriting_tool.config import (
    AppConfig,
    ImperfectionConfig,
    LayoutConfig,
    RuntimeConfig,
    StudioControlsConfig,
    load_config,
)
from handwriting_tool.ingest import analyze_reference_upload, extract_source_text, first_reference_image
from handwriting_tool.pipeline import HandwritingGenerationPipeline
from handwriting_tool.render.export import save_document


class StudioSettings(BaseModel):
    writing_carefulness: float = Field(0.62, ge=0, le=1)
    exam_rush: float = Field(0.38, ge=0, le=1)
    writer_fatigue: float = Field(0.35, ge=0, le=1)
    ink_flow: float = Field(0.58, ge=0, le=1)
    letter_consistency: float = Field(0.48, ge=0, le=1)
    margin_discipline: float = Field(0.62, ge=0, le=1)
    mood_variation: float = Field(0.25, ge=0, le=1)
    handedness: str = "right"
    paper_preset: str = "ruled"
    ink_preset: str = "blue_gel"
    output_format: str = "pdf"


class GenerateJsonRequest(BaseModel):
    text: str
    reference_image: str
    settings: StudioSettings = Field(default_factory=StudioSettings)


class GenerateResponse(BaseModel):
    session_id: str
    page_count: int
    preview_url: str
    download_url: str
    download_name: str
    page_urls: list[str]
    text_preserved: bool


class ExtractTextResponse(BaseModel):
    text: str
    source_type: str
    line_count: int
    paragraph_count: int
    confidence: float


class ReferenceAnalyzeResponse(BaseModel):
    page_count: int
    quality_score: float
    ink_coverage: float
    contrast_score: float
    preview_data_urls: list[str]


class StudioApi:
    def __init__(self, config: AppConfig, output_root: Path) -> None:
        self.config = config
        self.output_root = output_root
        self.output_root.mkdir(parents=True, exist_ok=True)

    def generate(self, text: str, reference_files: list[tuple[str, bytes]], settings: StudioSettings) -> GenerateResponse:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is required.")
        if not reference_files:
            raise HTTPException(status_code=400, detail="A handwriting sample image is required.")

        session_id = uuid.uuid4().hex[:12]
        session_dir = self.output_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        reference_path = session_dir / "reference.png"
        try:
            reference_image = first_reference_image(reference_files[0][0], reference_files[0][1])
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        reference_image.save(reference_path)
        for index, (filename, content) in enumerate(reference_files, start=1):
            safe_name = Path(filename).name or f"reference_{index}"
            (session_dir / f"uploaded_reference_{index}_{safe_name}").write_bytes(content)
        (session_dir / "input.txt").write_text(text, encoding="utf-8")

        pipeline = HandwritingGenerationPipeline(self._config_from_settings(settings))
        pages = pipeline.render_document(text, reference_path)
        page_urls: list[str] = []
        for index, page in enumerate(pages, start=1):
            page_path = session_dir / f"page_{index:02d}.png"
            page.save(page_path)
            page_urls.append(f"/outputs/{session_id}/{page_path.name}")

        preview_path = session_dir / "preview.png"
        pages[0].save(preview_path)
        output_format = settings.output_format.lower()
        download_name, download_url = self._save_output(session_dir, pages, output_format, page_urls)
        return GenerateResponse(
            session_id=session_id,
            page_count=len(pages),
            preview_url=f"/outputs/{session_id}/{preview_path.name}",
            download_url=download_url,
            download_name=download_name,
            page_urls=page_urls,
            text_preserved=True,
        )

    def _config_from_settings(self, settings: StudioSettings) -> AppConfig:
        config = deepcopy(self.config)
        values = settings.model_dump()

        config.controls = replace(config.controls, **_filter(values, StudioControlsConfig))
        config.layout = replace(config.layout, **_filter(values, LayoutConfig))
        config.runtime = replace(config.runtime, output_format=settings.output_format, preserve_exact_text=True)

        care = settings.writing_carefulness
        rush = settings.exam_rush
        fatigue = settings.writer_fatigue
        config.imperfections = replace(
            config.imperfections,
            typo_probability=max(0.0, 0.035 + rush * 0.06 - care * 0.025),
            correction_probability=1.0,
            line_baseline_drift_px=4.0 + rush * 9.0 + fatigue * 6.0,
            ink_blot_probability=max(0.0, 0.006 + settings.ink_flow * 0.035),
            overwritten_letter_probability=max(0.0, 0.01 + rush * 0.035),
            faded_stroke_probability=max(0.0, 0.012 + fatigue * 0.05),
        )
        return config

    def _save_output(
        self,
        session_dir: Path,
        pages: list[Any],
        output_format: str,
        page_urls: list[str],
    ) -> tuple[str, str]:
        if output_format == "png":
            if len(pages) == 1:
                return "generated.png", page_urls[0]
            archive_path = session_dir / "generated_pages.zip"
            with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
                for page_file in sorted(session_dir.glob("page_*.png")):
                    archive.write(page_file, arcname=page_file.name)
            return archive_path.name, f"/outputs/{session_dir.name}/{archive_path.name}"

        pdf_path = session_dir / "generated.pdf"
        save_document(pages, pdf_path, fmt="pdf")
        return pdf_path.name, f"/outputs/{session_dir.name}/{pdf_path.name}"


def create_app(config_path: str | Path = "configs/base.yaml", output_root: str | Path = "outputs/web") -> FastAPI:
    output_path = Path(output_root)
    studio = StudioApi(load_config(config_path), output_path)
    app = FastAPI(title="Handwriting Studio API", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/outputs", StaticFiles(directory=output_path), name="outputs")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/generate", response_model=GenerateResponse)
    async def generate_json(request: GenerateJsonRequest) -> GenerateResponse:
        reference_bytes = _decode_data_url(request.reference_image)
        return studio.generate(request.text, [("reference.png", reference_bytes)], request.settings)

    @app.post("/api/generate-upload", response_model=GenerateResponse)
    async def generate_upload(
        text: str = Form(...),
        settings: str = Form("{}"),
        reference: list[UploadFile] = File(...),
    ) -> GenerateResponse:
        parsed = StudioSettings.model_validate_json(settings)
        reference_files = [(item.filename or f"reference_{index}.png", await item.read()) for index, item in enumerate(reference, start=1)]
        return studio.generate(text, reference_files, parsed)

    @app.post("/api/source/extract", response_model=ExtractTextResponse)
    async def extract_source(source: UploadFile = File(...)) -> ExtractTextResponse:
        try:
            extracted = extract_source_text(source.filename or "source", await source.read())
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ExtractTextResponse(**extracted.__dict__)

    @app.post("/api/reference/analyze", response_model=ReferenceAnalyzeResponse)
    async def analyze_reference(reference: list[UploadFile] = File(...)) -> ReferenceAnalyzeResponse:
        try:
            files = [(item.filename or f"reference_{index}.png", await item.read()) for index, item in enumerate(reference, start=1)]
            analysis = analyze_reference_upload(files)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ReferenceAnalyzeResponse(**analysis.__dict__)

    @app.get("/api/sessions/{session_id}/{filename}")
    def download(session_id: str, filename: str) -> FileResponse:
        path = (output_path / session_id / filename).resolve()
        try:
            path.relative_to(output_path.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="File not found.") from exc
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found.")
        return FileResponse(path)

    return app


def _filter(values: dict[str, Any], target_type: type[object]) -> dict[str, Any]:
    fields = getattr(target_type, "__dataclass_fields__", {})
    return {key: value for key, value in values.items() if key in fields}


def _decode_data_url(data_url: str) -> bytes:
    if "," not in data_url:
        raise HTTPException(status_code=400, detail="Reference image payload is invalid.")
    header, encoded = data_url.split(",", 1)
    if ";base64" not in header:
        raise HTTPException(status_code=400, detail="Reference image must be base64 encoded.")
    return base64.b64decode(encoded)


app = create_app()
