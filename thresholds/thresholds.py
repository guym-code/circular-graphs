"""Visibility thresholding for circular graph plots.

Decides what's "shown" for a given connectivity matrix, the same way
plotting/colors.py decides what color things are and plotting/layout.py
decides where things sit. Nothing here touches matplotlib; the output
is a boolean mask (and the numeric metric it came from) that an
upstream caller (a GUI, plotting/graph_plot.py, or a script) uses to
filter the graph before plot() ever sees it.

The three methods split across two different levels, and mixing them
up is an easy mistake (this module used to make it):

* weighted_average is the only method that is genuinely about *nodes*:
  it finds "hub" nodes by their average (absolute) connection
  strength, then keeps every edge that touches a hub -- including a
  hub's edges to non-hub neighbors, since those neighbors have to be
  drawn too for the edge to make sense.
* positive_negative_value and positive_negative_percentile_value are
  properties of a single connection -- i.e. they threshold *edges*,
  individually, exactly like colors.resolve_edge_color_pair or
  graph_plot.plot's own i<j edge loop already do. "The strength of an
  edge" is not a node-level idea. A plain (unsigned) absolute-value or
  percentile method was deliberately dropped: passing the same value
  as both `positive_value`/`-negative_value` (or both percentile
  cutoffs) reproduces it with one fewer choice in the GUI.

The module is layered across three styles, since each threshold method
is naturally a small, self-contained *policy* while the metrics it's
built from are shared, reusable *math*:

* Functional core -- small, stateless, side-effect-free functions that
  turn a raw connectivity matrix into per-node or per-edge metrics
  (connection counts, strength, positive/negative strength, percentile
  rank). These have no knowledge of "thresholds" at all and are
  independently testable/reusable.
* Object-oriented strategies -- one frozen dataclass per threshold
  method (WeightedAverageThreshold, PositiveNegativeValueThreshold,
  ...), each encapsulating its own parameters and validation behind a
  single public `.apply(mat)` method (Strategy pattern). Constructing
  one *is* the parametrization step; nothing about "how" is exposed
  beyond that.
* Procedural entry points -- plain top-level functions
  (apply_threshold, filter_graph_by_mask, apply_and_filter) that a GUI
  form or graph_plot.py can call with primitive arguments (a method
  name + a dict of parameters) without ever importing or knowing about
  the strategy classes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import rankdata

from thresholds import defaults_thresholds as defaults

# The three mutually-exclusive ways to decide what's "important enough"
# to show. weighted_average is "node"-level (it finds hubs); the other
# two are "edge"-level.
VALID_THRESHOLD_METHODS = (
    "weighted_average",
    "positive_negative_value",
    "positive_negative_percentile_value",
)

# Parameter names accepted by each method's constructor, in the order
# given in the product spec. A GUI can loop over
# THRESHOLD_PARAM_SCHEMAS[method] to build its form fields without
# hardcoding anything method-specific.
THRESHOLD_PARAM_SCHEMAS: Dict[str, Tuple[str, ...]] = {
    "weighted_average": ("value",),
    "positive_negative_value": ("positive_value", "negative_value"),
    "positive_negative_percentile_value": (
        "greater_than_positive",
        "value_positive",
        "greater_than_negative",
        "value_negative",
    ),
}


# ---------------------------------------------------------------------------
# Functional core: pure metric computations.
# ---------------------------------------------------------------------------


def _zero_diagonal(mat: np.ndarray) -> np.ndarray:
    """Return a float copy of `mat` with its diagonal forced to zero.

    Self-connections should never contribute to a node's connection
    count/strength or count as an edge; this guards that regardless of
    whether the caller's matrix already has a clean zero diagonal.

    Args:
        mat: n x n connectivity matrix.

    Returns:
        Float array, shape (n, n), with diagonal zeroed.
    """
    out = np.array(mat, dtype=float, copy=True)
    np.fill_diagonal(out, 0.0)
    return out


def _upper_triangle_mask(n: int) -> np.ndarray:
    """Boolean n x n mask, True where i < j (each undirected edge once).

    Args:
        n: Number of nodes (matrix is n x n).

    Returns:
        Boolean array, shape (n, n), True at every off-diagonal upper
        triangle entry.
    """
    return np.triu(np.ones((n, n), dtype=bool), k=1)


def _existing_edge_mask(mat: np.ndarray) -> np.ndarray:
    """Boolean n x n mask, True at every off-diagonal nonzero entry.

    A zero weight means "no edge" (graph_plot.plot skips it outright),
    so every edge-level mask below is ANDed with this: no threshold
    direction or comparison should ever be able to conjure a "kept"
    edge out of a connection that doesn't exist.

    Args:
        mat: n x n connectivity matrix.

    Returns:
        Boolean array, shape (n, n), True at every off-diagonal nonzero entry.
    """
    return _zero_diagonal(mat) != 0


def node_connection_counts(mat: Sequence[Sequence[float]]) -> np.ndarray:
    """Number of nonzero edges incident to each node.

    Args:
        mat: n x n connectivity matrix.

    Returns:
        Integer array, shape (n,): count of nonzero off-diagonal entries
        in each row.
    """
    mat = _zero_diagonal(np.asarray(mat, dtype=float))
    return np.count_nonzero(mat, axis=1)


def node_strength(mat: Sequence[Sequence[float]], absolute: bool = True) -> np.ndarray:
    """Total edge weight incident to each node.

    Args:
        mat: n x n connectivity matrix.
        absolute: If True (default), sum |weight| per row, so strongly
            negative and strongly positive edges both count toward a
            node's strength. If False, sum the signed weights, so
            positive and negative edges can cancel out.

    Returns:
        Float array, shape (n,): per-node strength.
    """
    mat = _zero_diagonal(np.asarray(mat, dtype=float))
    return (np.abs(mat) if absolute else mat).sum(axis=1)


def node_average_strength(mat: Sequence[Sequence[float]]) -> np.ndarray:
    """Average absolute edge weight per node, over its actual connections.

    This is the "weighted average" hub metric: total absolute strength
    divided by number of connections, so a node with a few very strong
    edges and a node with many moderately strong edges can both score
    as hubs, while a node with many very weak edges does not.

    Args:
        mat: n x n connectivity matrix.

    Returns:
        Float array, shape (n,): per-node average |weight|, 0 for a
        node with no connections (rather than dividing by zero).
    """
    counts = node_connection_counts(mat)
    strength = node_strength(mat, absolute=True)
    return np.divide(
        strength, counts, out=np.zeros_like(strength), where=counts > 0
    )


def edge_strength(mat: Sequence[Sequence[float]], absolute: bool = True) -> np.ndarray:
    """Per-edge weight, as an n x n matrix (diagonal zeroed).

    Args:
        mat: n x n connectivity matrix.
        absolute: If True (default), return |weight|; if False, return
            the signed weight unchanged.

    Returns:
        Float array, shape (n, n).
    """
    mat = _zero_diagonal(np.asarray(mat, dtype=float))
    return np.abs(mat) if absolute else mat


def percentile_rank(values: Sequence[float]) -> np.ndarray:
    """Percentile rank (0-100) of each value within its own population.

    Ties share the same percentile (average-rank method), and a
    single-value population maps to 0 rather than dividing by zero.

    Args:
        values: 1D sequence of metric values.

    Returns:
        Float array, same shape as `values`, each entry in [0, 100].
    """
    values = np.asarray(values, dtype=float)
    n = values.size
    if n <= 1:
        return np.zeros_like(values)
    ranks = rankdata(values, method="average")
    return (ranks - 1) / (n - 1) * 100.0


def edge_positive_percentile_rank(mat: Sequence[Sequence[float]]) -> np.ndarray:
    """Percentile rank of each strictly-positive edge, within the
    population of positive edges only (zero/negative edges excluded
    from that population, not just clipped to it).

    Args:
        mat: n x n connectivity matrix.

    Returns:
        Float array, shape (n, n), symmetric. Non-positive entries
        (including the diagonal) are -1.0.
    """
    mat = _zero_diagonal(np.asarray(mat, dtype=float))
    n = mat.shape[0]
    iu, ju = np.where(_upper_triangle_mask(n) & (mat > 0))
    out = np.full((n, n), -1.0)
    if iu.size:
        pct = percentile_rank(mat[iu, ju])
        out[iu, ju] = pct
        out[ju, iu] = pct
    return out


def edge_negative_percentile_rank(mat: Sequence[Sequence[float]]) -> np.ndarray:
    """Percentile rank of each strictly-negative edge's magnitude,
    within the population of negative edges only (zero/positive edges
    excluded from that population, not just clipped to it).

    Args:
        mat: n x n connectivity matrix.

    Returns:
        Float array, shape (n, n), symmetric. Non-negative entries
        (including the diagonal) are -1.0.
    """
    mat = _zero_diagonal(np.asarray(mat, dtype=float))
    n = mat.shape[0]
    iu, ju = np.where(_upper_triangle_mask(n) & (mat < 0))
    out = np.full((n, n), -1.0)
    if iu.size:
        pct = percentile_rank(np.abs(mat[iu, ju]))
        out[iu, ju] = pct
        out[ju, iu] = pct
    return out


def _compare(metric: np.ndarray, value: float, greater_than: bool) -> np.ndarray:
    """Elementwise 'passes the cutoff' test in the direction requested.

    Args:
        metric: Numeric array of per-node or per-edge metrics.
        value: Cutoff value to compare against.
        greater_than: If True, "pass" means metric > value; if False,
            "pass" means metric < value.

    Returns:
        Boolean array, same shape as `metric`, True where the metric
        passes the cutoff test.
    """
    return metric > value if greater_than else metric < value


def _validate_matrix(mat: Sequence[Sequence[float]]) -> np.ndarray:
    """Coerce `mat` to a float ndarray and check it's square 2D.

    Args:
        mat: n x n connectivity matrix.

    Returns:
        Float array, shape (n, n), same as `mat`.

    Raises:
        ValueError: If `mat` isn't square 2D.
    """
    mat = np.asarray(mat, dtype=float)
    if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
        raise ValueError(
            f"Connectivity matrix must be square 2D, got shape {mat.shape}"
        )
    return mat


def _validate_percentile(name: str, val: float) -> None:
    """Validate that a value is within the percentile range [0, 100].

    Args:
        name: Name of the parameter being validated.
        val: Value to validate.

    Raises:
        ValueError: If the value is not within the percentile range.
    """
    if not (0.0 <= val <= 100.0):
        raise ValueError(f"{name} must be within [0, 100], got {val}")


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ThresholdResult:
    """Outcome of applying a Threshold to a connectivity matrix.

    Every method produces both a node_mask and an edge_mask, but only
    one of them is *directly* computed (see `level`) -- the other is
    derived, so callers always have a straightforward answer to "which
    nodes/edges are shown" regardless of which method was used:

    * level == "node" (weighted_average): node_mask marks hubs plus
      any node with a surviving hub-touching edge. edge_mask is
      derived as "at least one endpoint is a hub" -- a hub's edges to
      non-hub neighbors are kept, not just hub-to-hub edges.
    * level == "edge" (positive_negative_value,
      positive_negative_percentile_value): edge_mask is the primary
      decision. node_mask is derived as "this node has at least one
      surviving edge" -- purely informational; whether a GUI actually
      uses it to drop isolated nodes is a separate, opt-in choice (see
      apply_and_filter's `drop_isolated_nodes`).

    Attributes:
        node_mask: Boolean array, shape (n,); True for nodes kept.
        edge_mask: Boolean array, shape (n, n), symmetric; True for
            edges kept.
        metric: The underlying numeric metric the mask was computed
            from -- shape (n,) for weighted_average, shape (n, n) for
            positive_negative_value, shape (n, n, 2) for
            positive_negative_percentile_value.
        method: Name of the threshold method used (one of
            VALID_THRESHOLD_METHODS).
        level: "node" or "edge" -- which mask above was computed
            directly rather than derived.
    """

    node_mask: np.ndarray
    edge_mask: np.ndarray
    metric: np.ndarray
    method: str
    level: str

    @property
    def n_kept(self) -> int:
        """Number of nodes the mask keeps.

        Returns:
            Count of True entries in `node_mask`.
        """
        return int(np.count_nonzero(self.node_mask))

    @property
    def kept_indices(self) -> np.ndarray:
        """Indices (into the original matrix) of the kept nodes.

        Returns:
            Integer array of indices where `node_mask` is True.
        """
        return np.flatnonzero(self.node_mask)

    @property
    def n_kept_edges(self) -> int:
        """Number of (undirected) edges the mask keeps.

        Returns:
            Count of True entries in the upper triangle of `edge_mask`.
        """
        return int(np.count_nonzero(np.triu(self.edge_mask, k=1)))


# ---------------------------------------------------------------------------
# Object-oriented strategies: one class per threshold method.
# ---------------------------------------------------------------------------


class Threshold(ABC):
    """Base strategy: turns a connectivity matrix into a ThresholdResult.

    Each subclass encapsulates exactly one method's parameters (set once,
    at construction -- instances are frozen dataclasses) and exposes only
    `.apply()` as public surface; how the metric is computed and compared
    is a private implementation detail of the subclass.
    """

    method: str = ""
    level: str = ""

    @abstractmethod
    def apply(self, mat: Sequence[Sequence[float]]) -> ThresholdResult:
        """Compute the ThresholdResult for `mat` under this method.

        Args:
            mat: n x n connectivity matrix.

        Returns:
            ThresholdResult with this method's node_mask/edge_mask/metric.
        """


class EdgeLevelThreshold(Threshold):
    """Shared `apply()` for the methods that threshold individual edges
    (positive_negative_value, positive_negative_percentile_value):
    computes an edge_mask directly, then derives node_mask as "has at
    least one surviving edge"."""

    level = "edge"

    @abstractmethod
    def _edge_metric(self, mat: np.ndarray) -> np.ndarray:
        """Per-edge metric this method thresholds on.

        Args:
            mat: n x n connectivity matrix (diagonal not yet zeroed).

        Returns:
            Metric array; shape (n, n) for a single metric, or
            shape (n, n, 2) for a positive/negative pair.
        """

    @abstractmethod
    def _edge_mask(self, mat: np.ndarray, metric: np.ndarray) -> np.ndarray:
        """Turn (mat, metric) into a boolean keep-mask.

        Args:
            mat: n x n connectivity matrix (diagonal not yet zeroed).
            metric: This method's `_edge_metric(mat)` output.

        Returns:
            Boolean array, shape (n, n): True for edges that pass.
        """

    def apply(self, mat: Sequence[Sequence[float]]) -> ThresholdResult:
        """Compute the ThresholdResult for `mat` under this edge-level method.

        Args:
            mat: n x n connectivity matrix.

        Returns:
            ThresholdResult with edge_mask computed directly and
            node_mask derived as "has >= 1 surviving edge".
        """
        mat = _validate_matrix(mat)
        metric = self._edge_metric(mat)
        edge_mask = self._edge_mask(mat, metric) & _existing_edge_mask(mat)
        node_mask = edge_mask.any(axis=1)
        return ThresholdResult(
            node_mask=node_mask,
            edge_mask=edge_mask,
            metric=metric,
            method=self.method,
            level=self.level,
        )


