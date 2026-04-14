"""JEPA-Reasoner: reasons in continuous latent space, never generates tokens."""

import copy
import logging
import math
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from neoreason.model.normalization import HybridNorm

logger = logging.getLogger(__name__)


@dataclass
class ReasonerConfig:
    """Configuration for the JEPA Reasoner."""

    vocab_size: int = 32000
    d_model: int = 256
    n_heads: int = 8
    n_layers: int = 6
    d_ff: int = 1024
    max_seq_len: int = 512
    latent_dim: int = 256
    max_reasoning_steps: int = 8
    dropout: float = 0.1


class QKNormMultiheadAttention(nn.Module):
    """Multi-head attention with non-learnable QK normalization.

    Q and K are L2-normalized before the dot product, which stabilizes
    training by preventing attention logit explosion.
    """

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1) -> None:
        super().__init__()
        assert d_model % n_heads == 0
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: Tensor, attn_mask: Tensor | None = None) -> Tensor:
        """Forward pass with QK-normalized attention.

        Args:
            x: Input of shape (batch, seq_len, d_model).
            attn_mask: Optional attention mask.

        Returns:
            Output of shape (batch, seq_len, d_model).
        """
        batch, seq_len, _ = x.shape

        q = self.q_proj(x).view(batch, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        # Non-learnable QK normalization: L2-normalize Q and K
        q = F.normalize(q, p=2, dim=-1)
        k = F.normalize(k, p=2, dim=-1)

        # Scaled dot-product attention (scale by sqrt(head_dim) still applied)
        scale = math.sqrt(self.head_dim)
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) * scale

        if attn_mask is not None:
            attn_weights = attn_weights + attn_mask

        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_weights = self.dropout(attn_weights)

        out = torch.matmul(attn_weights, v)
        out = out.transpose(1, 2).contiguous().view(batch, seq_len, self.d_model)
        out = self.out_proj(out)
        return out


class PredictorBlock(nn.Module):
    """Pre-LN Transformer block with QK-Norm attention for the predictor."""

    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = QKNormMultiheadAttention(d_model, n_heads, dropout)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: Tensor) -> Tensor:
        """Pre-LN transformer block: norm -> attn -> residual -> norm -> ffn -> residual."""
        x = x + self.attn(self.norm1(x))
        x = x + self.ffn(self.norm2(x))
        return x


