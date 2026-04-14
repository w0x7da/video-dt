"""Phase 1: Pre-train the JEPA Reasoner on latent reasoning."""

import logging
import sys
import os

import hydra
from omegaconf import DictConfig
from torch.utils.data import DataLoader

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.data.text_pairs import BinaryTreeDataset
from neoreason.data.gsm8k import GSM8KDataset
from neoreason.data.collator import NeoReasonCollator
from neoreason.training.trainer import ReasonerTrainer
from neoreason.training.utils import (
    get_device,
    set_seed,
    count_parameters,
    setup_logging,
)

logger = logging.getLogger(__name__)


@hydra.main(config_path="../config/model", config_name="small", version_base=None)
def main(cfg: DictConfig) -> None:
    setup_logging(cfg.get("log_dir"))
    set_seed(cfg.seed)

    device = get_device(cfg.device)

    # Tokenizer
    tokenizer = TokenizerWrapper(backend=cfg.data.tokenizer)

    # Model
    rcfg = cfg.model.reasoner
    reasoner_config = ReasonerConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=rcfg.d_model,
        n_heads=rcfg.n_heads,
        n_layers=rcfg.n_layers,
        d_ff=rcfg.d_ff,
        max_seq_len=rcfg.max_seq_len,
        latent_dim=rcfg.latent_dim,
        max_reasoning_steps=rcfg.max_reasoning_steps,
        dropout=rcfg.dropout,
    )
    reasoner = JEPAReasoner(reasoner_config)
    logger.info(f"Reasoner parameters: {count_parameters(reasoner):,}")

    # Dataset
    if cfg.data.dataset == "binary_tree":
        train_dataset = BinaryTreeDataset(
            num_samples=cfg.data.train_samples,
            tree_depth=cfg.data.tree_depth,
            seed=cfg.seed,
        )
        eval_dataset = BinaryTreeDataset(
            num_samples=cfg.data.eval_samples,
            tree_depth=cfg.data.tree_depth,
            seed=cfg.seed + 1,
        )
    elif cfg.data.dataset == "gsm8k":
        train_dataset = GSM8KDataset(split="train")
        eval_dataset = GSM8KDataset(split="test")
    else:
        raise ValueError(f"Unknown dataset: {cfg.data.dataset}")

    # Collator & DataLoaders
    collator = NeoReasonCollator(
        tokenizer=tokenizer,
        max_seq_len=cfg.data.max_seq_len,
        max_step_len=cfg.data.max_step_len,
        max_steps=rcfg.max_reasoning_steps,
    )

    tcfg = cfg.training.reasoner
    train_loader = DataLoader(
        train_dataset,
        batch_size=tcfg.batch_size,
        shuffle=True,
        collate_fn=collator.collate_reasoner,
        num_workers=0,
    )
    eval_loader = DataLoader(
        eval_dataset,
        batch_size=tcfg.batch_size,
        shuffle=False,
        collate_fn=collator.collate_reasoner,
        num_workers=0,
    )

    # Trainer
    trainer = ReasonerTrainer(
        reasoner=reasoner,
        train_loader=train_loader,
        eval_loader=eval_loader,
        lr=tcfg.lr,
        weight_decay=tcfg.weight_decay,
        warmup_steps=tcfg.warmup_steps,
        max_grad_norm=tcfg.max_grad_norm,
        sigreg_weight=cfg.model.sigreg.weight,
        ema_momentum_initial=cfg.model.ema.momentum_initial,
        ema_momentum_final=cfg.model.ema.momentum_final,
        epochs=tcfg.epochs,
        checkpoint_dir=cfg.checkpoint_dir,
        device=device,
        scheduler_type=tcfg.scheduler,
    )

    trainer.train()


if __name__ == "__main__":
    main()
