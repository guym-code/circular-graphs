"""Manual verification / usage demo for the plotting module.

Not part of the shipped API -- builds a stand-in for the (not yet
existing) CircularGraph object using the repo's real atlas labels and a
synthetic connectivity matrix, then exercises plot()/show()/savegraph()
across the documented parameter combinations.

Usage:
    python plotting/example.py [output_dir]
"""

import csv
import os
import sys
import tempfile
import warnings
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

import matplotlib as mpl
import numpy as np
import numpy.typing as npt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plotting import graph_plot  # noqa: E402  (path setup must run first)

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS_LABELS_CSV = os.path.join(_REPO_ROOT, "Atlases", "labels_scf_100.csv")


def load_atlas_labels(path: str) -> List[str]:
    """Read one atlas ROI label per line from a single-column CSV.

    Args:
        path: Path to the labels CSV (no header row).

    Returns:
        List of label strings, in file order.
    """
    with open(path, encoding="utf-8-sig") as f:
        return [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]


def build_labels(
    full_labels: List[str],
) -> Tuple[Dict[int, str], Dict[int, str]]:
    """Build labels_dict/secondary_labels from full atlas label strings.

    The secondary label is the full label with its trailing region
    number stripped, e.g. "Left Visual 1" -> "Left Visual".

    Args:
        full_labels: Full ROI label per node, in node-index order.

    Returns:
        (labels_dict, secondary_labels), each mapping node index to a
        string.
    """
    labels_dict = dict(enumerate(full_labels))
    secondary_labels = {
        i: label.rsplit(" ", 1)[0] for i, label in enumerate(full_labels)
    }
    return labels_dict, secondary_labels


def build_color_scheme(secondary_labels: Dict[int, str]) -> Dict[str, Any]:
    """Assign each unique secondary label a distinct color.

    Args:
        secondary_labels: Mapping of node index to secondary label.

    Returns:
        A color_scheme dict with a "networks" mapping of
        {secondary label: hex color}.
    """
    unique = list(dict.fromkeys(secondary_labels.values()))
    cmap = mpl.colormaps["tab20"]
    networks = {
        label: mpl.colors.to_hex(cmap(i / max(len(unique) - 1, 1)))
        for i, label in enumerate(unique)
    }
    return {"networks": networks}


def make_synthetic_matrix(n: int, seed: int = 0) -> npt.NDArray[np.float64]:
    """Generate a synthetic symmetric connectivity matrix in [-1, 1].

    Args:
        n: Number of nodes (matrix is n x n).
        seed: Random seed, for reproducible demo output.

    Returns:
        n x n symmetric float array with a zero diagonal.
    """
    rng = np.random.default_rng(seed)
    m = rng.uniform(-1, 1, size=(n, n))
    m = (m + m.T) / 2
    np.fill_diagonal(m, 0.0)
    return m


def make_stub_graph(n: int, seed: int = 0) -> SimpleNamespace:
    """Build a minimal CircularGraph-like stub for demo purposes.

    Args:
        n: Number of nodes to include (first n rows of the atlas
            labels).
        seed: Random seed for the synthetic connectivity matrix.

    Returns:
        SimpleNamespace with edges_mat, labels_dict, secondary_labels,
        and color_scheme attributes.
    """
    full_labels = load_atlas_labels(ATLAS_LABELS_CSV)[:n]
    labels_dict, secondary_labels = build_labels(full_labels)
    color_scheme = build_color_scheme(secondary_labels)
    edges_mat = make_synthetic_matrix(n, seed=seed)
    return SimpleNamespace(
        edges_mat=edges_mat,
        labels_dict=labels_dict,
        secondary_labels=secondary_labels,
        color_scheme=color_scheme,
    )


def run(output_dir: str) -> None:
    """Render and save a set of demo figures covering the plot() spec.

    Args:
        output_dir: Directory to write demo PNGs into (created if
            missing).
    """
    os.makedirs(output_dir, exist_ok=True)

    demos = [
        dict(
            name="full_no_labels",
            n=100,
            plot_kwargs=dict(
                label=False, sec_label="Color", edge_color_method="PositiveNegative"
            ),
        ),
        dict(
            name="subset_bracket",
            n=21,
            plot_kwargs=dict(
                label=True, sec_label="Bracket", edge_color_method="Uniform"
            ),
        ),
        dict(
            name="subset_colorbracket",
            n=21,
            plot_kwargs=dict(
                label=True, sec_label="ColorBracket", edge_color_method="Node"
            ),
        ),
        dict(
            name="subset_gradient_nodes",
            n=21,
            plot_kwargs=dict(
                label=True, sec_label="Color", edge_color_method="Nodes"
            ),
        ),
        dict(
            name="subset_no_seclabel",
            n=21,
            plot_kwargs=dict(
                label=True, sec_label="False", edge_color_method="Uniform"
            ),
        ),
    ]

    for demo in demos:
        graph = make_stub_graph(demo["n"])
        graph_plot.plot(graph, **demo["plot_kwargs"])
        fname = os.path.join(output_dir, f"{demo['name']}.png")
        graph_plot.savegraph(graph, fname)
        print(f"saved {fname}")

    # background / transparency checks
    graph = make_stub_graph(21)
    graph_plot.plot(
        graph,
        label=True,
        sec_label="ColorBracket",
        edge_color_method="PositiveNegative",
    )
    custom_bg_fname = os.path.join(output_dir, "background_custom.png")
    graph_plot.savegraph(graph, custom_bg_fname, background="#f0f0f0")
    print(f"saved {custom_bg_fname}")

    transparent_fname = os.path.join(output_dir, "background_transparent.png")
    graph_plot.savegraph(graph, transparent_fname, background=None)
    print(f"saved {transparent_fname}")

    # show() smoke test (headless backends will warn, not crash)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        graph_plot.show(graph)
    print("show() did not raise")


if __name__ == "__main__":
    out_dir = (
        sys.argv[1]
        if len(sys.argv) > 1
        else tempfile.mkdtemp(prefix="circular_graph_demo_")
    )
    run(out_dir)
    print(f"\nAll demo figures written to: {out_dir}")
