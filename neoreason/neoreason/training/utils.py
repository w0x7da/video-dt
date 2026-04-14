"""Training utilities: device detection, seeding, checkpointing."""

import logging
import os
import random

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


def get_device(preference: str = "auto") -> torch.device:
    """Auto-detect the best available device.

    Args:
        preference: "auto", "cuda", "mps", or "cpu".

    Returns:
        torch.device for the selected backend.
    """
    if preference == "auto":
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
    else:
        device = torch.device(preference)

    logger.info(f"Using device: {device}")
    return device


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    logger.info(f"Random seed set to {seed}")


def save_checkpoint(
    path: str,
    reasoner: nn.Module | None = None,
    talker: nn.Module | None = None,
    optimizer: torch.optim.Optimizer | None = None,
    step: int = 0,
    epoch: int = 0,
    extra: dict | None = None,
) -> None:
    """Save a training checkpoint.

    Args:
        path: File path for the checkpoint.
        reasoner: Reasoner model (optional).
        talker: Talker model (optional).
        optimizer: Optimizer state (optional).
        step: Current training step.
        epoch: Current epoch.
        extra: Additional data to save.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ckpt = {"step": step, "epoch": epoch}

    if reasoner is not None:
        ckpt["reasoner_state_dict"] = reasoner.state_dict()
    if talker is not None:
        ckpt["talker_state_dict"] = talker.state_dict()
    if optimizer is not None:
        ckpt["optimizer_state_dict"] = optimizer.state_dict()
    if extra is not None:
        ckpt.update(extra)

    torch.save(ckpt, path)
    logger.info(f"Checkpoint saved to {path} (step={step}, epoch={epoch})")


def load_checkpoint(
    path: str,
    reasoner: nn.Module | None = None,
    talker: nn.Module | None = None,
    optimizer: torch.optim.Optimizer | None = None,
    device: torch.device | None = None,
) -> dict:
    """Load a training checkpoint.

    Args:
        path: File path of the checkpoint.
        reasoner: Reasoner model to load weights into.
        talker: Talker model to load weights into.
        optimizer: Optimizer to load state into.
        device: Device to map tensors to.

    Returns:
        The full checkpoint dict (for accessing step, epoch, etc.).
    """
    map_location = device if device else "cpu"
    ckpt = torch.load(path, map_location=map_location, weights_only=False)

    if reasoner is not None and "reasoner_state_dict" in ckpt:
        reasoner.load_state_dict(ckpt["reasoner_state_dict"])
        logger.info("Loaded reasoner weights from checkpoint")
    if talker is not None and "talker_state_dict" in ckpt:
        talker.load_state_dict(ckpt["talker_state_dict"])
        logger.info("Loaded talker weights from checkpoint")
    if optimizer is not None and "optimizer_state_dict" in ckpt:
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        logger.info("Loaded optimizer state from checkpoint")

    return ckpt


def count_parameters(model: nn.Module) -> int:
    """Count the number of trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def setup_logging(log_dir: str | None = None) -> None:
    """Configure logging with optional file output."""
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(os.path.join(log_dir, "train.log")))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=handlers,
    )