@dataclass(frozen=True)
class WeightedAverageThreshold(Threshold):
    """Identify hub nodes and show their connections.

    A node is a hub if its average (absolute) connection strength --
    total edge weight divided by number of connections, see
    node_average_strength -- is strictly greater than `value`. Every
    edge touching a hub is then kept, including a hub's edges to
    non-hub neighbors (a connection needs both its endpoints drawn to
    make sense), and any node left with a surviving edge is kept
    alongside the hubs themselves.

    Attributes:
        value: Cutoff on the per-node average absolute edge weight; a
            node with average strength strictly greater than this is
            a hub.
    """

    level = "node"

    value: float = defaults.THRESHOLD_VALUE
    method: str = field(default="weighted_average", init=False)

    def apply(self, mat: Sequence[Sequence[float]]) -> ThresholdResult:
        """Compute the ThresholdResult for `mat` under the hub method.

        Args:
            mat: n x n connectivity matrix.

        Returns:
            ThresholdResult with node_mask marking hubs and their
            neighbors, and edge_mask marking every edge touching a hub.
        """
        mat = _validate_matrix(mat)
        metric = node_average_strength(mat)
        hub_mask = metric > self.value
        edge_mask = (hub_mask[:, None] | hub_mask[None, :]) & _existing_edge_mask(mat)
        node_mask = hub_mask | edge_mask.any(axis=1)
        return ThresholdResult(
            node_mask=node_mask,
            edge_mask=edge_mask,
            metric=metric,
            method=self.method,
            level=self.level,
        )


