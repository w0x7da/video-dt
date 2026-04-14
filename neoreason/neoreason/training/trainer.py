"""Training loops for Reasoner (Phase 1) and Talker (Phase 2)."""

import logging
import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from neoreason.model.ema import EMAUpdater
from neoreason.model.reasoner import JEPAReasoner
from neoreason.training.losses import JEPALoss
from neoreason.training.scheduler import create_scheduler
from neoreason.training.utils import save_checkpoint

logger = logging.getLogger(__name__)


class ReasonerTrainer:
    """Phase 1: Pre-train the Reasoner with JEPA loss + SIGReg."""

    def __init__(
        self,
        reasoner: JEPAReasoner,
        train_loader: DataLoader,
        eval_loader: DataLoader | None = None,
        lr: float = 3e-4,
        weight_decay: float = 0.01,
        warmup_steps: int = 500,
        max_grad_norm: float = 1.0,
        sigreg_weight: float = 1.0,
        ema_momentum_initial: float = 0.996,
        ema_momentum_final: float = 0.999,
        epochs: int = 50,
        checkpoint_dir: str = "checkpoints",
        device: torch.device = torch.device("cpu"),
        scheduler_type: str = "cosine",
    ) -> None:
        self.reasoner = reasoner.to(device)
        self.train_loader = train_loader
        self.eval_loader = eval_loader
        self.device = device
        self.epochs = epochs
        self.max_grad_norm = max_grad_norm
        self.checkpoint_dir = checkpoint_dir

        # Optimizer only for online params
        self.optimizer = torch.optim.AdamW(
            reasoner.get_online_params(),
            lr=lr,
            weight_decay=weight_decay,
            betas=(0.9, 0.98),
        )

        # Total steps for scheduler
        total_steps = len(train_loader) * epochs
        self.scheduler = create_scheduler(
            self.optimizer, scheduler_type, warmup_steps, total_steps
        )

        # Loss
        self.criterion = JEPALoss(sigreg_weight=sigreg_weight)

        # EMA
        self.ema = EMAUpdater(
            momentum_initial=ema_momentum_initial,
            momentum_final=ema_momentum_final,
            total_steps=total_steps,
        )

        self.global_step = 0

    def train(self) -> None:
        """Run the full training loop."""
        logger.info(f"Starting Reasoner training for {self.epochs} epochs")
        logger.info(f"Total training steps: {len(self.train_loader) * self.epochs}")

        for epoch in range(self.epochs):
            self.reasoner.train()
            epoch_loss = 0.0
            epoch_pred_loss = 0.0
            epoch_sigreg_loss = 0.0
            n_batches = 0

            pbar = tqdm(self.train_loader, desc=f"Epoch {epoch + 1}/{self.epochs}")
            for batch in pbar:
                loss_dict = self._train_step(batch)
                epoch_loss += loss_dict["total"].item()
                epoch_pred_loss += loss_dict["prediction"].item()
                epoch_sigreg_loss += loss_dict["sigreg"].item()
                n_batches += 1

                pbar.set_postfix({
                    "loss": f"{loss_dict['total'].item():.4f}",
                    "pred": f"{loss_dict['prediction'].item():.4f}",
                    "sigreg": f"{loss_dict['sigreg'].item():.4f}",
                    "lr": f"{self.scheduler.get_last_lr()[0]:.2e}",
                })

            avg_loss = epoch_loss / max(n_batches, 1)
            avg_pred = epoch_pred_loss / max(n_batches, 1)
            avg_sigreg = epoch_sigreg_loss / max(n_batches, 1)
            logger.info(
                f"Epoch {epoch + 1}: loss={avg_loss:.4f} "
                f"pred={avg_pred:.4f} sigreg={avg_sigreg:.4f}"
            )

            # Save checkpoint each epoch
            save_checkpoint(
                os.path.join(self.checkpoint_dir, f"reasoner_epoch_{epoch + 1}.pt"),
                reasoner=self.reasoner,
                optimizer=self.optimizer,
                step=self.global_step,
                epoch=epoch + 1,
            )

        # Save final checkpoint
        save_checkpoint(
            os.path.join(self.checkpoint_dir, "reasoner_final.pt"),
            reasoner=self.reasoner,
            step=self.global_step,
            epoch=self.epochs,
        )
        logger.info("Reasoner training complete")

    def _train_step(self, batch: dict) -> dict[str, torch.Tensor]:
        """Execute a single training step.

        Args:
            batch: Dict with 'input_tokens' and 'step_tokens'.

        Returns:
            Loss dict with 'total', 'prediction', 'sigreg'.
        """
        input_tokens = batch["input_tokens"].to(self.device)
        step_tokens = [st.to(self.device) for st in batch["step_tokens"]]

        # Forward pass
        result = self.reasoner(input_tokens, step_tokens)

        # Compute loss
        loss_dict = self.criterion(result["predictions"], result["targets"])

        # Backward + optimize
        self.optimizer.zero_grad()
        loss_dict["total"].backward()
        nn.utils.clip_grad_norm_(
            self.reasoner.get_online_params(), self.max_grad_norm
        )
        self.optimizer.step()
        self.scheduler.step()

        # EMA update of target encoder
        online, target = self.reasoner.get_target_modules()
        self.ema.step(online, target, self.global_step)

        self.global_step += 1
        return loss_dict


