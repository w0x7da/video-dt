"""Talker models: translate latent reasoning trajectories into text tokens.

The Talker does NOT reason. It is trained with the Reasoner FROZEN.
Two variants:
    - MonoTalker: decoder-only, for simple tasks without context.
    - DualTalker: encoder-decoder, for contextual tasks (conversation, etc.).
"""

import logging
import math
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

logger = logging.getLogger(__name__)


@dataclass
class TalkerConfig:
    """Configuration for the Talker models."""

    type: str = "dual"  # "mono" or "dual"
    vocab_size: int = 32000
    d_model: int = 256
    n_heads: int = 8
    n_encoder_layers: int = 3
    n_decoder_layers: int = 4
    d_ff: int = 1024
    max_seq_len: int = 512
    latent_dim: int = 256
    max_reasoning_steps: int = 8
    dropout: float = 0.1


class MonoTalker(nn.Module):
    """Decoder-only Talker for simple tasks.

    Takes a flattened latent trajectory as prefix, then generates
    tokens autoregressively.
    """

    def __init__(self, config: TalkerConfig) -> None:
        super().__init__()
        self.config = config

        # Project latent trajectory to a sequence of d_model vectors
        self.latent_proj = nn.Linear(config.latent_dim, config.d_model)
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_embedding = nn.Embedding(
            config.max_seq_len + config.max_reasoning_steps + 1,
            config.d_model,
        )

        decoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.n_heads,
            dim_feedforward=config.d_ff,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.decoder = nn.TransformerEncoder(
            decoder_layer,
            num_layers=config.n_decoder_layers,
        )

        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)

    def _build_causal_mask(self, seq_len: int, device: torch.device) -> Tensor:
        """Build a causal attention mask."""
        mask = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1)
        mask = mask.masked_fill(mask == 1, float("-inf"))
        return mask

    def forward(
        self,
        latent_trajectory: list[Tensor],
        target_tokens: Tensor,
    ) -> Tensor:
        """Training forward pass with teacher forcing.

        Args:
            latent_trajectory: List of latent vectors [z_0, ..., z_n],
                each of shape (batch, latent_dim).
            target_tokens: Target token IDs of shape (batch, seq_len).

        Returns:
            Logits of shape (batch, seq_len, vocab_size).
        """
        batch = target_tokens.shape[0]
        device = target_tokens.device

        # Project latent trajectory: each z -> d_model vector
        latent_seq = torch.stack(latent_trajectory, dim=1)  # (batch, n_steps+1, latent_dim)
        latent_embeds = self.latent_proj(latent_seq)  # (batch, n_steps+1, d_model)

        # Embed target tokens (shifted right for teacher forcing)
        token_embeds = self.token_embedding(target_tokens)  # (batch, seq_len, d_model)

        # Concatenate: [latent_embeds, token_embeds]
        combined = torch.cat([latent_embeds, token_embeds], dim=1)
        total_len = combined.shape[1]

        # Add positional embeddings
        positions = torch.arange(total_len, device=device).unsqueeze(0)
        combined = combined + self.pos_embedding(positions)

        # Causal mask over the full sequence
        causal_mask = self._build_causal_mask(total_len, device)

        # Decode
        hidden = self.decoder(combined, mask=causal_mask)

        # Only take the token part (skip latent prefix)
        n_latent = latent_seq.shape[1]
        token_hidden = hidden[:, n_latent:, :]

        logits = self.lm_head(token_hidden)
        return logits

    @torch.no_grad()
    def generate(
        self,
        latent_trajectory: list[Tensor],
        max_tokens: int = 256,
        temperature: float = 1.0,
        top_p: float = 0.9,
        eos_token_id: int | None = None,
    ) -> Tensor:
        """Autoregressive token generation.

        Args:
            latent_trajectory: List of latent vectors from the Reasoner.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0 = greedy).
            top_p: Nucleus sampling threshold.
            eos_token_id: Stop generation at this token.

        Returns:
            Generated token IDs of shape (batch, generated_len).
        """
        device = latent_trajectory[0].device
        batch = latent_trajectory[0].shape[0]

        latent_seq = torch.stack(latent_trajectory, dim=1)
        latent_embeds = self.latent_proj(latent_seq)
        n_latent = latent_embeds.shape[1]

        # Start with just the latent prefix
        generated = torch.zeros(batch, 0, dtype=torch.long, device=device)

        for _ in range(max_tokens):
            if generated.shape[1] > 0:
                token_embeds = self.token_embedding(generated)
                combined = torch.cat([latent_embeds, token_embeds], dim=1)
            else:
                combined = latent_embeds

            total_len = combined.shape[1]
            positions = torch.arange(total_len, device=device).unsqueeze(0)
            combined = combined + self.pos_embedding(positions)

            causal_mask = self._build_causal_mask(total_len, device)
            hidden = self.decoder(combined, mask=causal_mask)

            # Take last position logits
            last_logits = self.lm_head(hidden[:, -1, :])

            # Sample next token
            next_token = _sample_token(last_logits, temperature, top_p)
            generated = torch.cat([generated, next_token.unsqueeze(1)], dim=1)

            if eos_token_id is not None and (next_token == eos_token_id).all():
                break

        return generated


