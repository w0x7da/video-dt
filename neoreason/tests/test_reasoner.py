"""Tests for the JEPA Reasoner."""

import torch
import torch.nn.functional as F

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.ema import EMAUpdater


def _make_config() -> ReasonerConfig:
    return ReasonerConfig(
        vocab_size=1000,
        d_model=64,
        n_heads=4,
        n_layers=2,
        d_ff=128,
        max_seq_len=64,
        latent_dim=64,
        max_reasoning_steps=4,
        dropout=0.0,
    )


class TestJEPAReasoner:
    def test_reasoning_trajectory_shapes(self) -> None:
        """Trajectory should have n_steps+1 vectors of shape (batch, latent_dim)."""
        config = _make_config()
        reasoner = JEPAReasoner(config)
        tokens = torch.randint(0, 1000, (4, 32))
        trajectory = reasoner.reason(tokens, n_steps=4)
        assert len(trajectory) == 5  # z_0 + 4 steps
        for z in trajectory:
            assert z.shape == (4, 64)

    def test_all_latents_on_unit_sphere(self) -> None:
        """Every latent in the trajectory must have L2 norm = 1."""
        config = _make_config()
        reasoner = JEPAReasoner(config)
        tokens = torch.randint(0, 1000, (8, 16))
        trajectory = reasoner.reason(tokens, n_steps=6)
        for z in trajectory:
            norms = torch.norm(z, dim=-1)
            assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_no_collapse(self) -> None:
        """Different inputs should produce different trajectories."""
        torch.manual_seed(42)
        config = _make_config()
        reasoner = JEPAReasoner(config)
        tokens1 = torch.randint(0, 1000, (1, 32))
        tokens2 = torch.randint(0, 1000, (1, 32))
        traj1 = reasoner.reason(tokens1, n_steps=4)
        traj2 = reasoner.reason(tokens2, n_steps=4)
        # Final latents should be different
        cosine_sim = F.cosine_similarity(traj1[-1], traj2[-1])
        assert cosine_sim.item() < 0.99

    def test_ema_updates_target_encoder(self) -> None:
        """EMA update should change target encoder weights."""
        config = _make_config()
        reasoner = JEPAReasoner(config)
        # Store original target weights
        orig_weight = reasoner.target_embedding.weight.data.clone()

        # Modify online weights slightly
        with torch.no_grad():
            reasoner.embedding.weight.data += 0.1

        # Do EMA update
        online, target = reasoner.get_target_modules()
        ema = EMAUpdater(momentum_initial=0.9, momentum_final=0.9, total_steps=1)
        ema.step(online, target, step=0)

        # Target should have changed
        assert not torch.allclose(
            reasoner.target_embedding.weight.data, orig_weight, atol=1e-6
        )

    def test_predictor_gradient_flow(self) -> None:
        """Gradients should flow through the predictor to the embeddings."""
        config = _make_config()
        reasoner = JEPAReasoner(config)
        tokens = torch.randint(0, 1000, (4, 16))
        trajectory = reasoner.reason(tokens, n_steps=3)
        loss = trajectory[-1].sum()
        loss.backward()
        # Check embedding gradients exist
        assert reasoner.embedding.weight.grad is not None
        assert reasoner.embedding.weight.grad.abs().sum() > 0

    def test_forward_training(self) -> None:
        """Training forward pass should return predictions and targets."""
        config = _make_config()
        reasoner = JEPAReasoner(config)
        input_tokens = torch.randint(0, 1000, (4, 16))
        step_tokens = [torch.randint(0, 1000, (4, 8)) for _ in range(3)]

        result = reasoner.forward(input_tokens, step_tokens)

        assert "predictions" in result
        assert "targets" in result
        assert len(result["predictions"]) == 3
        assert len(result["targets"]) == 3
        for pred, tgt in zip(result["predictions"], result["targets"]):
            assert pred.shape == (4, 64)
            assert tgt.shape == (4, 64)

    def test_target_encoder_no_grad(self) -> None:
        """Target encoder parameters should not require gradients."""
        config = _make_config()
        reasoner = JEPAReasoner(config)
        for p in reasoner.target_embedding.parameters():
            assert not p.requires_grad
        for p in reasoner.target_pos_embedding.parameters():
            assert not p.requires_grad

    def test_encode_target_no_grad(self) -> None:
        """encode_target should not create a computation graph."""
        config = _make_config()
        reasoner = JEPAReasoner(config)
        tokens = torch.randint(0, 1000, (2, 8))
        z = reasoner.encode_target(tokens)
        assert not z.requires_grad
