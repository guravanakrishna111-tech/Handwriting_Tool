from __future__ import annotations

import torch
from torch import nn


class ConditionalResBlock(nn.Module):
    def __init__(self, channels: int, cond_dim: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.norm1 = nn.GroupNorm(8, channels)
        self.norm2 = nn.GroupNorm(8, channels)
        self.scale = nn.Linear(cond_dim, channels)
        self.shift = nn.Linear(cond_dim, channels)

    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        residual = x
        scale = self.scale(cond).unsqueeze(-1).unsqueeze(-1)
        shift = self.shift(cond).unsqueeze(-1).unsqueeze(-1)
        x = self.conv1(nn.functional.gelu(self.norm1(x)))
        x = x * (1 + scale) + shift
        x = self.conv2(nn.functional.gelu(self.norm2(x)))
        return x + residual


class LineGenerator(nn.Module):
    def __init__(self, text_dim: int = 256, style_dim: int = 256, latent_channels: int = 128) -> None:
        super().__init__()
        cond_dim = text_dim + style_dim
        self.noise_proj = nn.Conv2d(1, latent_channels, kernel_size=3, padding=1)
        self.blocks = nn.ModuleList([ConditionalResBlock(latent_channels, cond_dim) for _ in range(6)])
        self.to_image = nn.Sequential(
            nn.GroupNorm(8, latent_channels),
            nn.GELU(),
            nn.Conv2d(latent_channels, 1, kernel_size=3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, noise: torch.Tensor, text_tokens: torch.Tensor, style_embedding: torch.Tensor) -> torch.Tensor:
        text_context = text_tokens.mean(dim=1)
        cond = torch.cat([text_context, style_embedding], dim=-1)
        x = self.noise_proj(noise)
        for block in self.blocks:
            x = block(x, cond)
        return self.to_image(x)

