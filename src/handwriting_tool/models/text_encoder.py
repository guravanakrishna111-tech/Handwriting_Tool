from __future__ import annotations

import string

import torch
from torch import nn


DEFAULT_VOCAB = ["<pad>", "<unk>"] + list(string.printable)


class CharacterTokenizer:
    def __init__(self, vocab: list[str] | None = None) -> None:
        self.vocab = vocab or DEFAULT_VOCAB
        self.stoi = {token: idx for idx, token in enumerate(self.vocab)}
        self.pad_id = self.stoi["<pad>"]
        self.unk_id = self.stoi["<unk>"]

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    def encode(self, text: str, max_length: int = 256) -> torch.Tensor:
        ids = [self.stoi.get(ch, self.unk_id) for ch in text[:max_length]]
        if len(ids) < max_length:
            ids.extend([self.pad_id] * (max_length - len(ids)))
        return torch.tensor(ids, dtype=torch.long)


class TextEncoder(nn.Module):
    def __init__(self, vocab_size: int, dim: int = 256, depth: int = 4, heads: int = 8, max_length: int = 256) -> None:
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, dim)
        self.position_embedding = nn.Embedding(max_length, dim)
        layer = nn.TransformerEncoderLayer(d_model=dim, nhead=heads, dim_feedforward=dim * 4, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=depth)
        self.norm = nn.LayerNorm(dim)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(token_ids.shape[1], device=token_ids.device).unsqueeze(0)
        x = self.token_embedding(token_ids) + self.position_embedding(positions)
        return self.norm(self.encoder(x))

