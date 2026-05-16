from __future__ import annotations

import torch
from torch import nn


class HandwritingRecognizer(nn.Module):
    def __init__(self, vocab_size: int, channels: int = 64, hidden_size: int = 256) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 2)),
            nn.Conv2d(channels, channels * 2, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 2)),
            nn.Conv2d(channels * 2, channels * 4, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.rnn = nn.LSTM(channels * 4 * 8, hidden_size, bidirectional=True, batch_first=True)
        self.classifier = nn.Linear(hidden_size * 2, vocab_size)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        feat = self.features(image)
        b, c, h, w = feat.shape
        feat = feat.permute(0, 3, 1, 2).contiguous().view(b, w, c * h)
        seq, _ = self.rnn(feat)
        return self.classifier(seq)

