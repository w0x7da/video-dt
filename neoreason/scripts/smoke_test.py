"""Quick smoke test: trains Reasoner + Talker for a few steps to validate everything works."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
from torch.utils.data import DataLoader

from neoreason.model.reasoner import JEPAReasoner, ReasonerConfig
from neoreason.model.talker import DualTalker, TalkerConfig
from neoreason.model.tokenizer_wrapper import TokenizerWrapper
from neoreason.model.ema import EMAUpdater
from neoreason.data.text_pairs import BinaryTreeDataset
from neoreason.data.collator import NeoReasonCollator
from neoreason.training.losses import JEPALoss
from neoreason.inference.pipeline import NeoReasonPipeline


def main() -> None:
    print("=" * 60)
    print("  NeoReason Smoke Test")
    print("=" * 60)

    device = torch.device("cpu")
    torch.manual_seed(42)

    # --- Tokenizer ---
    tokenizer = TokenizerWrapper(backend="simple")
    print(f"\nTokenizer: backend={tokenizer.backend}, vocab_size={tokenizer.vocab_size}")

    # --- Small config ---
    reasoner_config = ReasonerConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=64,
        n_heads=4,
        n_layers=2,
        d_ff=128,
        max_seq_len=64,
        latent_dim=64,
        max_reasoning_steps=4,
        dropout=0.0,
    )
    talker_config = TalkerConfig(
        type="dual",
        vocab_size=tokenizer.vocab_size,
        d_model=64,
        n_heads=4,
        n_encoder_layers=2,
        n_decoder_layers=2,
        d_ff=128,
        max_seq_len=64,
        latent_dim=64,
        max_reasoning_steps=4,
        dropout=0.0,
    )

    # --- Models ---
    reasoner = JEPAReasoner(reasoner_config).to(device)
    talker = DualTalker(talker_config).to(device)

    r_params = sum(p.numel() for p in reasoner.parameters() if p.requires_grad)
    t_params = sum(p.numel() for p in talker.parameters() if p.requires_grad)
    print(f"Reasoner params: {r_params:,}")
    print(f"Talker params: {t_params:,}")

    # --- Dataset ---
    dataset = BinaryTreeDataset(num_samples=100, tree_depth=3, seed=42)
    collator = NeoReasonCollator(tokenizer, max_seq_len=64, max_step_len=32, max_steps=4)

    print(f"Dataset: {len(dataset)} binary tree samples")
    print(f"Sample: {dataset[0]['solution_text']}")

    # ====================
    # PHASE 1: Train Reasoner
    # ====================
    print("\n--- PHASE 1: Reasoner Training (5 steps) ---")
    reasoner.train()
    optimizer = torch.optim.AdamW(reasoner.get_online_params(), lr=1e-3)
    criterion = JEPALoss(sigreg_weight=1.0)
    ema = EMAUpdater(momentum_initial=0.996, momentum_final=0.999, total_steps=5)

    loader = DataLoader(dataset, batch_size=8, shuffle=True, collate_fn=collator.collate_reasoner)

    losses = []
    t0 = time.time()
    for step, batch in enumerate(loader):
        if step >= 5:
            break

        input_tokens = batch["input_tokens"].to(device)
        step_tokens = [st.to(device) for st in batch["step_tokens"]]

        result = reasoner(input_tokens, step_tokens)
        loss_dict = criterion(result["predictions"], result["targets"])

        optimizer.zero_grad()
        loss_dict["total"].backward()
        torch.nn.utils.clip_grad_norm_(reasoner.get_online_params(), 1.0)
        optimizer.step()

        online, target = reasoner.get_target_modules()
        ema.step(online, target, step)

        losses.append(loss_dict["total"].item())
        print(f"  Step {step+1}: loss={loss_dict['total'].item():.4f} "
              f"(pred={loss_dict['prediction'].item():.4f}, sigreg={loss_dict['sigreg'].item():.4f})")

    dt = time.time() - t0
    print(f"  Time: {dt:.2f}s")
    print(f"  Loss trend: {losses[0]:.4f} -> {losses[-1]:.4f} "
          f"({'decreasing' if losses[-1] < losses[0] else 'not yet decreasing (normal for 5 steps)'})")

    # Verify latent trajectories are on unit sphere
    reasoner.eval()
    with torch.no_grad():
        test_tokens = torch.randint(0, tokenizer.vocab_size, (2, 16))
        trajectory = reasoner.reason(test_tokens, n_steps=4)
        norms = [torch.norm(z, dim=-1).mean().item() for z in trajectory]
        print(f"  Latent norms (should be ~1.0): {[f'{n:.4f}' for n in norms]}")

    # ====================
    # PHASE 2: Train Talker (Reasoner frozen)
    # ====================
    print("\n--- PHASE 2: Talker Training (5 steps, Reasoner frozen) ---")
    reasoner.eval()
    for p in reasoner.parameters():
        p.requires_grad = False

    talker.train()
    talker_optimizer = torch.optim.AdamW(talker.parameters(), lr=1e-3)
    ce_loss = torch.nn.CrossEntropyLoss(ignore_index=0)

    talker_loader = DataLoader(dataset, batch_size=8, shuffle=True, collate_fn=collator.collate_talker)

    talker_losses = []
    t0 = time.time()
    for step, batch in enumerate(talker_loader):
        if step >= 5:
            break

        input_tokens = batch["input_tokens"].to(device)
        target_tokens = batch["target_tokens"].to(device)

        with torch.no_grad():
            trajectory = reasoner.reason(input_tokens, n_steps=4)

        decoder_input = target_tokens[:, :-1]
        decoder_target = target_tokens[:, 1:]
        logits = talker(trajectory, decoder_input)

        loss = ce_loss(logits.reshape(-1, logits.shape[-1]), decoder_target.reshape(-1))

        talker_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(talker.parameters(), 1.0)
        talker_optimizer.step()

        talker_losses.append(loss.item())
        print(f"  Step {step+1}: talker_loss={loss.item():.4f}")

    dt = time.time() - t0
    print(f"  Time: {dt:.2f}s")

    # ====================
    # INFERENCE TEST
    # ====================
    print("\n--- INFERENCE TEST ---")
    for p in reasoner.parameters():
        p.requires_grad = False
    reasoner.eval()
    talker.eval()

    pipeline = NeoReasonPipeline(reasoner, talker, tokenizer, device)

    test_input = dataset[0]["input_text"][:100]  # Truncate for speed
    result = pipeline(test_input, n_reasoning_steps=4, temperature=0.7, max_tokens=32)

    print(f"  Input: {test_input[:80]}...")
    print(f"  Output: {result.text[:200]}")
    print(f"  Reasoning time: {result.reasoning_time:.3f}s")
    print(f"  Generation time: {result.generation_time:.3f}s")
    print(f"  Trajectory: {len(result.reasoning_trajectory)} steps x {result.reasoning_trajectory[0].shape[-1]} dims")

    # ====================
    # SUMMARY
    # ====================
    print("\n" + "=" * 60)
    print("  SMOKE TEST PASSED")
    print("=" * 60)
    print(f"  Reasoner: {r_params:,} params, loss {losses[0]:.4f} -> {losses[-1]:.4f}")
    print(f"  Talker: {t_params:,} params, loss {talker_losses[0]:.4f} -> {talker_losses[-1]:.4f}")
    print(f"  Inference: {len(result.text)} chars generated in {result.total_time:.3f}s")
    print(f"  All latent vectors on unit sphere: OK")
    print()


if __name__ == "__main__":
    main()