@dataclass(frozen=True)
class PositiveNegativeValueThreshold(EdgeLevelThreshold):
    """Threshold an edge's positive and negative weight separately,
    keeping it if either side is strong enough.

    Attributes:
        positive_value: An edge is kept if its (signed) weight is
            strictly greater than this.
        negative_value: An edge is also kept if its weight is strictly
            less than this -- i.e. more negative than `negative_value`.
            Pass e.g. -0.3 to keep strongly negative edges.
    """

    positive_value: float = defaults.THRESHOLD_VALUE
    negative_value: float = -defaults.THRESHOLD_VALUE
    method: str = field(default="positive_negative_value", init=False)

    def _edge_metric(self, mat: np.ndarray) -> np.ndarray:
        """Signed edge weight (diagonal zeroed).

        Args:
            mat: n x n connectivity matrix (diagonal not yet zeroed).

        Returns:
            Float array, shape (n, n): signed edge weight per position.
        """
        return edge_strength(mat, absolute=False)

    def _edge_mask(self, mat: np.ndarray, metric: np.ndarray) -> np.ndarray:
        """Keep an edge if it clears the positive or the negative cutoff.

        Args:
            mat: n x n connectivity matrix (unused; metric already
                carries the signed weight).
            metric: This method's `_edge_metric(mat)` output.

        Returns:
            Boolean array, shape (n, n): True where
            metric > positive_value or metric < negative_value.
        """
        return (metric > self.positive_value) | (metric < self.negative_value)


