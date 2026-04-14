"""Data collator for batching and padding NeoReason samples."""

import logging

import torch
from torch import Tensor

from neoreason.model.tokenizer_wrapper import TokenizerWrapper

logger = logging.getLogger(__name__)


class NeoReasonCollator:
    """Collator that tokenizes and pads samples for the Reasoner or Talker.

    Handles variable-length reasoning steps by tokenizing each step separately.
    """

    def __init__(
        self,
        tokenizer: TokenizerWrapper,
        max_seq_len: int = 512,
        max_step_len: int = 128,
        max_steps: int = 8,
    ) -> None:
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.max_step_len = max_step_len
        self.max_steps = max_steps

    def _tokenize_and_pad(self, texts: list[str], max_len: int) -> Tensor:
        """Tokenize and pad a list of texts to the same length.

        Args:
            texts: List of text strings.
            max_len: Maximum token length.

        Returns:
            Padded tensor of shape (len(texts), padded_len).
        """
        encoded = self.tokenizer.batch_encode(texts, max_length=max_len)
        return torch.tensor(encoded["input_ids"], dtype=torch.long)

    def collate_reasoner(
        self, batch: list[dict]
    ) -> dict[str, Tensor | list[Tensor]]:
        """Collate a batch for Reasoner training.

        Expects each sample to have 'input_text' and 'steps_text'.

        Returns:
            Dict with:
                - input_tokens: (batch_size, seq_len)
                - step_tokens: list of (batch_size, step_len) tensors
        """
        input_texts = []
        all_steps: list[list[str]] = []

        for sample in batch:
            # Support both 'input_text' (binary tree) and 'question' (GSM8K)
            text = sample.get("input_text") or sample.get("question", "")
            input_texts.append(text)

            steps = sample.get("steps_text") or sample.get("steps", [])
            # Truncate to max_steps
            all_steps.append(steps[: self.max_steps])

        # Tokenize inputs
        input_tokens = self._tokenize_and_pad(input_texts, self.max_seq_len)

        # Tokenize each step across the batch
        # Pad the number of steps to the maximum in this batch
        max_n_steps = max(len(s) for s in all_steps) if all_steps else 1
        step_tokens_list = []
        for step_idx in range(max_n_steps):
            step_texts = []
            for steps in all_steps:
                if step_idx < len(steps):
                    step_texts.append(steps[step_idx])
                else:
                    step_texts.append("")  # Pad with empty
            step_tokens = self._tokenize_and_pad(step_texts, self.max_step_len)
            step_tokens_list.append(step_tokens)

        return {
            "input_tokens": input_tokens,
            "step_tokens": step_tokens_list,
        }

    def collate_talker(
        self, batch: list[dict]
    ) -> dict[str, Tensor]:
        """Collate a batch for Talker training.

        Expects each sample to have 'input_text'/'question' and
        'solution_text'/'full_solution'.

        Returns:
            Dict with:
                - input_tokens: (batch_size, seq_len)
                - target_tokens: (batch_size, target_len)
        """
        input_texts = []
        target_texts = []

        for sample in batch:
            text = sample.get("input_text") or sample.get("question", "")
            input_texts.append(text)

            solution = sample.get("solution_text") or sample.get("full_solution", "")
            target_texts.append(solution)

        input_tokens = self._tokenize_and_pad(input_texts, self.max_seq_len)
        target_tokens = self._tokenize_and_pad(target_texts, self.max_seq_len)

        return {
            "input_tokens": input_tokens,
            "target_tokens": target_tokens,
        }
