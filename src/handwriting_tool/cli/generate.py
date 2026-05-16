from __future__ import annotations

import argparse

from handwriting_tool.config import load_config
from handwriting_tool.pipeline import HandwritingGenerationPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate handwritten pages from text and a reference sample.")
    parser.add_argument("--text", required=True, help="Path to the input text file.")
    parser.add_argument("--reference", required=True, help="Path to the reference handwritten image.")
    parser.add_argument("--output", required=True, help="Path to the output PDF or image.")
    parser.add_argument("--config", default="configs/base.yaml", help="Path to a YAML config file.")
    args = parser.parse_args()

    config = load_config(args.config)
    pipeline = HandwritingGenerationPipeline(config)
    pipeline.generate(args.text, args.reference, args.output)


if __name__ == "__main__":
    main()