class DualTalker(nn.Module):
    """Encoder-decoder Talker for contextual tasks.

    The encoder processes the latent trajectory from the Reasoner.
    The decoder generates tokens with cross-attention to the encoded latents.
    """

    def __init__(self, config: TalkerConfig) -> None:
        super().__init__()
        self.config = config

        # Encoder: process latent trajectory
        self.latent_proj = nn.Linear(config.latent_dim, config.d_model)
        self.latent_pos = nn.Embedding(config.max_reasoning_steps + 1, config.d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.n_heads,
            dim_feedforward=config.d_ff,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=config.n_encoder_layers,
        )

        # Decoder: generate tokens with cross-attention
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.token_pos = nn.Embedding(config.max_seq_len, config.d_model)

        decoder_layer = nn.TransformerDecoderLayer(
            d_model=config.d_model,
            nhead=config.n_heads,
            dim_feedforward=config.d_ff,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.decoder = nn.TransformerDecoder(
            decoder_layer,
            num_layers=config.n_decoder_layers,
        )

        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)

    def _build_causal_mask(self, seq_len: int, device: torch.device) -> Tensor:
        mask = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1)
        mask = mask.masked_fill(mask == 1, float("-inf"))
        return mask

    def encode_latents(self, latent_trajectory: list[Tensor]) -> Tensor:
        """Encode the latent trajectory through the Talker encoder.

        Args:
            latent_trajectory: List of latent vectors [z_0, ..., z_n].

        Returns:
            Encoded memory of shape (batch, n_steps+1, d_model).
        """
        device = latent_trajectory[0].device
        latent_seq = torch.stack(latent_trajectory, dim=1)
        latent_embeds = self.latent_proj(latent_seq)

        n_latent = latent_embeds.shape[1]
        positions = torch.arange(n_latent, device=device).unsqueeze(0)
        latent_embeds = latent_embeds + self.latent_pos(positions)

        memory = self.encoder(latent_embeds)
        return memory

    def forward(
        self,
        latent_trajectory: list[Tensor],
        target_tokens: Tensor,
    ) -> Tensor:
        """Training forward pass with teacher forcing.

        Args:
            latent_trajectory: List of latent vectors from the Reasoner.
            target_tokens: Target token IDs of shape (batch, seq_len).

        Returns:
            Logits of shape (batch, seq_len, vocab_size).
        """
        device = target_tokens.device
        seq_len = target_tokens.shape[1]

        # Encode latent trajectory
        memory = self.encode_latents(latent_trajectory)

        # Embed target tokens
        token_embeds = self.token_embedding(target_tokens)
        positions = torch.arange(seq_len, device=device).unsqueeze(0)
        token_embeds = token_embeds + self.token_pos(positions)

        # Causal mask for decoder self-attention
        tgt_mask = self._build_causal_mask(seq_len, device)

        # Decode with cross-attention to encoded latents
        hidden = self.decoder(token_embeds, memory, tgt_mask=tgt_mask)
        logits = self.lm_head(hidden)
        return logits

    @torch.no_grad()
    def generate(
        self,
        latent_trajectory: list[Tensor],
        max_tokens: int = 256,
        temperature: float = 1.0,
        top_p: float = 0.9,
        eos_token_id: int | None = None,
    ) -> Tensor:
        """Autoregressive token generation with cross-attention to latents.

        Args:
            latent_trajectory: List of latent vectors from the Reasoner.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            top_p: Nucleus sampling threshold.
            eos_token_id: Stop generation at this token.

        Returns:
            Generated token IDs of shape (batch, generated_len).
        """
        device = latent_trajectory[0].device
        batch = latent_trajectory[0].shape[0]

        # Encode latents once
        memory = self.encode_latents(latent_trajectory)

        # Start with a BOS-like zero token
        generated = torch.zeros(batch, 1, dtype=torch.long, device=device)

        for _ in range(max_tokens):
            seq_len = generated.shape[1]
            token_embeds = self.token_embedding(generated)
            positions = torch.arange(seq_len, device=device).unsqueeze(0)
            token_embeds = token_embeds + self.token_pos(positions)

            tgt_mask = self._build_causal_mask(seq_len, device)
            hidden = self.decoder(token_embeds, memory, tgt_mask=tgt_mask)

            last_logits = self.lm_head(hidden[:, -1, :])
            next_token = _sample_token(last_logits, temperature, top_p)
            generated = torch.cat([generated, next_token.unsqueeze(1)], dim=1)

            if eos_token_id is not None and (next_token == eos_token_id).all():
                break

        # Remove the initial zero token
        return generated[:, 1:]


def _sample_token(logits: Tensor, temperature: float, top_p: float) -> Tensor:
    """Sample a token from logits using temperature and nucleus sampling.

    Args:
        logits: Logits of shape (batch, vocab_size).
        temperature: Sampling temperature. 0 = greedy.
        top_p: Nucleus sampling threshold.

    Returns:
        Sampled token IDs of shape (batch,).
    """
    if temperature <= 0:
        return logits.argmax(dim=-1)

    logits = logits / temperature
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

    # Remove tokens with cumulative probability above top_p
    sorted_indices_to_remove = cumulative_probs - F.softmax(sorted_logits, dim=-1) >= top_p
    sorted_logits[sorted_indices_to_remove] = float("-inf")

    # Scatter back to original ordering
    logits = torch.zeros_like(logits).scatter(1, sorted_indices, sorted_logits)
    probs = F.softmax(logits, dim=-1)
    return torch.multinomial(probs, num_samples=1).squeeze(-1)


def create_talker(config: TalkerConfig) -> nn.Module:
    """Factory function to create the appropriate Talker variant.

    Args:
        config: Talker configuration with 'type' field ("mono" or "dual").

    Returns:
        MonoTalker or DualTalker instance.
    """
    if config.type == "mono":
        return MonoTalker(config)
    elif config.type == "dual":
        return DualTalker(config)
    else:
        raise ValueError(f"Unknown talker type: {config.type}. Use 'mono' or 'dual'.")
