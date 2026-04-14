"""Beam search decoding for the Talker."""

import logging

import torch
import torch.nn.functional as F
from torch import Tensor

logger = logging.getLogger(__name__)


@torch.no_grad()
def beam_search(
    talker: torch.nn.Module,
    latent_trajectory: list[Tensor],
    beam_width: int = 4,
    max_tokens: int = 256,
    eos_token_id: int | None = None,
    length_penalty: float = 1.0,
) -> list[tuple[list[int], float]]:
    """Beam search decoding for the Talker.

    Args:
        talker: The Talker model (DualTalker or MonoTalker).
        latent_trajectory: Latent reasoning trajectory from the Reasoner.
        beam_width: Number of beams to maintain.
        max_tokens: Maximum output length.
        eos_token_id: End of sequence token ID.
        length_penalty: Penalty for shorter sequences (> 1 favors longer).

    Returns:
        List of (token_ids, score) tuples sorted by score (best first).
    """
    device = latent_trajectory[0].device

    # Encode latents once if DualTalker
    if hasattr(talker, "encode_latents"):
        memory = talker.encode_latents(latent_trajectory)
    else:
        memory = None

    # Initialize beams: (token_sequence, cumulative_log_prob)
    beams: list[tuple[list[int], float]] = [([0], 0.0)]  # Start with token 0
    completed: list[tuple[list[int], float]] = []

    for _ in range(max_tokens):
        if not beams:
            break

        all_candidates: list[tuple[list[int], float]] = []

        for seq, score in beams:
            tokens = torch.tensor([seq], dtype=torch.long, device=device)

            if memory is not None:
                # DualTalker path
                token_embeds = talker.token_embedding(tokens)
                positions = torch.arange(tokens.shape[1], device=device).unsqueeze(0)
                token_embeds = token_embeds + talker.token_pos(positions)
                tgt_mask = talker._build_causal_mask(tokens.shape[1], device)
                hidden = talker.decoder(token_embeds, memory, tgt_mask=tgt_mask)
                logits = talker.lm_head(hidden[:, -1, :])
            else:
                # MonoTalker fallback — use full forward and take last position
                fake_target = tokens[:, 1:] if tokens.shape[1] > 1 else tokens
                logits_all = talker(latent_trajectory, fake_target)
                logits = logits_all[:, -1, :]

            log_probs = F.log_softmax(logits, dim=-1).squeeze(0)

            # Get top-k candidates
            top_log_probs, top_indices = torch.topk(log_probs, beam_width)

            for log_p, idx in zip(top_log_probs.tolist(), top_indices.tolist()):
                new_seq = seq + [idx]
                new_score = score + log_p

                if eos_token_id is not None and idx == eos_token_id:
                    # Apply length penalty
                    normalized_score = new_score / (len(new_seq) ** length_penalty)
                    completed.append((new_seq, normalized_score))
                else:
                    all_candidates.append((new_seq, new_score))

        # Keep top beam_width candidates
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        beams = all_candidates[:beam_width]

        if len(completed) >= beam_width:
            break

    # Add remaining beams to completed
    for seq, score in beams:
        normalized_score = score / (len(seq) ** length_penalty)
        completed.append((seq, normalized_score))

    # Sort by score
    completed.sort(key=lambda x: x[1], reverse=True)

    # Remove the initial 0 token from sequences
    result = [(seq[1:], score) for seq, score in completed]
    return result
