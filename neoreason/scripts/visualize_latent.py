"""Visualize latent reasoning trajectories using t-SNE."""

import argparse
import logging
import sys
import os

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.data.text_pairs import BinaryTreeDataset
from neoreason.eval.analysis import visualize_latent_trajectories, compute_isotropy
from neoreason.training.utils import get_device, set_seed, load_checkpoint

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize latent space")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/small",
                        help="Checkpoint directory")
    parser.add_argument("--n-samples", type=int, default=20,
                        help="Number of samples to visualize")
    parser.add_argument("--n-steps", type=int, default=8,
                        help="Number of reasoning steps")
    parser.add_argument("--output", type=str, default="latent_trajectories.png",
                        help="Output plot path")
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    set_seed(42)

    device = get_device(args.device)
    tokenizer = TokenizerWrapper(backend="tiktoken")

    # Build model
    reasoner_config = ReasonerConfig(vocab_size=tokenizer.vocab_size)
    reasoner = JEPAReasoner(reasoner_config).to(device).eval()

    reasoner_path = os.path.join(args.checkpoint, "reasoner_final.pt")
    if os.path.exists(reasoner_path):
        load_checkpoint(reasoner_path, reasoner=reasoner, device=device)
        print(f"Loaded reasoner from {reasoner_path}")
    else:
        print(f"Warning: No checkpoint at {reasoner_path}, using random weights")

    # Generate trajectories
    dataset = BinaryTreeDataset(num_samples=args.n_samples, tree_depth=3, seed=42)
    trajectories = []
    labels = []

    for i in range(min(args.n_samples, len(dataset))):
        sample = dataset[i]
        text = sample["input_text"]
        token_ids = tokenizer.encode(text)
        input_tokens = torch.tensor([token_ids], dtype=torch.long, device=device)

        with torch.no_grad():
            trajectory = reasoner.reason(input_tokens, args.n_steps)

        trajectories.append(trajectory)
        labels.append(f"Sample {i}: {sample['solution_text']}")

    # Compute isotropy
    all_latents = torch.cat(
        [z for traj in trajectories for z in traj], dim=0
    )
    isotropy = compute_isotropy(all_latents)
    print(f"\nLatent Space Isotropy:")
    for k, v in isotropy.items():
        print(f"  {k}: {v:.6f}")

    # Visualize
    visualize_latent_trajectories(trajectories, labels, save_path=args.output)
    print(f"\nVisualization saved to {args.output}")


if __name__ == "__main__":
    main()
