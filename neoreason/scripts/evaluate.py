"""Evaluate NeoReason on benchmarks."""

import logging
import sys
import os

import hydra
from omegaconf import DictConfig

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.talker import TalkerConfig, create_talker
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.data.text_pairs import BinaryTreeDataset
from neoreason.data.gsm8k import GSM8KDataset
from neoreason.inference.pipeline import NeoReasonPipeline
from neoreason.eval.benchmark import evaluate_gsm8k, evaluate_binary_tree
from neoreason.training.utils import (
    get_device,
    set_seed,
    load_checkpoint,
    setup_logging,
)

logger = logging.getLogger(__name__)


@hydra.main(config_path="../config/model", config_name="small", version_base=None)
def main(cfg: DictConfig) -> None:
    setup_logging(cfg.get("log_dir"))
    set_seed(cfg.seed)

    device = get_device(cfg.device)
    tokenizer = TokenizerWrapper(backend=cfg.data.tokenizer)

    # Build models
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
        dropout=0.0,
    )
    reasoner = JEPAReasoner(reasoner_config)

    tcfg = cfg.model.talker
    talker_config = TalkerConfig(
        type=tcfg.type,
        vocab_size=tokenizer.vocab_size,
        d_model=tcfg.d_model,
        n_heads=tcfg.n_heads,
        n_encoder_layers=tcfg.n_encoder_layers,
        n_decoder_layers=tcfg.n_decoder_layers,
        d_ff=tcfg.d_ff,
        max_seq_len=tcfg.max_seq_len,
        latent_dim=tcfg.latent_dim,
        max_reasoning_steps=tcfg.max_reasoning_steps,
        dropout=0.0,
    )
    talker = create_talker(talker_config)

    # Load checkpoints
    ckpt_dir = cfg.checkpoint_dir
    reasoner_path = os.path.join(ckpt_dir, "reasoner_final.pt")
    talker_path = os.path.join(ckpt_dir, "talker_final.pt")

    if os.path.exists(reasoner_path):
        load_checkpoint(reasoner_path, reasoner=reasoner, device=device)
    else:
        logger.warning(f"No reasoner checkpoint at {reasoner_path}")

    if os.path.exists(talker_path):
        load_checkpoint(talker_path, talker=talker, device=device)
    else:
        logger.warning(f"No talker checkpoint at {talker_path}")

    pipeline = NeoReasonPipeline(reasoner, talker, tokenizer, device)

    # Evaluate
    if cfg.data.dataset == "gsm8k":
        dataset = GSM8KDataset(split="test")
        results = evaluate_gsm8k(
            pipeline, dataset.samples,
            n_reasoning_steps=rcfg.max_reasoning_steps,
        )
    elif cfg.data.dataset == "binary_tree":
        dataset = BinaryTreeDataset(
            num_samples=cfg.data.eval_samples,
            tree_depth=cfg.data.tree_depth,
            seed=cfg.seed + 1,
        )
        results = evaluate_binary_tree(
            pipeline, dataset.samples,
            n_reasoning_steps=rcfg.max_reasoning_steps,
        )
    else:
        raise ValueError(f"Unknown dataset: {cfg.data.dataset}")

    print(f"\nResults: {results}")


if __name__ == "__main__":
    main()
