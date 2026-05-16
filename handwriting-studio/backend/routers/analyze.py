from __future__ import annotations

import os
import tempfile
import time
import uuid

from PIL import Image
from fastapi import APIRouter, File, HTTPException, UploadFile

from engines.character_extractor import CharacterExtractor
from engines.style_analyzer import HandwritingStyleAnalyzer
from session_store import sessions
from utils.image_utils import base64_preview_from_mask

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename or "sample.png")[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".png") as tmp:
            tmp.write(await file.read())
            sample_path = tmp.name
        if ext == ".pdf":
            sample_path = _rasterize_first_pdf_page(sample_path)
        style = HandwritingStyleAnalyzer().analyze(sample_path)
        variants = CharacterExtractor().extract_character_variants(sample_path, style)
        session_id = str(uuid.uuid4())
        previews = []
        for char, masks in list(variants.items())[:24]:
            if char.strip() and masks:
                previews.append({"char": char, "image": base64_preview_from_mask(masks[0])})
        sessions[session_id] = {
            "created_at": time.time(),
            "last_used": time.time(),
            "sample_path": sample_path,
            "style": style,
            "variants": variants,
            "last_text": "",
            "last_settings": None,
            "pages": [],
        }
        return {"session_id": session_id, "style_profile_summary": style.summary(), "char_count": sum(len(v) for v in variants.values()), "preview_chars": previews}
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": "analysis_failed", "detail": str(exc)})


def _rasterize_first_pdf_page(pdf_path: str) -> str:
    try:
        import pypdfium2 as pdfium
    except Exception as exc:
        raise ValueError("PDF upload requires pypdfium2 for first-page rasterization. Install it or upload a JPG/PNG sample.") from exc
    pdf = pdfium.PdfDocument(pdf_path)
    if len(pdf) == 0:
        raise ValueError("The uploaded PDF has no pages.")
    bitmap = pdf[0].render(scale=150 / 72).to_pil()
    if not isinstance(bitmap, Image.Image):
        bitmap = Image.fromarray(bitmap)
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    bitmap.convert("RGB").save(out.name, "PNG")
    return out.name
