"""Full inference pipeline: text -> Reasoner -> Talker -> text."""

import logging
import os
import time
from dataclasses import dataclass, field

import torch
import torch.nn as nn
from torch import Tensor

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.talker import TalkerConfig, create_talker
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.training.utils import load_checkpoint, get_device

logger = logging.getLogger(__name__)


@dataclass
class NeoReasonResult:
    """Result of a NeoReason inference."""

    text: str
    reasoning_trajectory: list[Tensor] = field(default_factory=list)
    reasoning_time: float = 0.0
    generation_time: float = 0.0
    total_time: float = 0.0


class NeoReasonPipeline:
    """End-to-end inference pipeline: input text -> reasoning -> output text."""

    def __init__(
        self,
        reasoner: JEPAReasoner,
        talker: nn.Module,
        tokenizer: TokenizerWrapper,
        device: torch.device = torch.device("cpu"),
    ) -> None:
        self.reasoner = reasoner.to(device).eval()
        self.talker = talker.to(device).eval()
        self.tokenizer = tokenizer
        self.device = device

    @classmethod
    def from_pretrained(
        cls,
        checkpoint_dir: str,
        reasoner_config: ReasonerConfig | None = None,
        talker_config: TalkerConfig | None = None,
        tokenizer_backend: str = "tiktoken",
        device: str = "auto",
    ) -> "NeoReasonPipeline":
        """Load a pretrained pipeline from checkpoint directory.

        Args:
            checkpoint_dir: Directory containing reasoner_final.pt and talker_final.pt.
            reasoner_config: Reasoner config (required if not in checkpoint).
            talker_config: Talker config (required if not in checkpoint).
            tokenizer_backend: "tiktoken" or "huggingface".
            device: Device preference.

        Returns:
            Loaded NeoReasonPipeline.
        """
        dev = get_device(device)
        tokenizer = TokenizerWrapper(backend=tokenizer_backend)

        # Use default small config if not provided
        if reasoner_config is None:
            reasoner_config = ReasonerConfig(vocab_size=tokenizer.vocab_size)
        if talker_config is None:
            talker_config = TalkerConfig(vocab_size=tokenizer.vocab_size)

        reasoner = JEPAReasoner(reasoner_config)
        talker = create_talker(talker_config)

        # Load weights
        reasoner_path = os.path.join(checkpoint_dir, "reasoner_final.pt")
        talker_path = os.path.join(checkpoint_dir, "talker_final.pt")

        if os.path.exists(reasoner_path):
            load_checkpoint(reasoner_path, reasoner=reasoner, device=dev)
        else:
            logger.warning(f"No reasoner checkpoint at {reasoner_path}")

        if os.path.exists(talker_path):
            load_checkpoint(talker_path, talker=talker, device=dev)
        else:
            logger.warning(f"No talker checkpoint at {talker_path}")

        return cls(reasoner, talker, tokenizer, dev)

    @torch.no_grad()
    def __call__(
        self,
        text: str,
        n_reasoning_steps: int = 8,
        temperature: float = 0.0,
        top_p: float = 0.9,
        max_tokens: int = 256,
    ) -> NeoReasonResult:
        """Run the full pipeline.

        Args:
            text: Input text (question/problem).
            n_reasoning_steps: Number of latent reasoning steps.
            temperature: Sampling temperature for the Talker.
            top_p: Nucleus sampling threshold.
            max_tokens: Maximum output tokens.

        Returns:
            NeoReasonResult with generated text and reasoning trajectory.
        """
        start = time.time()

        # Tokenize (truncate to max_seq_len)
        token_ids = self.tokenizer.encode(text)
        max_len = self.reasoner.config.max_seq_len
        token_ids = token_ids[:max_len]
        input_tokens = torch.tensor([token_ids], dtype=torch.long, device=self.device)

        # Reason
        t_reason = time.time()
        trajectory = self.reasoner.reason(input_tokens, n_reasoning_steps)
        reasoning_time = time.time() - t_reason

        # Generate
        t_gen = time.time()
        output_ids = self.talker.generate(
            trajectory,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        generation_time = time.time() - t_gen

        # Decode
        output_text = self.tokenizer.decode(output_ids[0].tolist())
        total_time = time.time() - start

        return NeoReasonResult(
            text=output_text,
            reasoning_trajectory=trajectory,
            reasoning_time=reasoning_time,
            generation_time=generation_time,
            total_time=total_time,
        )
