from __future__ import annotations

import random

import numpy as np
from fastapi import APIRouter, HTTPException

from engines.imperfection_engine import HumanImperfectionEngine
from engines.layout_engine import WritingLayoutEngine
from engines.paper_engine import PaperCompositionEngine
from engines.variant_engine import CharacterVariantEngine
from models.schemas import GenerateRequest, RegenerateRequest
from session_store import get_session
from utils.image_utils import pil_to_base64_png
from utils.text_utils import normalize_input_text

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate")
async def generate(request: GenerateRequest):
    try:
        session = get_session(request.session_id)
        settings = request.settings.model_dump() if hasattr(request.settings, "model_dump") else request.settings.dict()
        pages = _render(session, normalize_input_text(request.text), settings)
        session["pages"] = pages
        session["last_text"] = request.text
        session["last_settings"] = settings
        return {"pages": [pil_to_base64_png(page) for page in pages], "page_count": len(pages)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "detail": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": "generation_failed", "detail": str(exc)})


@router.post("/regenerate")
async def regenerate(request: RegenerateRequest):
    try:
        session = get_session(request.session_id)
        if request.seed is not None:
            random.seed(request.seed)
            np.random.seed(request.seed)
        settings = session.get("last_settings")
        text = session.get("last_text")
        if not settings or not text:
            raise ValueError("Generate the document once before regenerating a page.")
        pages = _render(session, text, settings)
        if request.page_index >= len(pages):
            raise ValueError("Page index is outside the generated document.")
        session["pages"] = pages
        return {"page": pil_to_base64_png(pages[request.page_index])}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "detail": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": "regeneration_failed", "detail": str(exc)})


def _render(session, text: str, settings: dict):
    style = session["style"]
    variant_engine = CharacterVariantEngine(session["variants"], style)
    imperfection = HumanImperfectionEngine(
        carefulness=float(settings.get("carefulness", 0.55)),
        fatigue_rate=float(settings.get("fatigue_rate", 0.25)),
        ink_flow=float(settings.get("ink_flow", 0.78)),
        margin_discipline=float(settings.get("margin_discipline", 0.72)),
    )
    layouts = WritingLayoutEngine(variant_engine).layout_text_on_page(text, style, imperfection, settings)
    paper = PaperCompositionEngine()
    return [paper.render_page(layout, settings.get("paper_preset", "ruled_notebook"), settings.get("ink_preset", "blue_gel")) for layout in layouts]