@dataclass(frozen=True)
class PositiveNegativePercentileThreshold(EdgeLevelThreshold):
    """Like PositiveNegativeValueThreshold, but each side is compared by
    percentile rank within its own population (positive edges ranked
    among positive edges, negative edges ranked by magnitude among
    negative edges) rather than by raw value.

    Attributes:
        value_positive: Cutoff percentile (0-100) among positive edges.
        greater_than_positive: Comparison direction for the positive
            side.
        value_negative: Cutoff percentile (0-100) among negative-edge
            magnitudes.
        greater_than_negative: Comparison direction for the negative
            side.
    """

    value_positive: float = defaults.THRESHOLD_PERCENTILE_VALUE
    greater_than_positive: bool = defaults.THRESHOLD_GREATER_THAN
    value_negative: float = defaults.THRESHOLD_PERCENTILE_VALUE
    greater_than_negative: bool = defaults.THRESHOLD_GREATER_THAN
    method: str = field(default="positive_negative_percentile_value", init=False)

    def __post_init__(self) -> None:
        """Validate that both cutoff percentiles are within [0, 100].

        Raises:
            ValueError: If `value_positive` or `value_negative` is
                outside [0, 100].
        """
        _validate_percentile("value_positive", self.value_positive)
        _validate_percentile("value_negative", self.value_negative)

    def _edge_metric(self, mat: np.ndarray) -> np.ndarray:
        """Positive-side and negative-side percentile ranks, stacked.

        Args:
            mat: n x n connectivity matrix (diagonal not yet zeroed).

        Returns:
            Float array, shape (n, n, 2): [..., 0] is
            edge_positive_percentile_rank(mat), [..., 1] is
            edge_negative_percentile_rank(mat).
        """
        positive_pct = edge_positive_percentile_rank(mat)
        negative_pct = edge_negative_percentile_rank(mat)
        return np.stack([positive_pct, negative_pct], axis=-1)

    def _edge_mask(self, mat: np.ndarray, metric: np.ndarray) -> np.ndarray:
        """Keep an edge if its own-sign percentile clears that side's cutoff.

        Args:
            mat: n x n connectivity matrix; only its sign is used, to
                gate each edge to the side its percentile was ranked on.
            metric: This method's `_edge_metric(mat)` output.

        Returns:
            Boolean array, shape (n, n): True where a positive edge
            clears the positive-side cutoff, or a negative edge clears
            the negative-side cutoff.
        """
        positive_pct, negative_pct = metric[..., 0], metric[..., 1]
        positive_pass = (mat > 0) & _compare(
            positive_pct, self.value_positive, self.greater_than_positive
        )
        negative_pass = (mat < 0) & _compare(
            negative_pct, self.value_negative, self.greater_than_negative
        )
        return positive_pass | negative_pass


