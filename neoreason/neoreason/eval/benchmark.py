"""Evaluation benchmarks for NeoReason."""

import logging
import re

from tqdm import tqdm

from neoreason.inference.pipeline import NeoReasonPipeline, NeoReasonResult

logger = logging.getLogger(__name__)


def extract_number(text: str) -> str | None:
    """Extract the final numeric answer from generated text.

    Looks for #### pattern first, then falls back to the last number.
    """
    # Try #### pattern (GSM8K format)
    match = re.search(r"####\s*([\d,.-]+)", text)
    if match:
        return match.group(1).replace(",", "").strip()

    # Fallback: last number in text
    numbers = re.findall(r"-?[\d,]+\.?\d*", text)
    if numbers:
        return numbers[-1].replace(",", "").strip()

    return None


def evaluate_gsm8k(
    pipeline: NeoReasonPipeline,
    dataset: list[dict],
    n_reasoning_steps: int = 8,
    max_output_tokens: int = 256,
    temperature: float = 0.0,
) -> dict[str, float]:
    """Evaluate the pipeline on GSM8K.

    Args:
        pipeline: The NeoReason inference pipeline.
        dataset: List of GSM8K samples with 'question' and 'answer' keys.
        n_reasoning_steps: Number of latent reasoning steps.
        max_output_tokens: Max tokens for generation.
        temperature: Sampling temperature.

    Returns:
        Dict with 'exact_match', 'total', 'correct' metrics.
    """
    correct = 0
    total = 0

    for sample in tqdm(dataset, desc="Evaluating GSM8K"):
        question = sample["question"]
        gold_answer = str(sample["answer"]).strip()

        result = pipeline(
            question,
            n_reasoning_steps=n_reasoning_steps,
            temperature=temperature,
            max_tokens=max_output_tokens,
        )

        predicted = extract_number(result.text)
        if predicted is not None and predicted == gold_answer:
            correct += 1
        total += 1

    em = correct / max(total, 1) * 100
    logger.info(f"GSM8K Exact Match: {em:.2f}% ({correct}/{total})")

    return {
        "exact_match": em,
        "correct": correct,
        "total": total,
    }


def evaluate_binary_tree(
    pipeline: NeoReasonPipeline,
    dataset: list[dict],
    n_reasoning_steps: int = 8,
    max_output_tokens: int = 128,
    temperature: float = 0.0,
) -> dict[str, float]:
    """Evaluate the pipeline on binary tree search.

    Args:
        pipeline: The NeoReason inference pipeline.
        dataset: List of binary tree samples with 'input_text' and 'solution_text'.
        n_reasoning_steps: Number of latent reasoning steps.
        max_output_tokens: Max tokens for generation.
        temperature: Sampling temperature.

    Returns:
        Dict with 'exact_match', 'total', 'correct' metrics.
    """
    correct = 0
    total = 0

    for sample in tqdm(dataset, desc="Evaluating Binary Tree"):
        input_text = sample["input_text"]
        gold_path = sample["solution_text"].strip()

        result = pipeline(
            input_text,
            n_reasoning_steps=n_reasoning_steps,
            temperature=temperature,
            max_tokens=max_output_tokens,
        )

        predicted = result.text.strip()
        if predicted == gold_path:
            correct += 1
        total += 1

    em = correct / max(total, 1) * 100
    logger.info(f"Binary Tree Exact Match: {em:.2f}% ({correct}/{total})")

    return {
        "exact_match": em,
        "correct": correct,
        "total": total,
    }
