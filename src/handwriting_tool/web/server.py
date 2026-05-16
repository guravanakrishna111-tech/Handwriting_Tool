from __future__ import annotations

import base64
import json
import mimetypes
import shutil
import threading
import uuid
from copy import deepcopy
from dataclasses import replace
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from zipfile import ZIP_DEFLATED, ZipFile

from handwriting_tool.config import AppConfig, ImperfectionConfig, LayoutConfig, RuntimeConfig, StudioControlsConfig, load_config
from handwriting_tool.pipeline import HandwritingGenerationPipeline
from handwriting_tool.render.export import save_document


PACKAGE_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = PACKAGE_ROOT / "static"


class WebApplication:
    def __init__(self, config: AppConfig, output_root: Path) -> None:
        self.config = config
        self.output_root = output_root
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def build_pipeline(self, overrides: dict[str, object]) -> HandwritingGenerationPipeline:
        config = deepcopy(self.config)
        imperfections = replace(config.imperfections, **self._filter_overrides(overrides, ImperfectionConfig))
        controls = replace(config.controls, **self._filter_overrides(overrides, StudioControlsConfig))
        layout = replace(config.layout, **self._filter_overrides(overrides, LayoutConfig))
        runtime = replace(config.runtime, **self._filter_overrides(overrides, RuntimeConfig))
        config.imperfections = imperfections
        config.controls = controls
        config.layout = layout
        config.runtime = runtime
        return HandwritingGenerationPipeline(config)

    def handle_generate(self, payload: dict[str, object]) -> dict[str, object]:
        text = str(payload.get("text", "")).strip()
        reference_image = str(payload.get("reference_image", "")).strip()
        output_format = str(payload.get("output_format", "pdf")).lower()

        if not text:
            raise ValueError("Please enter text to rewrite.")
        if not reference_image:
            raise ValueError("Please upload a reference handwritten page.")

        session_id = uuid.uuid4().hex[:12]
        session_dir = self.output_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        reference_path = session_dir / "reference.png"
        text_path = session_dir / "input.txt"
        preview_path = session_dir / "preview.png"

        text_path.write_text(text, encoding="utf-8")
        reference_path.write_bytes(_decode_data_url(reference_image))

        overrides = dict(payload.get("settings") or {})
        overrides["output_format"] = output_format
        pipeline = self.build_pipeline(overrides)
        pages = pipeline.render_document(text, reference_path)
        pages[0].save(preview_path)

        page_urls = []
        for index, image in enumerate(pages, start=1):
            page_file = session_dir / f"page_{index:02d}.png"
            image.save(page_file)
            page_urls.append(f"/outputs/{session_id}/{page_file.name}")

        download_name, download_url = self._save_primary_output(session_dir, pages, output_format, page_urls)

        return {
            "session_id": session_id,
            "message": self._build_message(len(pages), output_format),
            "preview_url": f"/outputs/{session_id}/{preview_path.name}",
            "download_url": download_url,
            "download_name": download_name,
            "page_urls": page_urls,
            "input_text_path": f"/outputs/{session_id}/{text_path.name}",
            "reference_path": f"/outputs/{session_id}/{reference_path.name}",
        }

    def _build_message(self, page_count: int, output_format: str) -> str:
        page_word = "page" if page_count == 1 else "pages"
        if output_format == "png" and page_count > 1:
            output_label = "ZIP archive of page PNGs"
        else:
            output_label = output_format.upper()
        return f"Generated {page_count} handwritten {page_word}. You can preview the first page and download the full {output_label} output."

    def _filter_overrides(self, overrides: dict[str, object], target_type: type[object]) -> dict[str, object]:
        field_names = getattr(target_type, "__dataclass_fields__", {})
        filtered: dict[str, object] = {}
        for key, value in overrides.items():
            if key not in field_names:
                continue
            filtered[key] = value
        return filtered

    def _save_primary_output(
        self,
        session_dir: Path,
        pages: list[object],
        output_format: str,
        page_urls: list[str],
    ) -> tuple[str, str]:
        if output_format == "png":
            if len(page_urls) == 1:
                return "generated.png", page_urls[0]
            archive_path = session_dir / "generated_pages.zip"
            with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
                for page_file in sorted(session_dir.glob("page_*.png")):
                    archive.write(page_file, arcname=page_file.name)
            return archive_path.name, f"/outputs/{session_dir.name}/{archive_path.name}"

        pdf_path = session_dir / "generated.pdf"
        save_document(pages, pdf_path, fmt="pdf")
        return pdf_path.name, f"/outputs/{session_dir.name}/{pdf_path.name}"


class HandwritingRequestHandler(BaseHTTPRequestHandler):
    app: WebApplication

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in {"/", "/index.html"}:
            self._serve_file(STATIC_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            target = (STATIC_ROOT / path.removeprefix("/static/")).resolve()
            if not self._is_within(target, STATIC_ROOT):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._serve_file(target)
            return
        if path.startswith("/outputs/"):
            target = (self.app.output_root / path.removeprefix("/outputs/")).resolve()
            if not self._is_within(target, self.app.output_root):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._serve_file(target)
            return
        if path == "/api/health":
            self._send_json({"status": "ok"})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/generate":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
            response = self.app.handle_generate(payload)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        self._send_json(response)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _serve_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        guessed = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", guessed)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()
        with path.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile)

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _is_within(self, candidate: Path, root: Path) -> bool:
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            return False
        return True


def _decode_data_url(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("Reference image payload is invalid.")
    header, encoded = data_url.split(",", 1)
    if ";base64" not in header:
        raise ValueError("Reference image must be base64 encoded.")
    return base64.b64decode(encoded)


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    config_path: str | Path = "configs/base.yaml",
    output_root: str | Path = "outputs/web",
) -> ThreadingHTTPServer:
    app = WebApplication(load_config(config_path), Path(output_root))
    handler = type("HandwritingHandler", (HandwritingRequestHandler,), {"app": app})
    server = ThreadingHTTPServer((host, port), handler)
    return server
