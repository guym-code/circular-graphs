"""Integration tests: exercise Thresholds/thresholds.py against real,
messy data from Main__Data/, instead of the small hand-built matrices
used in the other test_thresholds_*.py files.

Real connectomes behave differently from tidy synthetic examples -- in
particular this dataset is near-complete (almost every possible edge is
nonzero) and lopsided in scale (positive correlations reach much higher
magnitudes than negative ones). These tests are written to hold up
against whatever the real numbers happen to be, by deriving "expected"
values from the same matrix rather than hardcoding magic numbers -- so
they double as regression tests if Main__Data/ is ever regenerated.

Marked `integration` (slower, and skips itself if the data file isn't
present -- e.g. a fresh clone without Main__Data/ populated):
    pytest -m integration        # run only these
    pytest -m "not integration"  # skip these, run the fast unit tests
"""

from pathlib import Path

import numpy as np
import pytest

from I_O.edge_list2mat import edge_list_to_matrix
from I_O.edge_loader import load_edge_list
from Thresholds import thresholds as t

pytestmark = pytest.mark.integration

DATA_PATH = Path(__file__).resolve().parent.parent / "Main__Data" / "edge_list_scf100.csv"


@pytest.fixture(scope="module")
def real_matrix() -> np.ndarray:
    """Schaefer-100 resting-state Pearson correlation matrix, subject 0.

    Loaded through the project's real I_O pipeline (not re-parsed by
    hand here), so this exercises Thresholds against data prepared
    exactly the way CircularGraph prepares it. Module-scoped: parsing a
    4951-column CSV is comparatively expensive, so every test in this
    file shares one load.
    """
    if not DATA_PATH.exists():
        pytest.skip(f"real dataset not found at {DATA_PATH}")
    edge_index, edge_values = load_edge_list(DATA_PATH)
    return edge_list_to_matrix(edge_values, edge_index, subject_idx=0)


def test_real_matrix_sanity(real_matrix):
    assert real_matrix.shape == (100, 100)
    assert np.array_equal(real_matrix, real_matrix.T)
    assert (real_matrix > 0).any() and (real_matrix < 0).any()


@pytest.mark.parametrize(
    "method,params",
    [
        ("weighted_average", dict(value=0.25)),
        ("positive_negative_value", dict(positive_value=0.3, negative_value=-0.3)),
        (
            "positive_negative_percentile_value",
            dict(value_positive=90.0, value_negative=90.0),
        ),
    ],
)
def test_structural_invariants_hold_on_real_data(real_matrix, method, params):
    result = t.apply_threshold(real_matrix, method, **params)
    n = real_matrix.shape[0]

    assert result.node_mask.shape == (n,)
    assert result.edge_mask.shape == (n, n)
    assert np.array_equal(result.edge_mask, result.edge_mask.T)
    assert not result.edge_mask.diagonal().any()
    assert not (result.edge_mask & (real_matrix == 0)).any()
    # thresholding must actually remove *something* at these cutoffs
    assert result.n_kept_edges < int(np.count_nonzero(np.triu(real_matrix, k=1)))


def test_weighted_average_cutoff_above_max_metric_is_still_empty_on_real_data(
    real_matrix,
):
    metric = t.node_average_strength(real_matrix)
    result = t.apply_threshold(
        real_matrix, "weighted_average", value=float(metric.max()) + 1.0
    )
    assert result.n_kept == 0
    assert result.n_kept_edges == 0


def test_dense_real_graph_can_keep_every_node_while_shedding_many_edges(real_matrix):
    # This dataset is near-complete, so a moderate hub cutoff sheds a
    # real chunk of edges without necessarily isolating any node --
    # verifying that expectation doesn't silently rot into "0 edges
    # kept" or "no edges dropped" if the data changes.
    result = t.apply_threshold(real_matrix, "weighted_average", value=0.25)
    total_edges = int(np.count_nonzero(np.triu(real_matrix, k=1)))
    assert 0 < result.n_kept_edges < total_edges


def test_percentile_and_absolute_value_can_disagree_sharply_on_lopsided_real_data(
    real_matrix,
):
    # Independently derive what each method *should* keep on the
    # negative side, straight from the matrix, instead of hardcoding
    # numbers -- then confirm the module's output matches.
    negative_cutoff = -0.3
    expected_abs_negative_edges = int(
        np.count_nonzero(np.triu(real_matrix < negative_cutoff, k=1))
    )

    abs_result = t.apply_threshold(
        real_matrix,
        "positive_negative_value",
        positive_value=0.3,
        negative_value=negative_cutoff,
    )
    actual_abs_negative_edges = int(
        np.count_nonzero(np.triu(abs_result.edge_mask & (real_matrix < 0), k=1))
    )
    assert actual_abs_negative_edges == expected_abs_negative_edges

    n_negative_total = int(np.count_nonzero(np.triu(real_matrix < 0, k=1)))
    expected_pct_negative_edges = round(n_negative_total * 0.10)

    pct_result = t.apply_threshold(
        real_matrix,
        "positive_negative_percentile_value",
        value_positive=90.0,
        value_negative=90.0,
    )
    actual_pct_negative_edges = int(
        np.count_nonzero(np.triu(pct_result.edge_mask & (real_matrix < 0), k=1))
    )
    assert actual_pct_negative_edges == pytest.approx(
        expected_pct_negative_edges, abs=2
    )

    # The actual point of this test: on data whose negative values sit
    # close to a fixed absolute cutoff, percentile-based thresholding
    # keeps meaningfully more of that side than an absolute cutoff does.
    assert actual_pct_negative_edges > actual_abs_negative_edges


def test_apply_and_filter_drop_isolated_nodes_never_increases_node_count(real_matrix):
    for method, params in [
        ("weighted_average", dict(value=0.3)),
        ("positive_negative_value", dict(positive_value=0.5, negative_value=-0.5)),
    ]:
        kept_mat, _, _, _ = t.apply_and_filter(real_matrix, method, **params)
        dropped_mat, _, _, _ = t.apply_and_filter(
            real_matrix, method, drop_isolated_nodes=True, **params
        )
        assert kept_mat.shape[0] == real_matrix.shape[0]
        assert dropped_mat.shape[0] <= kept_mat.shape[0]
