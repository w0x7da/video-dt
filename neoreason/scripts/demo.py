"""Interactive CLI demo for NeoReason."""

import argparse
import logging
import sys
import os

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.talker import TalkerConfig, create_talker
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.inference.pipeline import NeoReasonPipeline
from neoreason.training.utils import get_device, set_seed, load_checkpoint

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="NeoReason Interactive Demo")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/small",
                        help="Checkpoint directory")
    parser.add_argument("--n-steps", type=int, default=8,
                        help="Number of reasoning steps")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Sampling temperature (0 = greedy)")
    parser.add_argument("--max-tokens", type=int, default=256,
                        help="Maximum output tokens")
    parser.add_argument("--device", type=str, default="auto",
                        help="Device (auto/cuda/mps/cpu)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    set_seed(42)

    device = get_device(args.device)
    tokenizer = TokenizerWrapper(backend="tiktoken")

    # Build models with small config
    reasoner_config = ReasonerConfig(vocab_size=tokenizer.vocab_size)
    talker_config = TalkerConfig(vocab_size=tokenizer.vocab_size)

    reasoner = JEPAReasoner(reasoner_config)
    talker = create_talker(talker_config)

    # Load checkpoints if available
    reasoner_path = os.path.join(args.checkpoint, "reasoner_final.pt")
    talker_path = os.path.join(args.checkpoint, "talker_final.pt")

    if os.path.exists(reasoner_path):
        load_checkpoint(reasoner_path, reasoner=reasoner, device=device)
        print(f"Loaded reasoner from {reasoner_path}")
    else:
        print(f"Warning: No reasoner checkpoint at {reasoner_path}, using random weights")

    if os.path.exists(talker_path):
        load_checkpoint(talker_path, talker=talker, device=device)
        print(f"Loaded talker from {talker_path}")
    else:
        print(f"Warning: No talker checkpoint at {talker_path}, using random weights")

    pipeline = NeoReasonPipeline(reasoner, talker, tokenizer, device)

    print("\n" + "=" * 60)
    print("  NeoReason - JEPA-Reasoner + Talker Demo")
    print("=" * 60)
    print(f"  Device: {device}")
    print(f"  Reasoning steps: {args.n_steps}")
    print(f"  Temperature: {args.temperature}")
    print("  Type 'quit' to exit\n")

    while True:
        try:
            question = input("> Pose ta question : ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAu revoir!")
            break

        if question.lower() in ("quit", "exit", "q"):
            print("Au revoir!")
            break

        if not question:
            continue

        print(f"\nRaisonnement en cours... ({args.n_steps} steps latents)")

        result = pipeline(
            question,
            n_reasoning_steps=args.n_steps,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )

        # Show reasoning steps
        for i, z in enumerate(result.reasoning_trajectory):
            norm = torch.norm(z).item()
            print(f"  Step {i}: ||z|| = {norm:.4f} (dim={z.shape[-1]})")

        print(f"\nReponse :")
        print(f"  {result.text}")

        print(f"\nMetriques :")
        print(f"  - Temps de raisonnement : {result.reasoning_time:.3f}s")
        print(f"  - Temps de generation : {result.generation_time:.3f}s")
        print(f"  - Temps total : {result.total_time:.3f}s")
        traj_shape = f"{len(result.reasoning_trajectory)} x {result.reasoning_trajectory[0].shape[-1]}"
        print(f"  - Dimension trajectoire latente : {traj_shape}")
        print()


if __name__ == "__main__":
    main()
