"""Binary Tree Search dataset for PoC validation.

Generates synthetic binary trees with a target leaf. The model must find
the path from root to target leaf. This is the same task used in the
JEPA-Reasoner paper (99.87% accuracy with 42M params).
"""

import logging
import random
import string
from dataclasses import dataclass

from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


@dataclass
class TreeNode:
    label: str
    left: "TreeNode | None" = None
    right: "TreeNode | None" = None


def _generate_tree(depth: int, rng: random.Random) -> TreeNode:
    """Generate a complete binary tree with unique labels."""
    labels = list(string.ascii_uppercase + string.digits)
    rng.shuffle(labels)
    label_iter = iter(labels)

    def _build(d: int) -> TreeNode:
        node = TreeNode(label=next(label_iter))
        if d > 0:
            node.left = _build(d - 1)
            node.right = _build(d - 1)
        return node

    return _build(depth)


def _get_all_leaves(node: TreeNode) -> list[TreeNode]:
    """Collect all leaf nodes."""
    if node.left is None and node.right is None:
        return [node]
    leaves = []
    if node.left:
        leaves.extend(_get_all_leaves(node.left))
    if node.right:
        leaves.extend(_get_all_leaves(node.right))
    return leaves


def _find_path(root: TreeNode, target_label: str) -> list[str] | None:
    """Find the path from root to the node with target_label."""
    if root.label == target_label:
        return [root.label]
    for child in [root.left, root.right]:
        if child is not None:
            path = _find_path(child, target_label)
            if path is not None:
                return [root.label] + path
    return None


def _tree_to_text(node: TreeNode) -> str:
    """Convert a tree to a textual description."""
    lines = []

    def _describe(n: TreeNode) -> None:
        if n.left is not None and n.right is not None:
            lines.append(f"Node {n.label} has children {n.left.label} and {n.right.label}.")
            _describe(n.left)
            _describe(n.right)
        else:
            lines.append(f"Node {n.label} is a leaf.")

    _describe(node)
    return " ".join(lines)


class BinaryTreeDataset(Dataset):
    """Synthetic binary tree search dataset.

    Each sample contains:
        - input_text: textual description of the tree + target leaf
        - steps_text: list of step descriptions (one per node in the path)
        - solution_text: full path as "A -> B -> D"
    """

    def __init__(
        self,
        num_samples: int = 10000,
        tree_depth: int = 4,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.num_samples = num_samples
        self.tree_depth = tree_depth
        self.samples: list[dict[str, str | list[str]]] = []

        rng = random.Random(seed)
        for _ in range(num_samples):
            tree = _generate_tree(tree_depth, rng)
            leaves = _get_all_leaves(tree)
            target = rng.choice(leaves)

            tree_desc = _tree_to_text(tree)
            input_text = f"{tree_desc} Find the path to leaf {target.label}."

            path = _find_path(tree, target.label)
            assert path is not None

            # Steps: one per node traversed
            steps_text = []
            for i, label in enumerate(path):
                if i == 0:
                    steps_text.append(f"Start at root {label}.")
                elif i == len(path) - 1:
                    steps_text.append(f"Arrive at target leaf {label}.")
                else:
                    steps_text.append(f"Move to node {label}.")

            solution_text = " -> ".join(path)

            self.samples.append({
                "input_text": input_text,
                "steps_text": steps_text,
                "solution_text": solution_text,
            })

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> dict[str, str | list[str]]:
        return self.samples[idx]
