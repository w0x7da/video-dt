"""Latent space analysis and visualization."""

import logging

import torch
import numpy as np
from torch import Tensor

logger = logging.getLogger(__name__)


def compute_isotropy(embeddings: Tensor) -> dict[str, float]:
    """Compute isotropy metrics for a set of embeddings.

    Args:
        embeddings: Tensor of shape (n_samples, latent_dim).

    Returns:
        Dict with eigenvalue statistics measuring how isotropic the space is.
    """
    z = embeddings.detach().cpu().float()
    z_centered = z - z.mean(dim=0, keepdim=True)
    cov = (z_centered.T @ z_centered) / (z.shape[0] - 1)
    eigenvals = torch.linalg.eigvalsh(cov)
    eigenvals = eigenvals.clamp(min=1e-8)

    return {
        "eigenvalue_mean": eigenvals.mean().item(),
        "eigenvalue_std": eigenvals.std().item(),
        "eigenvalue_min": eigenvals.min().item(),
        "eigenvalue_max": eigenvals.max().item(),
        "isotropy_ratio": (eigenvals.min() / eigenvals.max()).item(),
        "effective_rank": (eigenvals.sum() / eigenvals.max()).item(),
    }


def visualize_latent_trajectories(
    trajectories: list[list[Tensor]],
    labels: list[str] | None = None,
    save_path: str | None = None,
) -> None:
    """Visualize latent trajectories using t-SNE.

    Args:
        trajectories: List of trajectories, each a list of (1, latent_dim) tensors.
        labels: Optional labels for each trajectory.
        save_path: If provided, save the plot to this path.
    """
    try:
        import matplotlib.pyplot as plt
        from sklearn.manifold import TSNE
    except ImportError:
        logger.warning("matplotlib and/or scikit-learn not available for visualization")
        return

    # Flatten all latent vectors
    all_vectors = []
    trajectory_ids = []
    step_ids = []

    for traj_idx, trajectory in enumerate(trajectories):
        for step_idx, z in enumerate(trajectory):
            vec = z.detach().cpu().numpy()
            if vec.ndim > 1:
                vec = vec[0]  # Take first in batch
            all_vectors.append(vec)
            trajectory_ids.append(traj_idx)
            step_ids.append(step_idx)

    all_vectors_np = np.array(all_vectors)

    # t-SNE
    perplexity = min(30, len(all_vectors_np) - 1)
    if perplexity < 2:
        logger.warning("Too few samples for t-SNE visualization")
        return

    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
    embedded = tsne.fit_transform(all_vectors_np)

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    n_trajs = len(trajectories)
    colors = plt.cm.tab10(np.linspace(0, 1, max(n_trajs, 1)))

    for traj_idx in range(n_trajs):
        mask = [i for i, t in enumerate(trajectory_ids) if t == traj_idx]
        points = embedded[mask]

        label = labels[traj_idx] if labels else f"Trajectory {traj_idx}"
        ax.plot(points[:, 0], points[:, 1], "o-", color=colors[traj_idx],
                label=label, markersize=6, alpha=0.7)

        # Mark start and end
        ax.plot(points[0, 0], points[0, 1], "s", color=colors[traj_idx],
                markersize=12, markeredgecolor="black")
        ax.plot(points[-1, 0], points[-1, 1], "*", color=colors[traj_idx],
                markersize=15, markeredgecolor="black")

    ax.set_title("Latent Reasoning Trajectories (t-SNE)")
    ax.set_xlabel("t-SNE dim 1")
    ax.set_ylabel("t-SNE dim 2")
    if n_trajs <= 10:
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Trajectory visualization saved to {save_path}")
    else:
        plt.show()

    plt.close(fig)
