from __future__ import annotations

import torch
from torch import nn


class StyleEncoder(nn.Module):
    def __init__(self, in_channels: int = 1, dim: int = 256) -> None:
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm2d(32),
            nn.GELU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.GELU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.Conv2d(128, dim, kernel_size=3, stride=2, padding=1),
            nn.GELU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.proj = nn.Linear(dim, dim)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        feat = self.backbone(image).flatten(1)
        return nn.functional.normalize(self.proj(feat), dim=-1)

