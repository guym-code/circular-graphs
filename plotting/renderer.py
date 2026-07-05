"""Low-level matplotlib drawing primitives for circular graphs.

This is the only module that touches matplotlib drawing calls directly.
Callers (graph_plot.py) are responsible for computing geometry
(layout.py) and colors (colors.py) beforehand.
"""

import math
from typing import List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.ft2font import FT2Font
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path

from . import colors as color_utils
from . import defaults, layout

Point = Tuple[float, float]
Edge = Tuple[int, int, float, str, str]
Group = Tuple[str, int, int]


def create_figure(figsize: Tuple[float, float] = (8, 8)) -> Tuple[Figure, Axes]:
    """Create a blank white-background figure/axes pair to draw into.

    Args:
        figsize: (width, height) in inches.

    Returns:
        (fig, ax) tuple of a new matplotlib Figure and its single Axes.
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("none")
    return fig, ax


def draw_nodes(
    ax: Axes,
    positions: Sequence[Point],
    node_colors: Sequence[str],
    marker_size: float = 60,
) -> None:
    """Draw node markers at their circle positions.

    Args:
        ax: Axes to draw into.
        positions: Node (x, y) positions.
        node_colors: Per-node color, aligned with `positions`.
        marker_size: Marker area in points^2 (as used by ax.scatter).
    """
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    ax.scatter(xs, ys, s=marker_size, c=node_colors, zorder=3, edgecolors="none")


def _bezier_path(p1: Point, p2: Point, curvature: float) -> Path:
    """Build a quadratic Bezier matplotlib Path from p1 to p2."""
    control = layout.bezier_control_point(p1, p2, curvature)
    return Path([p1, control, p2], [Path.MOVETO, Path.CURVE3, Path.CURVE3])


def _sample_bezier(p1: Point, control: Point, p2: Point, n: int) -> List[Point]:
    """Sample n evenly-spaced points along a quadratic Bezier curve."""
    ts = np.linspace(0.0, 1.0, n)
    xs = (1 - ts) ** 2 * p1[0] + 2 * (1 - ts) * ts * control[0] + ts**2 * p2[0]
    ys = (1 - ts) ** 2 * p1[1] + 2 * (1 - ts) * ts * control[1] + ts**2 * p2[1]
    return list(zip(xs, ys))


def _draw_gradient_edge(
    ax: Axes,
    p1: Point,
    p2: Point,
    curvature: float,
    color_a: str,
    color_b: str,
    lw: float,
    n_segments: int = 30,
) -> None:
    """Draw a Bezier chord as a multi-segment gradient from color_a to
    color_b."""
    control = layout.bezier_control_point(p1, p2, curvature)
    pts = _sample_bezier(p1, control, p2, n_segments + 1)
    segments = [[pts[k], pts[k + 1]] for k in range(len(pts) - 1)]
    seg_colors = [
        color_utils.interpolate_color(color_a, color_b, t)
        for t in np.linspace(0.0, 1.0, n_segments)
    ]
    lc = LineCollection(
        segments, colors=seg_colors, linewidths=lw, capstyle="round", zorder=1
    )
    ax.add_collection(lc)


def draw_edges(
    ax: Axes,
    positions: Sequence[Point],
    edges: Sequence[Edge],
    curvature: float = defaults.EDGE_CURVATURE,
    linewidth_range: Tuple[float, float] = defaults.EDGE_LINEWIDTH_RANGE,
) -> None:
    """Draw all edges as curved (Bezier) chords between node positions.

    Args:
        ax: Axes to draw into.
        positions: Node (x, y) positions, indexed by node index.
        edges: Sequence of (i, j, weight, color_a, color_b). When
            color_a == color_b the edge is a solid-colored chord;
            otherwise it is drawn as a gradient from color_a to color_b.
        curvature: Bezier curvature, see layout.bezier_control_point.
        linewidth_range: (min, max) linewidth in points; edge linewidth
            is scaled linearly by |weight| (clamped to 1.0) between them.
    """
    min_lw, max_lw = linewidth_range
    for i, j, weight, color_a, color_b in edges:
        p1, p2 = positions[i], positions[j]
        lw = min_lw + (max_lw - min_lw) * min(abs(weight), 1.0)
        if color_a == color_b:
            patch = PathPatch(
                _bezier_path(p1, p2, curvature),
                facecolor="none",
                edgecolor=color_a,
                lw=lw,
                capstyle="round",
                zorder=1,
            )
            ax.add_patch(patch)
        else:
            _draw_gradient_edge(ax, p1, p2, curvature, color_a, color_b, lw)


def draw_labels(
    ax: Axes,
    angles: Sequence[float],
    labels: Sequence[Optional[str]],
    font: Optional[str] = None,
    size: float = 10,
    radius: float = defaults.NODE_RADIUS,
) -> None:
    """Draw a radial label just outside each node.

    Labels on the left half of the circle are rotated 180 degrees (and
    right-aligned instead of left-aligned) so all text reads upright.

    Args:
        ax: Axes to draw into.
        angles: Node angles in radians, aligned with `labels`.
        labels: Per-node label text; falsy entries (None/"") are skipped.
        font: Font family name, or None for the matplotlib default.
        size: Font size in points.
        radius: Node circle radius; labels are placed just outside it.
    """
    label_radius = radius * 1.05
    for angle, label in zip(angles, labels):
        if not label:
            continue
        lx, ly = layout.polar_to_xy(angle, label_radius)
        deg = math.degrees(angle) % 360
        on_left = 90 < deg < 270
        rotation = deg + 180 if on_left else deg
        ha = "right" if on_left else "left"
        ax.text(
            lx,
            ly,
            label,
            rotation=rotation,
            rotation_mode="anchor",
            ha=ha,
            va="center",
            fontsize=size,
            fontfamily=font,
            zorder=4,
        )


def _raw_angle(pos: float, n: int) -> float:
    """Unwrapped angle (radians) for a fractional node position.

    Unlike layout.compute_node_angles, this is not wrapped to [0, 2*pi),
    so it stays monotonic across a group span and can be evaluated at
    the fractional positions used to pad bracket arcs slightly beyond
    their first/last node.
    """
    return math.pi / 2 - pos * (2 * math.pi / n)


def _char_advance_widths_pt(
    text: str, font: Optional[str], size: float
) -> List[float]:
    """Per-character glyph advance widths, in points.

    Uses FreeType font metrics directly (via matplotlib's font cache),
    so this works without a live canvas renderer or a draw() call, and
    correctly includes whitespace advance width (unlike measuring an
    inked bounding box).

    Args:
        text: String whose characters' widths should be measured.
        font: Font family name, or None for the matplotlib default.
        size: Font size in points.

    Returns:
        List of advance widths in points, one per character of `text`.
        Falls back to a fixed 0.6 * size per character if font metrics
        are unavailable for any reason.
    """
    try:
        face = FT2Font(findfont(FontProperties(family=font, size=size)))
        face.set_size(size, 72)
        widths = []
        for ch in text:
            face.clear()
            face.set_text(ch, 0)
            width, _height = face.get_width_height()
            widths.append(width / 64.0)
        return widths
    except (RuntimeError, ValueError, OSError):
        return [0.6 * size for _ in text]


def _points_per_data_unit(fig: Figure, ax: Axes, extent: float) -> float:
    """Approximate conversion factor from data units to points.

    Uses the figure size and the axes' figure-relative position (both
    known from layout alone, without needing a rendered canvas) together
    with the fixed view `extent` set by finalize_axes.

    Args:
        fig: Figure the axes belongs to.
        ax: Axes the data units are measured in.
        extent: Half-width of the (square) view set by finalize_axes.

    Returns:
        Number of points per one data unit along the x axis.
    """
    fig_width_in, _fig_height_in = fig.get_size_inches()
    axes_width_in = ax.get_position().width * fig_width_in
    data_width = 2 * extent
    return (axes_width_in * 72.0) / data_width


def draw_arc_text(
    ax: Axes,
    fig: Figure,
    text: str,
    mid_angle: float,
    radius: float,
    font: Optional[str] = None,
    size: float = 10,
    extent: float = defaults.PLOT_EXTENT,
) -> None:
    """Draw text curved along a circular arc, centered on `mid_angle`.

    Characters are spaced using their real glyph advance widths (normal,
    non-stretched letter spacing), centered as a whole on `mid_angle`,
    and each is rotated to be tangent to the circle at its position (the
    text baseline follows the arc's curvature). On the bottom half of
    the circle, each glyph's rotation is flipped 180 degrees so the text
    still reads correctly and upright when traced along the curve.

    Args:
        ax: Axes to draw into.
        fig: Figure `ax` belongs to (used to convert font points to data
            units).
        text: String to render along the arc.
        mid_angle: Angle (radians) to center the text on.
        radius: Radius at which to place the text.
        font: Font family name, or None for the matplotlib default.
        size: Font size in points.
        extent: Half-width of the (square) view set by finalize_axes;
            must match the value finalize_axes will be called with.
    """
    if not text:
        return

    points_per_data_unit = _points_per_data_unit(fig, ax, extent)
    widths_data = [
        w / points_per_data_unit for w in _char_advance_widths_pt(text, font, size)
    ]
    total_width = sum(widths_data)

    offsets = []
    cumulative = 0.0
    for width in widths_data:
        offsets.append(cumulative + width / 2.0 - total_width / 2.0)
        cumulative += width

    mid_deg = math.degrees(mid_angle) % 360
    flip = 90 < mid_deg < 270

    for ch, offset in zip(text, offsets):
        angle = mid_angle - offset / radius
        x, y = layout.polar_to_xy(angle, radius)
        deg = math.degrees(angle)
        rotation = deg - 90 + (180 if flip else 0)
        ax.text(
            x,
            y,
            ch,
            rotation=rotation,
            rotation_mode="anchor",
            ha="center",
            va="center",
            fontsize=size,
            fontfamily=font,
            zorder=4,
        )


def draw_group_brackets(
    ax: Axes,
    fig: Figure,
    n: int,
    groups: Sequence[Group],
    font: Optional[str] = None,
    size: float = 10,
    radius: float = defaults.NODE_RADIUS,
    extent: float = defaults.PLOT_EXTENT,
) -> None:
    """Draw a bracket arc plus curved label over each secondary-label
    group.

    The label sits just outside the bracket (at a slightly larger
    radius), curving the same way as the bracket beneath it.

    Args:
        ax: Axes to draw into.
        fig: Figure `ax` belongs to (passed through to draw_arc_text).
        n: Total number of nodes (used to convert group positions to
            angles).
        groups: (label, start_pos, end_pos) tuples, as returned by
            layout.detect_groups.
        font: Font family name for the group label, or None for default.
        size: Font size in points for the group label.
        radius: Node circle radius; the bracket is drawn just outside it.
        extent: Half-width of the (square) view set by finalize_axes;
            must match the value finalize_axes will be called with.
    """
    bracket_radius = radius * 1.15
    text_radius = bracket_radius * 1.06
    half_gap = 0.4
    for label, start_pos, end_pos in groups:
        a_start = _raw_angle(start_pos - half_gap, n)
        a_end = _raw_angle(end_pos + half_gap, n)
        arc_angles = np.linspace(a_start, a_end, 50)
        xs = bracket_radius * np.cos(arc_angles)
        ys = bracket_radius * np.sin(arc_angles)
        ax.plot(xs, ys, color="black", lw=1.2, solid_capstyle="round", zorder=2)
        for a in (a_start, a_end):
            x0, y0 = bracket_radius * math.cos(a), bracket_radius * math.sin(a)
            x1, y1 = radius * 1.02 * math.cos(a), radius * 1.02 * math.sin(a)
            ax.plot([x0, x1], [y0, y1], color="black", lw=1.2, zorder=2)
        mid_angle = (a_start + a_end) / 2.0
        draw_arc_text(ax, fig, label, mid_angle, text_radius, font, size, extent)


def draw_group_legend(
    ax: Axes,
    node_colors: Sequence[str],
    groups: Sequence[Group],
    font: Optional[str] = None,
    size: float = 10,
) -> None:
    """Draw a bottom-right legend mapping secondary-label groups to
    colors.

    Args:
        ax: Axes to draw into.
        node_colors: Per-node colors, as returned by
            colors.resolve_node_colors; the first node of each group is
            used as that group's representative swatch.
        groups: (label, start_pos, end_pos) tuples, as returned by
            layout.detect_groups.
        font: Font family name for the legend labels, or None for
            default.
        size: Font size in points for the legend labels.
    """
    seen = {}
    for label, start_pos, _end_pos in groups:
        if label not in seen:
            seen[label] = node_colors[start_pos]
    if not seen:
        return
    handles = [Patch(color=color, label=label) for label, color in seen.items()]
    legend_kwargs = dict(
        loc="lower right", bbox_to_anchor=(1.3, -0.05), fontsize=size, frameon=False
    )
    if font:
        legend_kwargs["prop"] = {"family": font, "size": size}
    ax.legend(handles=handles, **legend_kwargs)


def finalize_axes(ax: Axes, extent: float = defaults.PLOT_EXTENT) -> None:
    """Apply final axes styling: equal aspect, fixed extent, no frame.

    Args:
        ax: Axes to finalize.
        extent: Half-width/height of the (square) view, in data units.
    """
    ax.set_xlim(-extent, extent)
    ax.set_ylim(-extent, extent)
    ax.set_aspect("equal")
    ax.axis("off")
