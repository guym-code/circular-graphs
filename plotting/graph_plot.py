"""Public plotting functions: plot, show, savegraph.

These are plain functions (not a mixin class) that operate on any object
exposing edges_mat, labels_dict, secondary_labels, and color_scheme --
the attributes the eventual CircularGraph class will provide. The class
can attach these directly (e.g. CircularGraph.plot = graph_plot.plot) or
wrap them in thin methods, whichever its author prefers.
"""

import os
from typing import Any, Dict, Optional, Protocol, Sequence, Union

from matplotlib.figure import Figure

from . import colors, defaults, layout, renderer
from .colors import ColorInput, PositiveNegativeInput

VALID_SEC_LABEL_MODES = ("Color", "Bracket", "ColorBracket", "False")


class CircularGraphLike(Protocol):
    """Structural type for the attributes graph_plot functions rely on.

    Matches the (not yet implemented) CircularGraph class: any object
    with these four attributes can be passed to plot/show/savegraph.
    """

    edges_mat: Sequence[Sequence[float]]
    labels_dict: Dict[int, str]
    secondary_labels: Optional[Dict[int, str]]
    color_scheme: Optional[Dict[str, Any]]


def plot(
    graph: CircularGraphLike,
    label: bool = defaults.LABEL,
    label_font: Optional[str] = defaults.LABEL_FONT,
    label_size: float = defaults.LABEL_SIZE,
    sec_label: Union[str, bool] = defaults.SEC_LABEL,
    sec_label_font: Optional[str] = defaults.SEC_LABEL_FONT,
    sec_label_size: float = defaults.SEC_LABEL_SIZE,
    edge_color_method: str = defaults.EDGE_COLOR_METHOD,
    edge_color: Optional[Union[ColorInput, PositiveNegativeInput]] = None,
) -> Figure:
    """Design and create the circular graph figure for `graph`.

    Builds node layout and colors, draws nodes/edges/labels/group
    annotations, and stores the result on `graph` (as `_fig`/`_ax`) so
    that show()/savegraph() can later be called on the same graph.

    Args:
        graph: Object exposing edges_mat, labels_dict, secondary_labels,
            color_scheme (see CircularGraphLike).
        label: If True, draw each node's label from graph.labels_dict
            next to it.
        label_font: Font family for node labels, or None for default.
        label_size: Font size (points) for node labels.
        sec_label: One of "Color", "Bracket", "ColorBracket", "False"
            (or the boolean False, treated as "False"). "Color" colors
            nodes by secondary label and shows a legend; "Bracket" draws
            a bracket + curved label over each group; "ColorBracket"
            does both (no legend needed).
        sec_label_font: Font family for group labels/legend, or None for
            default.
        sec_label_size: Font size (points) for group labels/legend.
        edge_color_method: One of "Uniform", "PositiveNegative", "Node",
            "Nodes" (see colors.resolve_edge_color_pair).
        edge_color: Optional override color(s) for "Uniform" (a single
            color) or "PositiveNegative" (a dict/2-tuple of positive,
            negative). Ignored for "Node"/"Nodes".

    Returns:
        The created matplotlib Figure (also stored as graph._fig).

    Raises:
        ValueError: If `sec_label` is not a recognized mode.
    """
    if sec_label is False:
        sec_label = "False"
    if sec_label not in VALID_SEC_LABEL_MODES:
        raise ValueError(
            f"sec_label must be one of {VALID_SEC_LABEL_MODES}, got {sec_label!r}"
        )

    edges_mat = graph.edges_mat
    n = len(edges_mat)
    labels_dict = graph.labels_dict or {}
    secondary_labels = getattr(graph, "secondary_labels", None) or {}
    color_scheme = getattr(graph, "color_scheme", None) or {}

    positions = layout.compute_node_positions(n, radius=defaults.NODE_RADIUS)
    angles = layout.compute_node_angles(n)
    groups = (
        layout.detect_groups(list(range(n)), secondary_labels)
        if secondary_labels
        else []
    )

    node_colors = colors.resolve_node_colors(n, secondary_labels, color_scheme)

    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            weight = edges_mat[i][j]
            if not weight:
                continue
            color_a, color_b = colors.resolve_edge_color_pair(
                edge_color_method, edge_color, node_colors, color_scheme, i, j, weight
            )
            edges.append((i, j, weight, color_a, color_b))

    fig, ax = renderer.create_figure()
    renderer.draw_edges(ax, positions, edges)
    renderer.draw_nodes(ax, positions, node_colors)

    if label:
        node_labels = [labels_dict.get(i) for i in range(n)]
        renderer.draw_labels(ax, angles, node_labels, font=label_font, size=label_size)

    if sec_label in ("Bracket", "ColorBracket") and groups:
        renderer.draw_group_brackets(
            ax, fig, n, groups, font=sec_label_font, size=sec_label_size
        )
    if sec_label == "Color" and groups:
        renderer.draw_group_legend(
            ax, node_colors, groups, font=sec_label_font, size=sec_label_size
        )

    renderer.finalize_axes(ax)

    graph._fig = fig
    graph._ax = ax
    return fig


def show(graph: CircularGraphLike) -> None:
    """Show the figure created by a prior call to plot(graph, ...).

    Args:
        graph: Graph previously passed to plot().

    Raises:
        RuntimeError: If plot(graph, ...) has not been called yet.
    """
    fig = getattr(graph, "_fig", None)
    if fig is None:
        raise RuntimeError("show() requires plot(graph, ...) to be called first")
    fig.show()


def savegraph(
    graph: CircularGraphLike,
    fname: Union[str, "os.PathLike[str]"],
    format: str = defaults.SAVE_FORMAT,
    dpi: int = defaults.SAVE_DPI,
    background: Optional[str] = defaults.SAVE_BACKGROUND,
) -> None:
    """Save the figure created by a prior call to plot(graph, ...).

    Args:
        graph: Graph previously passed to plot().
        fname: Output path, as a string or path-like object, including
            the filename.
        format: Image format (e.g. "png", "svg", "pdf").
        dpi: Resolution in dots per inch.
        background: Hex color for the saved image's background, or None
            for a transparent background.

    Raises:
        RuntimeError: If plot(graph, ...) has not been called yet.
    """
    fig = getattr(graph, "_fig", None)
    if fig is None:
        raise RuntimeError("savegraph() requires plot(graph, ...) to be called first")
    facecolor = colors.normalize_hex(background) if background else "none"
    fig.savefig(
        fname,
        format=format,
        dpi=dpi,
        facecolor=facecolor,
        transparent=(background is None),
        bbox_inches="tight",
    )
