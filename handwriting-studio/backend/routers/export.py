from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from engines.pdf_generator import PDFGenerator
from session_store import get_session

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export/pdf/{session_id}")
async def export_pdf(session_id: str):
    try:
        session = get_session(session_id)
        pages = session.get("pages") or []
        if not pages:
            raise ValueError("No generated pages are available for this session.")
        data = PDFGenerator().generate_pdf(pages)
        headers = {"Content-Disposition": 'attachment; filename="handwriting-studio.pdf"'}
        return StreamingResponse(io.BytesIO(data), media_type="application/pdf", headers=headers)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "detail": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": "export_failed", "detail": str(exc)})