_THRESHOLD_CLASSES: Dict[str, type] = {
    "weighted_average": WeightedAverageThreshold,
    "positive_negative_value": PositiveNegativeValueThreshold,
    "positive_negative_percentile_value": PositiveNegativePercentileThreshold,
}


# ---------------------------------------------------------------------------
# Procedural entry points: plain functions over primitive arguments, for
# a GUI form or graph_plot.py to call without touching the classes above.
# ---------------------------------------------------------------------------


def apply_threshold(
    mat: Sequence[Sequence[float]],
    method: str = defaults.THRESHOLD_METHOD,
    **params,
) -> ThresholdResult:
    """Build the strategy named by `method` and apply it to `mat`.

    This is the single function a GUI form (or graph_plot.py) needs:
    pick a method by name -- see VALID_THRESHOLD_METHODS -- and pass its
    parameters as keywords (see THRESHOLD_PARAM_SCHEMAS), all without
    importing or knowing about the Threshold subclasses.

    Args:
        mat: n x n connectivity matrix.
        method: One of VALID_THRESHOLD_METHODS.
        **params: Keyword parameters for the method's constructor (see
            THRESHOLD_PARAM_SCHEMAS[method]).

    Returns:
        ThresholdResult with the resulting node_mask/edge_mask/metric.

    Raises:
        ValueError: If `method` is unrecognized, or if `params` doesn't
            match what that method's constructor accepts.
    """
    if method not in _THRESHOLD_CLASSES:
        raise ValueError(
            f"Unknown threshold method: {method!r}, expected one of "
            f"{VALID_THRESHOLD_METHODS}"
        )
    cls = _THRESHOLD_CLASSES[method]
    try:
        strategy = cls(**params)
    except TypeError as exc:
        raise ValueError(f"Invalid parameters for method {method!r}: {exc}") from exc
    return strategy.apply(mat)


