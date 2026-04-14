"""Exponential Moving Average updater for the target encoder."""

import logging

import torch.nn as nn

logger = logging.getLogger(__name__)


class EMAUpdater:
    """Updates target model parameters as an EMA of online model parameters.

    momentum(step) = momentum_initial + (momentum_final - momentum_initial) * step / total_steps

    target_params = momentum * target_params + (1 - momentum) * online_params
    """

    def __init__(
        self,
        momentum_initial: float = 0.996,
        momentum_final: float = 0.999,
        total_steps: int = 10000,
    ) -> None:
        self.momentum_initial = momentum_initial
        self.momentum_final = momentum_final
        self.total_steps = max(total_steps, 1)

    def get_momentum(self, step: int) -> float:
        """Compute linearly interpolated momentum for the current step."""
        ratio = min(step / self.total_steps, 1.0)
        return self.momentum_initial + (self.momentum_final - self.momentum_initial) * ratio

    @staticmethod
    def update(
        online_model: nn.Module,
        target_model: nn.Module,
        momentum: float,
    ) -> None:
        """Update target model parameters via EMA.

        Args:
            online_model: The model being trained (source of new params).
            target_model: The EMA model (to be updated).
            momentum: Current EMA momentum value.
        """
        for online_param, target_param in zip(
            online_model.parameters(), target_model.parameters()
        ):
            target_param.data.mul_(momentum).add_(
                online_param.data, alpha=1.0 - momentum
            )

    def step(
        self,
        online_model: nn.Module,
        target_model: nn.Module,
        step: int,
    ) -> float:
        """Perform one EMA update step.

        Args:
            online_model: The model being trained.
            target_model: The EMA model.
            step: Current training step.

        Returns:
            The momentum value used for this step.
        """
        momentum = self.get_momentum(step)
        self.update(online_model, target_model, momentum)
        return momentum
