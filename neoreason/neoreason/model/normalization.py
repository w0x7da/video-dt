"""Hybrid Normalization for projecting latent vectors onto the unit hypersphere."""

import logging

import torch
import torch.nn as nn
from torch import Tensor

logger = logging.getLogger(__name__)


class HybridNorm(nn.Module):
    """RMS Normalization followed by L2 Normalization.

    Projects all latent vectors onto the unit hypersphere (||z||_2 = 1).

    Step 1 - RMS Norm: stabilizes magnitudes across dimensions.
        x_rms = x / sqrt(mean(x^2) + eps)

    Step 2 - L2 Norm: projects onto the unit hypersphere.
        x_l2 = x_rms / ||x_rms||_2

    No learnable parameters — weight is fixed at 1.
    """

    def __init__(self, dim: int, eps: float = 1e-8) -> None:
        super().__init__()
        self.dim = dim
        self.eps = eps

    def forward(self, x: Tensor) -> Tensor:
        """Apply RMS norm then L2 norm.

        Args:
            x: Input tensor of shape (..., dim).

        Returns:
            Normalized tensor on the unit hypersphere, same shape as input.
        """
        # Step 1: RMS Normalization
        rms = torch.sqrt(torch.mean(x * x, dim=-1, keepdim=True) + self.eps)
        x_rms = x / rms

        # Step 2: L2 Normalization
        l2_norm = torch.norm(x_rms, p=2, dim=-1, keepdim=True).clamp(min=self.eps)
        x_l2 = x_rms / l2_norm

        return x_l2