def filter_graph_by_mask(
    edges_mat: Sequence[Sequence[float]],
    node_mask: Sequence[bool],
    edge_mask: Optional[Sequence[Sequence[bool]]] = None,
    labels_dict: Optional[Dict[int, str]] = None,
    secondary_labels: Optional[Dict[int, str]] = None,
) -> Tuple[np.ndarray, Dict[int, str], Dict[int, str]]:
    """Zero out filtered-out edges and drop filtered-out nodes entirely,
    re-indexing the survivors.

    Kept nodes are renumbered 0..k-1 in their original relative order,
    so the result can be handed straight to graph_plot.plot() (via a
    CircularGraphLike stub) as if it were the whole graph.

    Args:
        edges_mat: n x n connectivity matrix.
        node_mask: Boolean keep-mask, shape (n,), e.g. from
            ThresholdResult.node_mask. Pass all-True to keep every node
            (e.g. for an edge-level method where isolated nodes should
            stay visible -- see apply_and_filter's `drop_isolated_nodes`).
        edge_mask: Optional boolean keep-mask, shape (n, n), e.g. from
            ThresholdResult.edge_mask. Edges failing it are zeroed
            before node filtering. None skips edge filtering entirely.
        labels_dict: Optional node-index -> label mapping, in the
            original n-node indexing.
        secondary_labels: Optional node-index -> secondary-label
            mapping, in the original n-node indexing.

    Returns:
        (filtered_mat, filtered_labels_dict, filtered_secondary_labels),
        all re-indexed to the k = sum(node_mask) kept nodes.

    Raises:
        ValueError: If `edge_mask`'s shape doesn't match `edges_mat`,
            or `node_mask`'s length doesn't match `edges_mat`'s size.
    """
    mat = _validate_matrix(edges_mat)
    if edge_mask is not None:
        edge_mask = np.asarray(edge_mask, dtype=bool)
        if edge_mask.shape != mat.shape:
            raise ValueError(
                f"edge_mask shape {edge_mask.shape} does not match matrix "
                f"shape {mat.shape}"
            )
        mat = np.where(edge_mask, mat, 0.0)

    mask = np.asarray(node_mask, dtype=bool)
    if mask.shape[0] != mat.shape[0]:
        raise ValueError(
            f"node_mask length {mask.shape[0]} does not match matrix size "
            f"{mat.shape[0]}"
        )
    kept = np.flatnonzero(mask)
    filtered_mat = mat[np.ix_(kept, kept)]

    def _remap(d: Optional[Dict[int, str]]) -> Dict[int, str]:
        """Re-index a node-index -> label mapping to the kept, renumbered nodes.

        Args:
            d: Node-index -> label mapping in the original indexing, or
                None/empty.

        Returns:
            Dict mapping new index (0..k-1) -> label, for kept nodes
            that had an entry in `d`.
        """
        if not d:
            return {}
        return {new_i: d[old_i] for new_i, old_i in enumerate(kept) if old_i in d}

    return filtered_mat, _remap(labels_dict), _remap(secondary_labels)


