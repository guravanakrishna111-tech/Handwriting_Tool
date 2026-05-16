from __future__ import annotations

import base64
import io
import re
import zipfile
from dataclasses import dataclass
from html import unescape
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


@dataclass
class ExtractedDocument:
    text: str
    source_type: str
    line_count: int
    paragraph_count: int
    confidence: float


@dataclass
class ReferenceAnalysis:
    page_count: int
    quality_score: float
    ink_coverage: float
    contrast_score: float
    preview_data_urls: list[str]


def extract_source_text(filename: str, content: bytes) -> ExtractedDocument:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        text = content.decode("utf-8", errors="replace")
        return _document_response(_normalize_text(text), "txt", 1.0)
    if suffix == ".docx":
        return _document_response(_extract_docx(content), "docx", 0.92)
    if suffix == ".pdf":
        return _document_response(_extract_pdf(content), "pdf", 0.88)
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        return _document_response(_ocr_image_bytes(content), "image_ocr", 0.72)
    raise ValueError("Unsupported source document. Upload PDF, DOCX, TXT, or an image document.")


def analyze_reference_upload(files: list[tuple[str, bytes]]) -> ReferenceAnalysis:
    previews: list[str] = []
    coverages: list[float] = []
    contrasts: list[float] = []
    page_count = 0

    for filename, content in files:
        suffix = Path(filename).suffix.lower()
        images = _reference_images_from_pdf(content) if suffix == ".pdf" else [Image.open(io.BytesIO(content)).convert("RGB")]
        for image in images[:4]:
            page_count += 1
            prepared = preprocess_handwriting_sample(image)
            coverage, contrast = _image_quality(prepared)
            coverages.append(coverage)
            contrasts.append(contrast)
            previews.append(_thumbnail_data_url(prepared))

    if not page_count:
        raise ValueError("No readable reference pages were found.")

    avg_coverage = float(np.mean(coverages)) if coverages else 0.0
    avg_contrast = float(np.mean(contrasts)) if contrasts else 0.0
    coverage_score = 1.0 - min(1.0, abs(avg_coverage - 0.08) / 0.08)
    quality = max(0.0, min(1.0, coverage_score * 0.45 + avg_contrast * 0.55))
    return ReferenceAnalysis(
        page_count=page_count,
        quality_score=round(quality, 3),
        ink_coverage=round(avg_coverage, 3),
        contrast_score=round(avg_contrast, 3),
        preview_data_urls=previews,
    )


def first_reference_image(filename: str, content: bytes) -> Image.Image:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        images = _reference_images_from_pdf(content)
        if not images:
            raise ValueError("Could not rasterize the reference PDF.")
        return preprocess_handwriting_sample(images[0])
    return preprocess_handwriting_sample(Image.open(io.BytesIO(content)).convert("RGB"))


def preprocess_handwriting_sample(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((1800, 2400))
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(1.25)
    return Image.merge("RGB", (gray, gray, gray))


def _extract_pdf(content: bytes) -> str:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise RuntimeError("pdfplumber is required for PDF text extraction.") from exc

    chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=4) or ""
            if not text.strip():
                try:
                    image = page.to_image(resolution=180).original
                    text = _ocr_pil_image(image)
                except Exception:
                    text = ""
            chunks.append(text.rstrip())
    return _normalize_text("\n\n".join(chunks))


def _reference_images_from_pdf(content: bytes) -> list[Image.Image]:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise RuntimeError("pdfplumber is required for PDF reference uploads.") from exc

    images: list[Image.Image] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages[:4]:
            try:
                images.append(page.to_image(resolution=170).original.convert("RGB"))
            except Exception:
                text = page.extract_text(layout=True) or ""
                if text.strip():
                    canvas = Image.new("RGB", (1200, 1600), "white")
                    images.append(canvas)
    return images


def _extract_docx(content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"</w:tr>", "\n", xml)
    text_nodes = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)
    return _normalize_text(unescape("".join(text_nodes) if text_nodes else re.sub("<[^>]+>", "", xml)))


def _ocr_image_bytes(content: bytes) -> str:
    return _ocr_pil_image(Image.open(io.BytesIO(content)).convert("RGB"))


def _ocr_pil_image(image: Image.Image) -> str:
    try:
        import cv2
        import pytesseract
    except ModuleNotFoundError as exc:
        raise RuntimeError("pytesseract and opencv-python are required for OCR extraction.") from exc

    gray = np.asarray(ImageOps.grayscale(image))
    gray = cv2.fastNlMeansDenoising(gray, None, 12, 7, 21)
    threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
    return _normalize_text(pytesseract.image_to_string(Image.fromarray(threshold), config="--psm 6"))


def _document_response(text: str, source_type: str, confidence: float) -> ExtractedDocument:
    paragraphs = [block for block in re.split(r"\n\s*\n", text) if block.strip()]
    return ExtractedDocument(
        text=text,
        source_type=source_type,
        line_count=len(text.splitlines()),
        paragraph_count=len(paragraphs),
        confidence=confidence if text.strip() else 0.0,
    )


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def _image_quality(image: Image.Image) -> tuple[float, float]:
    array = np.asarray(ImageOps.grayscale(image), dtype=np.float32) / 255.0
    ink = array < 0.78
    coverage = float(ink.mean())
    contrast = float(np.clip(array.std() * 3.4, 0, 1))
    return coverage, contrast


def _thumbnail_data_url(image: Image.Image) -> str:
    thumb = image.copy()
    thumb.thumbnail((360, 520))
    buffer = io.BytesIO()
    thumb.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