class TalkerTrainer:
    """Phase 2: Train the Talker with the Reasoner frozen."""

    def __init__(
        self,
        reasoner: JEPAReasoner,
        talker: nn.Module,
        train_loader: DataLoader,
        eval_loader: DataLoader | None = None,
        lr: float = 1e-4,
        weight_decay: float = 0.01,
        warmup_steps: int = 200,
        max_grad_norm: float = 1.0,
        n_reasoning_steps: int = 8,
        epochs: int = 30,
        checkpoint_dir: str = "checkpoints",
        device: torch.device = torch.device("cpu"),
        scheduler_type: str = "cosine",
    ) -> None:
        self.device = device
        self.epochs = epochs
        self.max_grad_norm = max_grad_norm
        self.checkpoint_dir = checkpoint_dir
        self.n_reasoning_steps = n_reasoning_steps

        # Freeze Reasoner completely
        self.reasoner = reasoner.to(device)
        self.reasoner.eval()
        for p in self.reasoner.parameters():
            p.requires_grad = False

        self.talker = talker.to(device)
        self.train_loader = train_loader
        self.eval_loader = eval_loader

        # Optimizer for Talker only
        self.optimizer = torch.optim.AdamW(
            self.talker.parameters(),
            lr=lr,
            weight_decay=weight_decay,
            betas=(0.9, 0.98),
        )

        total_steps = len(train_loader) * epochs
        self.scheduler = create_scheduler(
            self.optimizer, scheduler_type, warmup_steps, total_steps
        )

        self.criterion = nn.CrossEntropyLoss(ignore_index=0)  # Ignore padding
        self.global_step = 0

    def train(self) -> None:
        """Run the full Talker training loop."""
        logger.info(f"Starting Talker training for {self.epochs} epochs")

        for epoch in range(self.epochs):
            self.talker.train()
            epoch_loss = 0.0
            n_batches = 0

            pbar = tqdm(self.train_loader, desc=f"Epoch {epoch + 1}/{self.epochs}")
            for batch in pbar:
                loss = self._train_step(batch)
                epoch_loss += loss.item()
                n_batches += 1
                pbar.set_postfix({
                    "loss": f"{loss.item():.4f}",
                    "lr": f"{self.scheduler.get_last_lr()[0]:.2e}",
                })

            avg_loss = epoch_loss / max(n_batches, 1)
            logger.info(f"Epoch {epoch + 1}: talker_loss={avg_loss:.4f}")

            save_checkpoint(
                os.path.join(self.checkpoint_dir, f"talker_epoch_{epoch + 1}.pt"),
                talker=self.talker,
                optimizer=self.optimizer,
                step=self.global_step,
                epoch=epoch + 1,
            )

        save_checkpoint(
            os.path.join(self.checkpoint_dir, "talker_final.pt"),
            talker=self.talker,
            step=self.global_step,
            epoch=self.epochs,
        )
        logger.info("Talker training complete")

    def _train_step(self, batch: dict) -> torch.Tensor:
        """Execute a single Talker training step.

        Args:
            batch: Dict with 'input_tokens' and 'target_tokens'.

        Returns:
            Scalar cross-entropy loss.
        """
        input_tokens = batch["input_tokens"].to(self.device)
        target_tokens = batch["target_tokens"].to(self.device)

        # Get latent trajectory from frozen Reasoner
        with torch.no_grad():
            trajectory = self.reasoner.reason(input_tokens, self.n_reasoning_steps)

        # Teacher forcing: predict target tokens from trajectory
        # Input to decoder: target_tokens[:-1], target: target_tokens[1:]
        decoder_input = target_tokens[:, :-1]
        decoder_target = target_tokens[:, 1:]

        logits = self.talker(trajectory, decoder_input)

        # Flatten for cross-entropy
        logits_flat = logits.reshape(-1, logits.shape[-1])
        target_flat = decoder_target.reshape(-1)
        loss = self.criterion(logits_flat, target_flat)

        # Backward + optimize
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.talker.parameters(), self.max_grad_norm)
        self.optimizer.step()
        self.scheduler.step()

        self.global_step += 1
        return loss