class JEPAReasoner(nn.Module):
    """JEPA-Reasoner: autoregressive reasoning in continuous latent space.

    Components:
        1. Token Embedding Layer — maps tokens to d_model space
        2. Target Encoder — EMA copy of embedding, provides stable targets
        3. Predictor — Modified Transformer blocks with QK-Norm
        4. HybridNorm — projects latent vectors onto unit hypersphere

    The Reasoner NEVER generates tokens. It produces a trajectory of
    latent vectors [z_0, z_1, ..., z_n] on the unit hypersphere.
    """

    def __init__(self, config: ReasonerConfig) -> None:
        super().__init__()
        self.config = config

        # Input encoder: tokens -> latent space
        self.embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_embedding = nn.Embedding(config.max_seq_len, config.d_model)

        # Target encoder: deep copy of embedding, updated via EMA
        self.target_embedding = copy.deepcopy(self.embedding)
        self.target_pos_embedding = copy.deepcopy(self.pos_embedding)
        # Freeze target encoder — only updated via EMA
        for p in self.target_embedding.parameters():
            p.requires_grad = False
        for p in self.target_pos_embedding.parameters():
            p.requires_grad = False

        # Predictor: transformer blocks with QK-Norm
        self.predictor_blocks = nn.ModuleList([
            PredictorBlock(config.d_model, config.n_heads, config.d_ff, config.dropout)
            for _ in range(config.n_layers)
        ])

        # Hybrid normalization: RMS + L2 -> unit hypersphere
        self.hybrid_norm = HybridNorm(config.latent_dim)

    def _embed_and_pool(
        self,
        tokens: Tensor,
        embedding: nn.Embedding,
        pos_embedding: nn.Embedding,
    ) -> Tensor:
        """Embed tokens and mean-pool to a single latent vector.

        Args:
            tokens: Token IDs of shape (batch, seq_len).
            embedding: The embedding layer to use.
            pos_embedding: The positional embedding layer.

        Returns:
            Pooled latent vector of shape (batch, d_model).
        """
        seq_len = tokens.shape[1]
        positions = torch.arange(seq_len, device=tokens.device).unsqueeze(0)
        x = embedding(tokens) + pos_embedding(positions)
        # Mean pooling over the sequence dimension
        z = x.mean(dim=1)
        return z

    def encode(self, tokens: Tensor) -> Tensor:
        """Encode input tokens to initial latent vector z_0 on the hypersphere.

        Args:
            tokens: Token IDs of shape (batch, seq_len).

        Returns:
            Normalized latent vector z_0 of shape (batch, latent_dim).
        """
        z = self._embed_and_pool(tokens, self.embedding, self.pos_embedding)
        return self.hybrid_norm(z)

    @torch.no_grad()
    def encode_target(self, tokens: Tensor) -> Tensor:
        """Encode tokens using the target (EMA) encoder. No gradients.

        Args:
            tokens: Token IDs of shape (batch, seq_len).

        Returns:
            Normalized target latent vector of shape (batch, latent_dim).
        """
        z = self._embed_and_pool(tokens, self.target_embedding, self.target_pos_embedding)
        return self.hybrid_norm(z)

    def predict_next(self, z: Tensor) -> Tensor:
        """Predict the next latent vector from the current one.

        Args:
            z: Current latent vector of shape (batch, latent_dim).

        Returns:
            Next predicted latent vector on the hypersphere, shape (batch, latent_dim).
        """
        # Reshape to (batch, 1, d_model) for transformer blocks
        x = z.unsqueeze(1)
        for block in self.predictor_blocks:
            x = block(x)
        # Extract single output and normalize
        z_next = x.squeeze(1)
        return self.hybrid_norm(z_next)

    def reason(self, input_tokens: Tensor, n_steps: int) -> list[Tensor]:
        """Autoregressive reasoning in latent space.

        Args:
            input_tokens: Token IDs of shape (batch, seq_len).
            n_steps: Number of reasoning steps.

        Returns:
            Trajectory [z_0, z_1, ..., z_n] — list of (n_steps + 1) tensors,
            each of shape (batch, latent_dim), all on the unit hypersphere.
        """
        z = self.encode(input_tokens)
        trajectory = [z]

        for _ in range(n_steps):
            z = self.predict_next(z)
            trajectory.append(z)

        return trajectory

    def forward(
        self,
        input_tokens: Tensor,
        target_tokens_per_step: list[Tensor],
    ) -> dict[str, list[Tensor]]:
        """Training forward pass.

        Args:
            input_tokens: Token IDs for the question, shape (batch, seq_len).
            target_tokens_per_step: List of token ID tensors, one per reasoning step.
                Each target represents the text of one reasoning step.

        Returns:
            Dict with 'predictions' and 'targets' lists of latent vectors.
        """
        n_steps = len(target_tokens_per_step)

        # Encode input -> z_0
        z = self.encode(input_tokens)

        predictions = []
        targets = []

        for step_tokens in target_tokens_per_step:
            # Predict next latent
            z_pred = self.predict_next(z)
            predictions.append(z_pred)

            # Target: encode the step text with the EMA encoder
            z_target = self.encode_target(step_tokens)
            targets.append(z_target)

            # Use prediction as next input (autoregressive)
            z = z_pred

        return {"predictions": predictions, "targets": targets}

    def get_online_params(self) -> list[nn.Parameter]:
        """Return parameters of the online encoder + predictor (for optimizer)."""
        params = []
        params.extend(self.embedding.parameters())
        params.extend(self.pos_embedding.parameters())
        params.extend(self.predictor_blocks.parameters())
        # HybridNorm has no learnable params
        return params

    def get_target_modules(self) -> tuple[nn.ModuleList, nn.ModuleList]:
        """Return (online_modules, target_modules) for EMA updates."""
        online = nn.ModuleList([self.embedding, self.pos_embedding])
        target = nn.ModuleList([self.target_embedding, self.target_pos_embedding])
        return online, target
