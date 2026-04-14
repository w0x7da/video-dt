# NeoReason: JEPA-Reasoner + Talker

A PyTorch implementation of latent-space reasoning based on the JEPA-Reasoner architecture.
The Reasoner thinks in continuous latent space (no tokens), and the Talker translates
reasoning trajectories into human-readable text.

```
┌─────────────────────────────────────────────────────┐
│                    NeoReason                        │
│                                                     │
│  ┌─────────────┐    latent     ┌─────────────────┐  │
│  │  REASONER   │──trajectory──>│     TALKER      │  │
│  │  (JEPA)     │    [z0->zn]   │  (Transformer)  │  │
│  └──────┬──────┘               └───────┬─────────┘  │
│         │                              │            │
│    Reasons in                 Generates text        │
│    continuous latent          from latents          │
│    space (no tokens)          (no reasoning)        │
└─────────────────────────────────────────────────────┘
```

## Papers

- **JEPA-Reasoner** (arXiv:2512.19171) — Decouples latent reasoning from token generation
- **LLM-JEPA** (arXiv:2509.14252) — Augments LLMs with JEPA objectives
- **LeWorldModel** (arXiv:2603.19312) — Stable JEPA with SIGReg regularization

## Installation

```bash
cd neoreason
pip install -e .
```

## Quick Start

### Train the Reasoner (Phase 1)
```bash
python scripts/train_reasoner.py --config-name=small data.dataset=binary_tree
```

### Train the Talker (Phase 2)
```bash
python scripts/train_talker.py --config-name=small
```

### Evaluate
```bash
python scripts/evaluate.py --config-name=small
```

### Interactive Demo
```bash
python scripts/demo.py --checkpoint checkpoints/small/
```

### Visualize Latent Space
```bash
python scripts/visualize_latent.py --checkpoint checkpoints/small/
```

## Model Configurations

| Config | Reasoner | Talker | Target Hardware |
|--------|----------|--------|-----------------|
| small  | 12M      | 8M     | Mac Mini M4 16GB |
| medium | 85M      | 42M    | Single A100     |
| large  | 340M     | 120M   | Multi-GPU       |

## Architecture

**Reasoner**: Token Embedding → Mean Pooling → HybridNorm → Predictor (Transformer with QK-Norm) → HybridNorm → next latent vector. Autoregressive loop in latent space produces trajectory [z0, z1, ..., zn] on the unit hypersphere.

**Talker (Dual)**: Encoder processes latent trajectory with self-attention. Decoder generates tokens with cross-attention to encoded latents.

**Training**: Phase 1 trains the Reasoner with cosine prediction loss + SIGReg anti-collapse regularizer. Phase 2 trains the Talker with cross-entropy loss while the Reasoner is frozen.

## Tests

```bash
cd neoreason
python -m pytest tests/ -v
```
