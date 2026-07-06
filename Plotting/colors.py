"""
Color resolution for nodes and edges.
Uses matplotlib's color utilities, actual drawing happens in renderer.py.
"""

from typing import Dict, List, Optional, Sequence, Tuple, Union

import matplotlib as mpl
import matplotlib.colors as mcolors
from . import defaults

VALID_EDGE_COLOR_METHODS = ("Uniform", "PositiveNegative", "Node", "Nodes")

ColorInput = Union[str, Tuple[float, float, float]]
PositiveNegativeInput = Union[Dict[str, ColorInput], Tuple[ColorInput, ColorInput]]


def normalize_hex(color: Optional[ColorInput]) -> Optional[str]:
    """Validate and normalize a color to a lowercase hex string.

    Args:
        color: Any matplotlib-recognized color (hex string, named color,
            or RGB(A) tuple), or None.

    Returns:
        Lowercase hex color string (e.g. "#ff0000"), or None if `color`
        is None. None is used by savegraph's `background` to mean
        transparent.
    """
    if color is None:
        return None
    return mcolors.to_hex(color).lower()


def resolve_node_colors(
    n: int,
    secondary_labels: Optional[Dict[int, str]],
    color_palette: Optional[Dict[str, ColorInput]],
) -> List[str]:
    """Resolve a display color for every node.

    Nodes are colored based on these conditions (ordered):
    color_palette[<secondary label>]: Each secondary label has an explicitly assigned color
    secondary_labels: Each secondary label is colored by a default palette
    node index: If there is no predefined color palette and no secondary label for the data - color is per index.

    Parameters:
        n: Number of nodes.
        secondary_labels: Mapping of node index to secondary label, or
            None/empty if there are no secondary labels.
        color_palette: Mapping of secondary label to color (e.g.
            {"VisionLeft": "#ffffff", "VisionRight": "#000000"}), or
            None/empty.

    Returns:
        List of n lowercase hex color strings, indexed by node position.
    """
    color_palette = color_palette or {}
    fallback_cmap = mpl.colormaps[
        defaults.SEC_LABEL_FALLBACK_COLORMAP if secondary_labels else defaults.NODE_FALLBACK_COLORMAP]

    default_label_colors: Dict[str, str] = {}
    if secondary_labels:
        unique_labels = sorted(set(secondary_labels.values()))

        default_label_colors = {
            label: mcolors.to_hex(fallback_cmap(idx / len(unique_labels)))
            for idx, label in enumerate(unique_labels)
        }

    colors: List[str] = []
    for i in range(n):
        label = secondary_labels.get(i) if secondary_labels else None
        color: Optional[ColorInput] = None
        if label is not None:
            color = color_palette.get(label) or default_label_colors.get(label)
        if color is None:
            t = i / max(n - 1, 1)
            color = mcolors.to_hex(fallback_cmap(t))
        colors.append(normalize_hex(color))
    return colors


def _unpack_positive_negative(
    edge_color: PositiveNegativeInput,
    default_positive: ColorInput,
    default_negative: ColorInput,
) -> Tuple[ColorInput, ColorInput]:
    """Extract (positive, negative) colors from a PositiveNegative input.

    Parameters:
        edge_color: Either a dict with "positive"/"negative" keys, or a 2-tuple/list of (positive, negative).
        default_positive: Fallback used when edge_color is a dict missing the "positive" key.
        default_negative: Fallback used when edge_color is a dict missing the "negative" key.

    Returns:
        (positive, negative) color tuple.

    Raises:
        ValueError: If edge_color is neither a dict nor a 2-tuple/list.
    """
    if isinstance(edge_color, dict):
        return (
            edge_color.get("positive", default_positive),
            edge_color.get("negative", default_negative),
        )
    if isinstance(edge_color, (tuple, list)) and len(edge_color) == 2:
        return edge_color[0], edge_color[1]
    raise ValueError(
        "edge_color for edge_color_method='PositiveNegative' must be a "
        "dict {'positive': ..., 'negative': ...} or a 2-tuple "
        "(positive, negative)"
    )


def resolve_edge_color_pair(
    method: str,
    edge_color: Optional[Union[ColorInput, PositiveNegativeInput]],
    node_colors: Sequence[str],
    i: int,
    j: int,
    weight: float,
) -> Tuple[str, str]:
    """Resolve the two endpoint colors to draw an edge between.

    For solid-colored methods ("Uniform", "Node") color_a == color_b. For
    gradient methods ("PositiveNegative" picks by sign, "Nodes" uses each
    endpoint's node color) color_a and color_b may differ, and the caller
    is expected to render a gradient between them.

    Parameters:
        method: One of "Uniform", "PositiveNegative", "Node", "Nodes".
        edge_color: Override color(s) for "Uniform" (single color) or
            "PositiveNegative" (dict/2-tuple of positive, negative).
            Ignored for "Node"/"Nodes". None uses the defaults.py
            EDGE_COLOR_* constants.
        node_colors: Per-node colors, as returned by resolve_node_colors.
        i: Index of the edge's first endpoint node.
        j: Index of the edge's second endpoint node.
        weight: Edge weight; only its sign matters, for
            "PositiveNegative".

    Returns:
        (color_a, color_b) hex color tuple.

    Raises:
        ValueError: If `method` is not a recognized edge_color_method.
    """
    if method not in VALID_EDGE_COLOR_METHODS:
        raise ValueError(
            f"Unknown edge_color_method: {method!r}, expected one of "
            f"{VALID_EDGE_COLOR_METHODS}"
        )

    if method == "Uniform":
        color = edge_color if edge_color else defaults.EDGE_COLOR_UNIFORM
        color = normalize_hex(color)
        return color, color

    if method == "PositiveNegative":
        default_positive = defaults.EDGE_COLOR_POSITIVE
        default_negative = defaults.EDGE_COLOR_NEGATIVE
        if edge_color:
            positive, negative = _unpack_positive_negative(
                edge_color, default_positive, default_negative
            )
        else:
            positive, negative = default_positive, default_negative
        color = normalize_hex(positive if weight >= 0 else negative)
        return color, color

    if method == "Node":
        color = node_colors[i]
        return color, color

    # method == "Nodes"
    return node_colors[i], node_colors[j]


def interpolate_color(
    color_a: ColorInput, color_b: ColorInput, t: float
) -> Tuple[float, float, float]:
    """Linearly interpolate between two colors in RGB space.

    Parameters:
        color_a: Color at t=0.
        color_b: Color at t=1.
        t: Interpolation factor in [0, 1].

    Returns:
        (r, g, b) tuple with components in [0, 1].
    """
    rgb_a = mcolors.to_rgb(color_a)
    rgb_b = mcolors.to_rgb(color_b)
    return tuple(a + (b - a) * t for a, b in zip(rgb_a, rgb_b))