def apply_and_filter(
    edges_mat: Sequence[Sequence[float]],
    method: str = defaults.THRESHOLD_METHOD,
    drop_isolated_nodes: bool = False,
    labels_dict: Optional[Dict[int, str]] = None,
    secondary_labels: Optional[Dict[int, str]] = None,
    **params,
) -> Tuple[np.ndarray, Dict[int, str], Dict[int, str], ThresholdResult]:
    """Compute a threshold and immediately filter the graph by it.

    Convenience wrapper around apply_threshold() + filter_graph_by_mask()
    for the common "compute mask, then drop/zero what didn't pass" case.

    Args:
        edges_mat: n x n connectivity matrix.
        method: One of VALID_THRESHOLD_METHODS.
        drop_isolated_nodes: If False (the default), every node stays
            visible and only edges are zeroed out -- for
            weighted_average that means every node is drawn but only
            edges touching a hub are kept; for the two edge-level
            methods, a node can end up with no remaining edges but is
            still drawn. If True, nodes left with zero surviving edges
            (weighted_average: non-hubs with no hub neighbor) are also
            dropped.
        labels_dict: Optional node-index -> label mapping to re-index.
        secondary_labels: Optional node-index -> secondary-label
            mapping to re-index.
        **params: Parameters for the chosen method (see
            THRESHOLD_PARAM_SCHEMAS[method]).

    Returns:
        (filtered_mat, filtered_labels_dict, filtered_secondary_labels,
        result); `result` is computed against the *original*,
        unfiltered matrix, so its metrics/masks still line up with the
        original node/edge indices for inspection (e.g. plotting a
        histogram of the metric before deciding on a cutoff).
    """
    result = apply_threshold(edges_mat, method, **params)
    if drop_isolated_nodes:
        node_mask = result.node_mask
    else:
        node_mask = np.ones_like(result.node_mask, dtype=bool)

    filtered_mat, filtered_labels, filtered_secondary = filter_graph_by_mask(
        edges_mat, node_mask, result.edge_mask, labels_dict, secondary_labels
    )
    return filtered_mat, filtered_labels, filtered_secondary, result
