from __future__ import annotations

import io
import tempfile
from typing import List

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class PDFGenerator:
    def generate_pdf(self, pages: List[Image.Image], output_path: str | None = None) -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        for page in pages:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                page.convert("RGB").save(tmp.name, "JPEG", quality=92)
                c.drawImage(tmp.name, 0, 0, width=A4[0], height=A4[1])
            c.showPage()
        c.save()
        data = buffer.getvalue()
        if output_path:
            with open(output_path, "wb") as fh:
                fh.write(data)
        return data

