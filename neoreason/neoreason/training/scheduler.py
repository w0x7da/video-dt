"""Learning rate schedulers with warmup."""

import logging
import math

from torch.optim import Optimizer
from torch.optim.lr_scheduler import LambdaLR

logger = logging.getLogger(__name__)


def create_scheduler(
    optimizer: Optimizer,
    scheduler_type: str = "cosine",
    warmup_steps: int = 500,
    total_steps: int = 10000,
) -> LambdaLR:
    """Create a learning rate scheduler with linear warmup.

    Args:
        optimizer: The optimizer to schedule.
        scheduler_type: "cosine" for cosine annealing with warmup.
        warmup_steps: Number of warmup steps.
        total_steps: Total number of training steps.

    Returns:
        LambdaLR scheduler.
    """
    if scheduler_type == "cosine":

        def lr_lambda(step: int) -> float:
            if step < warmup_steps:
                return step / max(warmup_steps, 1)
            progress = (step - warmup_steps) / max(total_steps - warmup_steps, 1)
            return 0.5 * (1.0 + math.cos(math.pi * progress))

    elif scheduler_type == "linear":

        def lr_lambda(step: int) -> float:
            if step < warmup_steps:
                return step / max(warmup_steps, 1)
            progress = (step - warmup_steps) / max(total_steps - warmup_steps, 1)
            return max(1.0 - progress, 0.0)

    else:
        raise ValueError(f"Unknown scheduler type: {scheduler_type}")

    return LambdaLR(optimizer, lr_lambda)
