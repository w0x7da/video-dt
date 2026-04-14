"""JEPA training losses: SIGReg regularizer and cosine prediction loss."""

import logging

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

logger = logging.getLogger(__name__)


class SIGRegLoss(nn.Module):
    """Sigmoid Regularizer — prevents representation collapse.

    Forces the latent space to be isotropic by penalizing small eigenvalues
    of the covariance matrix of the batch embeddings.

    Algorithm:
        1. Center Z: Z_centered = Z - Z.mean(dim=0)
        2. Covariance: C = (Z_centered.T @ Z_centered) / (batch_size - 1)
        3. Eigenvalues: eigenvals = eigvalsh(C)
        4. Loss: -log(sigmoid(eigenvals)).mean()

    If all vectors collapse to the same point, eigenvalues -> 0 -> loss -> inf.
    """

    def __init__(self, eps: float = 1e-8) -> None:
        super().__init__()
        self.eps = eps

    def forward(self, z: Tensor) -> Tensor:
        """Compute SIGReg loss on a batch of latent vectors.

        Args:
            z: Latent vectors of shape (batch_size, latent_dim).

        Returns:
            Scalar SIGReg loss.
        """
        batch_size = z.shape[0]
        if batch_size < 2:
            return torch.tensor(0.0, device=z.device, dtype=z.dtype)

        # Center
        z_centered = z - z.mean(dim=0, keepdim=True)

        # Covariance matrix
        cov = (z_centered.T @ z_centered) / (batch_size - 1)

        # Eigenvalues — fallback to CPU for MPS (eigvalsh not supported)
        original_device = cov.device
        if cov.device.type == "mps":
            cov_cpu = cov.detach().cpu()
            eigenvals = torch.linalg.eigvalsh(cov_cpu).to(original_device)
        else:
            eigenvals = torch.linalg.eigvalsh(cov)

        # Numerical stability
        eigenvals = eigenvals.clamp(min=self.eps)

        # SIGReg penalty: -log(sigmoid(eigenvals))
        loss = -torch.log(torch.sigmoid(eigenvals) + self.eps).mean()

        return loss


class CosinePredictionLoss(nn.Module):
    """Cosine similarity loss between predicted and target latent vectors.

    loss = (1 - cosine_similarity(prediction, target)) * latent_dim
    Scaling by latent_dim stabilizes training across different model sizes.
    """

    def forward(self, prediction: Tensor, target: Tensor) -> Tensor:
        """Compute scaled cosine prediction loss.

        Args:
            prediction: Predicted latent vectors (batch_size, latent_dim).
            target: Target latent vectors (batch_size, latent_dim). Should be detached.

        Returns:
            Scalar cosine prediction loss.
        """
        latent_dim = prediction.shape[-1]
        cos_sim = F.cosine_similarity(prediction, target.detach(), dim=-1)
        loss = (1.0 - cos_sim).mean() * latent_dim
        return loss


class JEPALoss(nn.Module):
    """Combined JEPA loss: cosine prediction loss + lambda * SIGReg.

    Args:
        sigreg_weight: Weight (lambda) for the SIGReg regularization term.
    """

    def __init__(self, sigreg_weight: float = 1.0) -> None:
        super().__init__()
        self.cosine_loss = CosinePredictionLoss()
        self.sigreg_loss = SIGRegLoss()
        self.sigreg_weight = sigreg_weight

    def forward(
        self,
        predictions: list[Tensor],
        targets: list[Tensor],
    ) -> dict[str, Tensor]:
        """Compute the full JEPA loss over a reasoning trajectory.

        Args:
            predictions: List of predicted latent vectors (one per reasoning step).
            targets: List of target latent vectors from the EMA encoder.

        Returns:
            Dict with 'total', 'prediction', and 'sigreg' loss values.
        """
        # Prediction loss: average cosine loss over all steps
        pred_losses = []
        for pred, tgt in zip(predictions, targets):
            pred_losses.append(self.cosine_loss(pred, tgt))
        loss_pred = torch.stack(pred_losses).mean()

        # SIGReg: compute over all predicted latents stacked together
        all_preds = torch.cat(predictions, dim=0)
        loss_sigreg = self.sigreg_loss(all_preds)

        loss_total = loss_pred + self.sigreg_weight * loss_sigreg

        return {
            "total": loss_total,
            "prediction": loss_pred,
            "sigreg": loss_sigreg,
        }
