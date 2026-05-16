from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from handwriting_tool.config import load_config
from handwriting_tool.data.synthetic import SyntheticHandwritingDataset
from handwriting_tool.models.line_generator import LineGenerator
from handwriting_tool.models.style_encoder import StyleEncoder
from handwriting_tool.models.text_encoder import CharacterTokenizer, TextEncoder


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the baseline conditional line generator on synthetic data.")
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--output-dir", default="checkpoints")
    args = parser.parse_args()

    config = load_config(args.config)
    dataset = SyntheticHandwritingDataset(config, samples=64)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    tokenizer = CharacterTokenizer()
    text_encoder = TextEncoder(tokenizer.vocab_size)
    style_encoder = StyleEncoder()
    generator = LineGenerator()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    text_encoder.to(device)
    style_encoder.to(device)
    generator.to(device)

    optimizer = torch.optim.AdamW(
        list(text_encoder.parameters()) + list(style_encoder.parameters()) + list(generator.parameters()),
        lr=2e-4,
    )
    criterion = nn.L1Loss()

    for epoch in range(args.epochs):
        for batch in loader:
            images = batch["image"].to(device)
            tokens = torch.stack([tokenizer.encode(text) for text in batch["text"]]).to(device)
            text_features = text_encoder(tokens)
            style_features = style_encoder(images[:, :, :128, :512])
            noise = torch.randn(images.size(0), 1, images.size(2), images.size(3), device=device)
            recon = generator(noise, text_features, style_features)
            loss = criterion(recon, images)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        print(f"epoch={epoch + 1} loss={loss.item():.4f}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "text_encoder": text_encoder.state_dict(),
            "style_encoder": style_encoder.state_dict(),
            "generator": generator.state_dict(),
        },
        output_dir / "baseline_generator.pt",
    )


if __name__ == "__main__":
    main()

