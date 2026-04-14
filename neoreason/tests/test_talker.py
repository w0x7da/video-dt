"""Tests for the MonoTalker and DualTalker."""

import torch

from neoreason.model.talker import (
    MonoTalker,
    DualTalker,
    TalkerConfig,
    create_talker,
)


def _make_config(talker_type: str = "dual") -> TalkerConfig:
    return TalkerConfig(
        type=talker_type,
        vocab_size=500,
        d_model=64,
        n_heads=4,
        n_encoder_layers=2,
        n_decoder_layers=2,
        d_ff=128,
        max_seq_len=32,
        latent_dim=64,
        max_reasoning_steps=4,
        dropout=0.0,
    )


def _make_trajectory(batch: int = 2, n_steps: int = 4, dim: int = 64) -> list[torch.Tensor]:
    return [torch.randn(batch, dim) for _ in range(n_steps + 1)]


class TestMonoTalker:
    def test_output_shape(self) -> None:
        """Forward should return (batch, seq_len, vocab_size)."""
        config = _make_config("mono")
        talker = MonoTalker(config)
        trajectory = _make_trajectory(batch=2, n_steps=4, dim=64)
        target_tokens = torch.randint(0, 500, (2, 16))
        logits = talker(trajectory, target_tokens)
        assert logits.shape == (2, 16, 500)

    def test_generate_produces_tokens(self) -> None:
        """Generate should produce valid token IDs."""
        config = _make_config("mono")
        talker = MonoTalker(config)
        trajectory = _make_trajectory(batch=2, n_steps=4, dim=64)
        tokens = talker.generate(trajectory, max_tokens=8, temperature=1.0)
        assert tokens.shape[0] == 2
        assert tokens.shape[1] <= 8
        assert tokens.min() >= 0
        assert tokens.max() < 500

    def test_gradient_flow(self) -> None:
        """Gradients should flow through MonoTalker."""
        config = _make_config("mono")
        talker = MonoTalker(config)
        trajectory = [torch.randn(2, 64, requires_grad=True) for _ in range(5)]
        target_tokens = torch.randint(0, 500, (2, 8))
        logits = talker(trajectory, target_tokens)
        loss = logits.sum()
        loss.backward()
        assert trajectory[0].grad is not None


class TestDualTalker:
    def test_output_shape(self) -> None:
        """Forward should return (batch, seq_len, vocab_size)."""
        config = _make_config("dual")
        talker = DualTalker(config)
        trajectory = _make_trajectory(batch=2, n_steps=4, dim=64)
        target_tokens = torch.randint(0, 500, (2, 16))
        logits = talker(trajectory, target_tokens)
        assert logits.shape == (2, 16, 500)

    def test_generate_produces_tokens(self) -> None:
        """Generate should produce valid token IDs."""
        config = _make_config("dual")
        talker = DualTalker(config)
        trajectory = _make_trajectory(batch=2, n_steps=4, dim=64)
        tokens = talker.generate(trajectory, max_tokens=8, temperature=1.0)
        assert tokens.shape[0] == 2
        assert tokens.shape[1] <= 8
        assert tokens.min() >= 0
        assert tokens.max() < 500

    def test_cross_attention_influence(self) -> None:
        """Different latent trajectories should produce different outputs."""
        torch.manual_seed(42)
        config = _make_config("dual")
        talker = DualTalker(config)
        target_tokens = torch.randint(0, 500, (1, 8))

        traj1 = [torch.randn(1, 64) for _ in range(5)]
        traj2 = [torch.randn(1, 64) * 10 for _ in range(5)]

        logits1 = talker(traj1, target_tokens)
        logits2 = talker(traj2, target_tokens)

        # Different trajectories should give different logits
        assert not torch.allclose(logits1, logits2, atol=1e-3)

    def test_encode_latents_shape(self) -> None:
        """Encode latents should return (batch, n_steps+1, d_model)."""
        config = _make_config("dual")
        talker = DualTalker(config)
        trajectory = _make_trajectory(batch=3, n_steps=4, dim=64)
        memory = talker.encode_latents(trajectory)
        assert memory.shape == (3, 5, 64)

    def test_gradient_flow(self) -> None:
        """Gradients should flow through DualTalker."""
        config = _make_config("dual")
        talker = DualTalker(config)
        trajectory = [torch.randn(2, 64, requires_grad=True) for _ in range(5)]
        target_tokens = torch.randint(0, 500, (2, 8))
        logits = talker(trajectory, target_tokens)
        loss = logits.sum()
        loss.backward()
        assert trajectory[0].grad is not None


class TestCreateTalker:
    def test_create_mono(self) -> None:
        config = _make_config("mono")
        talker = create_talker(config)
        assert isinstance(talker, MonoTalker)

    def test_create_dual(self) -> None:
        config = _make_config("dual")
        talker = create_talker(config)
        assert isinstance(talker, DualTalker)

    def test_create_invalid(self) -> None:
        config = _make_config("invalid")
        try:
            create_talker(config)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
