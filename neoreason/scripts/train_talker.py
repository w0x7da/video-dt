"""Phase 2: Train the Talker with the Reasoner frozen."""

import logging
import sys
import os

import hydra
from omegaconf import DictConfig
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.talker import TalkerConfig, create_talker
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.data.text_pairs import BinaryTreeDataset
from neoreason.data.gsm8k import GSM8KDataset
from neoreason.data.collator import NeoReasonCollator
from neoreason.training.trainer import TalkerTrainer
from neoreason.training.utils import (
    get_device,
    set_seed,
    count_parameters,
    load_checkpoint,
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

    # Build Reasoner and load pretrained weights
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

    # Load pretrained reasoner checkpoint
    reasoner_ckpt = os.path.join(cfg.checkpoint_dir, "reasoner_final.pt")
    if os.path.exists(reasoner_ckpt):
        load_checkpoint(reasoner_ckpt, reasoner=reasoner, device=device)
        logger.info(f"Loaded pretrained reasoner from {reasoner_ckpt}")
    else:
        logger.warning(f"No pretrained reasoner at {reasoner_ckpt}, using random init")

    # Build Talker
    tcfg_model = cfg.model.talker
    talker_config = TalkerConfig(
        type=tcfg_model.type,
        vocab_size=tokenizer.vocab_size,
        d_model=tcfg_model.d_model,
        n_heads=tcfg_model.n_heads,
        n_encoder_layers=tcfg_model.n_encoder_layers,
        n_decoder_layers=tcfg_model.n_decoder_layers,
        d_ff=tcfg_model.d_ff,
        max_seq_len=tcfg_model.max_seq_len,
        latent_dim=tcfg_model.latent_dim,
        max_reasoning_steps=tcfg_model.max_reasoning_steps,
        dropout=tcfg_model.dropout,
    )
    talker = create_talker(talker_config)
    logger.info(f"Talker parameters: {count_parameters(talker):,}")

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

    tcfg = cfg.training.talker
    train_loader = DataLoader(
        train_dataset,
        batch_size=tcfg.batch_size,
        shuffle=True,
        collate_fn=collator.collate_talker,
        num_workers=0,
    )
    eval_loader = DataLoader(
        eval_dataset,
        batch_size=tcfg.batch_size,
        shuffle=False,
        collate_fn=collator.collate_talker,
        num_workers=0,
    )

    # Trainer
    trainer = TalkerTrainer(
        reasoner=reasoner,
        talker=talker,
        train_loader=train_loader,
        eval_loader=eval_loader,
        lr=tcfg.lr,
        weight_decay=tcfg.weight_decay,
        warmup_steps=tcfg.warmup_steps,
        max_grad_norm=tcfg.max_grad_norm,
        n_reasoning_steps=rcfg.max_reasoning_steps,
        epochs=tcfg.epochs,
        checkpoint_dir=cfg.checkpoint_dir,
        device=device,
        scheduler_type=tcfg.scheduler,
    )

    trainer.train()


if __name__ == "__main__":
    main()
