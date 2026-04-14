"""Tests for HybridNorm, EMA, and loss functions."""

import torch
import torch.nn as nn

from neoreason.model.normalization import HybridNorm
from neoreason.model.ema import EMAUpdater
from neoreason.training.losses import SIGRegLoss, CosinePredictionLoss, JEPALoss


class TestHybridNorm:
    def test_unit_sphere(self) -> None:
        """All outputs must lie on the unit hypersphere."""
        norm = HybridNorm(256)
        x = torch.randn(32, 256)
        out = norm(x)
        norms = torch.norm(out, dim=-1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_unit_sphere_3d(self) -> None:
        """Works with 3D inputs (batch, seq, dim)."""
        norm = HybridNorm(128)
        x = torch.randn(4, 10, 128)
        out = norm(x)
        norms = torch.norm(out, dim=-1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_gradient_flow(self) -> None:
        """Gradients must flow through the normalization."""
        norm = HybridNorm(64)
        x = torch.randn(8, 64, requires_grad=True)
        out = norm(x)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None
        assert not torch.all(x.grad == 0)

    def test_zero_input(self) -> None:
        """Should handle zero inputs without NaN."""
        norm = HybridNorm(32)
        x = torch.zeros(4, 32)
        out = norm(x)
        assert not torch.isnan(out).any()

    def test_output_shape(self) -> None:
        """Output shape must match input shape."""
        norm = HybridNorm(256)
        x = torch.randn(16, 256)
        out = norm(x)
        assert out.shape == x.shape


class TestEMAUpdater:
    def test_momentum_schedule(self) -> None:
        """Momentum should interpolate linearly from initial to final."""
        ema = EMAUpdater(
            momentum_initial=0.996,
            momentum_final=0.999,
            total_steps=1000,
        )
        assert abs(ema.get_momentum(0) - 0.996) < 1e-6
        assert abs(ema.get_momentum(500) - 0.9975) < 1e-6
        assert abs(ema.get_momentum(1000) - 0.999) < 1e-6
        # Beyond total_steps should clamp to final
        assert abs(ema.get_momentum(2000) - 0.999) < 1e-6

    def test_ema_update_moves_target(self) -> None:
        """Target model params should move toward online model."""
        online = nn.Linear(16, 16)
        target = nn.Linear(16, 16)
        # Set target to zeros
        with torch.no_grad():
            for p in target.parameters():
                p.zero_()

        ema = EMAUpdater(momentum_initial=0.5, momentum_final=0.5, total_steps=1)
        ema.step(online, target, step=0)

        # Target should now be 0.5 * 0 + 0.5 * online = 0.5 * online
        for op, tp in zip(online.parameters(), target.parameters()):
            expected = 0.5 * op.data
            assert torch.allclose(tp.data, expected, atol=1e-6)

    def test_step_returns_momentum(self) -> None:
        """step() should return the momentum value used."""
        ema = EMAUpdater(momentum_initial=0.9, momentum_final=0.99, total_steps=100)
        online = nn.Linear(4, 4)
        target = nn.Linear(4, 4)
        m = ema.step(online, target, step=50)
        assert abs(m - 0.945) < 1e-6


class TestSIGRegLoss:
    def test_diverse_vectors_low_loss(self) -> None:
        """Diverse (orthogonal-ish) vectors should have low SIGReg loss."""
        torch.manual_seed(42)
        # Use a random orthogonal-ish matrix
        z = torch.randn(64, 32)
        loss_fn = SIGRegLoss()
        loss = loss_fn(z)
        assert loss.item() < 2.0  # Should be reasonably low

    def test_collapsed_vectors_higher_loss(self) -> None:
        """Collapsed vectors should have higher SIGReg loss than diverse ones."""
        torch.manual_seed(42)
        loss_fn = SIGRegLoss()

        # Diverse vectors: large eigenvalues -> sigmoid(large) ~ 1 -> -log(1) ~ 0
        z_diverse = torch.randn(64, 32)
        loss_diverse = loss_fn(z_diverse)

        # Collapsed vectors: eigenvalues ~ 0 -> sigmoid(0) = 0.5 -> -log(0.5) ~ 0.693
        z_collapsed = torch.ones(64, 32) * 0.5
        z_collapsed = z_collapsed + torch.randn_like(z_collapsed) * 1e-6
        loss_collapsed = loss_fn(z_collapsed)

        assert loss_collapsed.item() > loss_diverse.item()

    def test_single_sample_returns_zero(self) -> None:
        """Batch size 1 should return 0 (can't compute covariance)."""
        z = torch.randn(1, 32)
        loss_fn = SIGRegLoss()
        loss = loss_fn(z)
        assert loss.item() == 0.0

    def test_gradient_flows(self) -> None:
        """Gradients should flow through SIGReg."""
        z = torch.randn(16, 32, requires_grad=True)
        loss_fn = SIGRegLoss()
        loss = loss_fn(z)
        loss.backward()
        assert z.grad is not None


class TestCosinePredictionLoss:
    def test_identical_vectors_zero_loss(self) -> None:
        """Identical vectors should give near-zero loss."""
        pred = torch.randn(8, 64)
        target = pred.clone()
        loss_fn = CosinePredictionLoss()
        loss = loss_fn(pred, target)
        assert loss.item() < 1e-4

    def test_opposite_vectors_high_loss(self) -> None:
        """Opposite vectors should give high loss."""
        pred = torch.randn(8, 64)
        target = -pred
        loss_fn = CosinePredictionLoss()
        loss = loss_fn(pred, target)
        assert loss.item() > 100.0  # 2 * latent_dim = 128

    def test_scaling_by_dim(self) -> None:
        """Loss should scale with latent_dim."""
        pred = torch.randn(8, 128)
        target = torch.randn(8, 128)
        loss_fn = CosinePredictionLoss()
        loss = loss_fn(pred, target)
        # For random vectors, cosine sim ~ 0, so loss ~ 1 * dim = 128
        assert loss.item() > 50.0


class TestJEPALoss:
    def test_combined_loss(self) -> None:
        """JEPALoss should combine prediction and SIGReg losses."""
        torch.manual_seed(42)
        predictions = [torch.randn(16, 64) for _ in range(4)]
        targets = [torch.randn(16, 64) for _ in range(4)]
        loss_fn = JEPALoss(sigreg_weight=1.0)
        result = loss_fn(predictions, targets)
        assert "total" in result
        assert "prediction" in result
        assert "sigreg" in result
        assert result["total"].item() > 0
        # total = prediction + 1.0 * sigreg
        expected = result["prediction"] + 1.0 * result["sigreg"]
        assert torch.allclose(result["total"], expected, atol=1e-5)
