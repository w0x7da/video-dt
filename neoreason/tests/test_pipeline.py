"""End-to-end pipeline tests."""

import torch

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.talker import DualTalker, MonoTalker, TalkerConfig
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.inference.pipeline import NeoReasonPipeline


def _make_small_pipeline(talker_type: str = "dual") -> NeoReasonPipeline:
    """Create a small pipeline for testing."""
    tokenizer = TokenizerWrapper(backend="simple")

    reasoner_config = ReasonerConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=64,
        n_heads=4,
        n_layers=2,
        d_ff=128,
        max_seq_len=64,
        latent_dim=64,
        max_reasoning_steps=4,
        dropout=0.0,
    )
    reasoner = JEPAReasoner(reasoner_config)

    talker_config = TalkerConfig(
        type=talker_type,
        vocab_size=tokenizer.vocab_size,
        d_model=64,
        n_heads=4,
        n_encoder_layers=2,
        n_decoder_layers=2,
        d_ff=128,
        max_seq_len=64,
        latent_dim=64,
        max_reasoning_steps=4,
        dropout=0.0,
    )
    if talker_type == "dual":
        talker = DualTalker(talker_config)
    else:
        talker = MonoTalker(talker_config)

    return NeoReasonPipeline(reasoner, talker, tokenizer, torch.device("cpu"))


class TestEndToEnd:
    def test_dual_talker_pipeline(self) -> None:
        """Full pipeline with DualTalker should produce non-empty text."""
        pipeline = _make_small_pipeline("dual")
        result = pipeline("What is 2 + 3?", n_reasoning_steps=3, max_tokens=16)
        assert isinstance(result.text, str)
        assert len(result.reasoning_trajectory) == 4  # z_0 + 3 steps
        assert result.total_time > 0

    def test_mono_talker_pipeline(self) -> None:
        """Full pipeline with MonoTalker should produce non-empty text."""
        pipeline = _make_small_pipeline("mono")
        result = pipeline("What is 2 + 3?", n_reasoning_steps=3, max_tokens=16)
        assert isinstance(result.text, str)
        assert len(result.reasoning_trajectory) == 4

    def test_trajectory_on_hypersphere(self) -> None:
        """All reasoning trajectory vectors should be on the unit hypersphere."""
        pipeline = _make_small_pipeline("dual")
        result = pipeline("Test question", n_reasoning_steps=4, max_tokens=8)
        for z in result.reasoning_trajectory:
            norms = torch.norm(z, dim=-1)
            assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_different_inputs_different_outputs(self) -> None:
        """Different inputs should produce different reasoning trajectories."""
        torch.manual_seed(42)
        pipeline = _make_small_pipeline("dual")
        result1 = pipeline("What is 2 + 3?", n_reasoning_steps=3, max_tokens=8)
        result2 = pipeline("Explain gravity", n_reasoning_steps=3, max_tokens=8)
        # Final latent vectors should differ
        z1 = result1.reasoning_trajectory[-1]
        z2 = result2.reasoning_trajectory[-1]
        cosine_sim = torch.nn.functional.cosine_similarity(z1, z2).item()
        assert cosine_sim < 0.99

    def test_timing_metrics(self) -> None:
        """Pipeline should report timing metrics."""
        pipeline = _make_small_pipeline("dual")
        result = pipeline("Hello", n_reasoning_steps=2, max_tokens=8)
        assert result.reasoning_time >= 0
        assert result.generation_time >= 0
        assert result.total_time >= result.reasoning_time
