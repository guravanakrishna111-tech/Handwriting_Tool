from __future__ import annotations

from pathlib import Path

from PIL import Image


def save_document(images: list[Image.Image], output_path: str | Path, fmt: str = "pdf") -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if not images:
        raise ValueError("No images to save.")

    fmt = fmt.lower()
    if fmt == "pdf" or destination.suffix.lower() == ".pdf":
        first, rest = images[0], images[1:]
        first.save(destination, save_all=True, append_images=rest, resolution=300.0)
        return

    if len(images) == 1:
        images[0].save(destination)
        return

    stem = destination.with_suffix("")
    for idx, image in enumerate(images):
        image.save(stem.parent / f"{stem.name}_{idx + 1:02d}.png")

