"""Pure geometry helpers for arranging nodes and edges on a circle.

No matplotlib here -- this module only computes numbers/points that
renderer.py then draws.
"""

import math
from typing import Dict, List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Group = Tuple[str, int, int]


def compute_node_angles(n: int) -> List[float]:
    """Compute evenly spaced node angles around a circle.
        Needed for determining node label positions

    Parameters:
        n: Number of nodes to place. Non-positive values yield no angles.

    Returns:
        List of n angles in radians, starting at the top (12 o'clock,
        pi/2) and proceeding clockwise, each wrapped to [0, 2*pi).
    """
    if n <= 0:
        return []
    step = 2 * math.pi / n
    return [(math.pi / 2 - i * step) % (2 * math.pi) for i in range(n)]


def polar_to_xy(angle: float, radius: float = 1.0) -> Point:
    """Convert a polar coordinate to Cartesian (x, y).

    Parameters:
        angle: Angle in radians.
        radius: Distance from the origin.

    Returns:
        (x, y) Cartesian coordinates.
    """
    return radius * math.cos(angle), radius * math.sin(angle)


def compute_node_positions(n: int, radius: float = 1.0) -> List[Point]:
    """Compute node (x, y) positions evenly spaced on a circle.

    Parameters:
        n: Number of nodes to place.
        radius: Circle radius the nodes sit on.

    Returns:
        List of n (x, y) positions, in the same order as
        compute_node_angles(n).
    """
    return [polar_to_xy(a, radius) for a in compute_node_angles(n)]


def compute_hemi_flip_order(n: int) -> List[int]:
    """Compute a draw order that mirrors the second half of nodes.

    Assumes node indices [0, n/2) are one hemisphere and [n/2, n) are the
    other, each internally ordered the same way (e.g. anterior to
    posterior). Keeps the first half's order as-is and reverses the
    second half, so node n/2 (the second half's first node) ends up
    adjacent to node 0 at one end, and node n-1 ends up adjacent to node
    n/2-1 at the other -- the two hemispheres mirror each other across
    the split points instead of both winding the same rotational
    direction.

    For odd n, the first half gets n // 2 nodes and the second half gets
    the remaining n - n // 2.

    Parameters:
        n: Total number of nodes.

    Returns:
        List of n node indices, in draw-position order (position i holds
        node order[i]) -- suitable as the `order` passed to
        compute_node_angles-indexed data, or to detect_groups.
    """
    half = n // 2
    return list(range(half)) + list(range(n - 1, half - 1, -1))


def detect_groups(
    order: Sequence[int],
    secondary_labels: Optional[Dict[int, str]],
    hard_breaks: Optional[Sequence[int]] = None,
) -> List[Group]:
    """Find contiguous runs of nodes sharing the same secondary label.

    Nodes are assumed to already be index-adjacent within each secondary
    label group (guaranteed by upstream data prep), so this only needs a
    single pass merging consecutive equal labels -- no sorting/reordering.
    The scan never wraps around, so position 0 and the last position are
    never merged even if they share a label.

    Parameters:
        order: Node indices in draw order (position i holds node
            order[i]).
        secondary_labels: Mapping of node index to secondary label. Nodes
            missing from the mapping (or mapped to None) belong to no
            group. May be None or empty, meaning no groups at all.
        hard_breaks: Positions after which a new group is always started,
            even if the label is unchanged -- e.g. the hemisphere split
            introduced by compute_hemi_flip_order, where the last node of
            one hemisphere and the (now-adjacent) last node of the other
            can coincidentally share a label but must stay two brackets.

    Returns:
        List of (label, start_pos, end_pos) tuples, where start_pos and
        end_pos are inclusive positions within `order` (not node indices).
    """
    breaks = set(hard_breaks) if hard_breaks else set()
    groups: List[Group] = []
    current_label: Optional[str] = None
    start_pos = 0
    for pos, idx in enumerate(order):
        label = secondary_labels.get(idx) if secondary_labels else None
        if label == current_label and label is not None and (pos - 1) not in breaks:
            continue
        if current_label is not None:
            groups.append((current_label, start_pos, pos - 1))
        current_label = label
        start_pos = pos
    if current_label is not None:
        groups.append((current_label, start_pos, len(order) - 1))
    return groups


def bezier_control_point(p1: Point, p2: Point, curvature: float) -> Point:
    """Compute the control point for a quadratic Bezier chord.

    Parameters:
        p1: Start point of the chord.
        p2: End point of the chord.
        curvature: 0.0 pulls the control point to the origin (center),
            producing the classic chord-diagram bow through the middle of
            the circle. 1.0 leaves the control point at the midpoint of
            p1/p2, i.e. a straight line between them.

    Returns:
        (x, y) control point for a quadratic Bezier curve from p1 to p2.
    """
    mx, my = (p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0
    return mx * curvature, my * curvature
