"""GSM8K dataset loader for math reasoning evaluation."""

import logging
import re

from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


def _parse_answer(answer_text: str) -> tuple[list[str], str]:
    """Parse a GSM8K answer into reasoning steps and final number.

    Args:
        answer_text: Raw answer string like "Step1\\nStep2\\n#### 42"

    Returns:
        (steps, final_answer) where steps is a list of reasoning step strings
        and final_answer is the numeric answer after ####.
    """
    parts = answer_text.split("####")
    if len(parts) == 2:
        reasoning = parts[0].strip()
        final = parts[1].strip().replace(",", "")
    else:
        reasoning = answer_text.strip()
        final = ""

    # Split reasoning into steps (by newlines)
    steps = [s.strip() for s in reasoning.split("\n") if s.strip()]
    return steps, final


class GSM8KDataset(Dataset):
    """GSM8K math reasoning dataset.

    Each sample contains:
        - question: the math problem text
        - steps: list of reasoning step strings
        - answer: the final numeric answer
        - full_solution: the complete solution text
    """

    def __init__(self, split: str = "train") -> None:
        """Load GSM8K from HuggingFace datasets.

        Args:
            split: "train" (7473 examples) or "test" (1319 examples).
        """
        super().__init__()
        try:
            from datasets import load_dataset
            ds = load_dataset("gsm8k", "main", split=split)
        except Exception as e:
            logger.warning(f"Failed to load GSM8K from HuggingFace: {e}")
            logger.warning("Using empty dataset. Install 'datasets' and ensure network access.")
            self.samples: list[dict[str, str | list[str]]] = []
            return

        self.samples = []
        for item in ds:
            question = item["question"]
            answer_text = item["answer"]
            steps, final_answer = _parse_answer(answer_text)

            self.samples.append({
                "question": question,
                "steps": steps,
                "answer": final_answer,
                "full_solution": answer_text,
            })

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, str | list[str]]:
        return self.samples[idx]
