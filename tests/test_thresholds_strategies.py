"""Tests for the OO strategy layer: ThresholdResult and the three
Threshold subclasses (WeightedAverageThreshold, PositiveNegativeValueThreshold,
PositiveNegativePercentileThreshold)."""

import numpy as np
import pytest

from Thresholds import thresholds as t


class TestThresholdResult:
    def test_properties(self):
        node_mask = np.array([True, False, True])
        edge_mask = np.array(
            [
                [False, False, True],
                [False, False, False],
                [True, False, False],
            ]
        )
        result = t.ThresholdResult(
            node_mask=node_mask,
            edge_mask=edge_mask,
            metric=np.zeros(3),
            method="positive_negative_value",
            level="edge",
        )
        assert result.n_kept == 2
        assert result.kept_indices.tolist() == [0, 2]
        assert result.n_kept_edges == 1


class TestWeightedAverageThreshold:
    def test_hub_and_its_neighbors_are_kept(self, hub_matrix):
        result = t.WeightedAverageThreshold(value=0.5).apply(hub_matrix)
        assert result.level == "node"
        assert result.node_mask.tolist() == [True, True, True, False]

    def test_only_edges_touching_a_hub_survive(self, hub_matrix):
        result = t.WeightedAverageThreshold(value=0.5).apply(hub_matrix)
        assert result.edge_mask[0, 1] and result.edge_mask[1, 0]
        assert result.edge_mask[0, 2] and result.edge_mask[2, 0]
        # neither node 1 nor node 2 is a hub, so their mutual edge is dropped
        assert not result.edge_mask[1, 2]

    def test_cutoff_above_max_metric_yields_empty_graph(self, hub_matrix):
        result = t.WeightedAverageThreshold(value=999.0).apply(hub_matrix)
        assert result.n_kept == 0
        assert result.n_kept_edges == 0
        assert not result.node_mask.any()
        assert not result.edge_mask.any()

    def test_metric_matches_node_average_strength(self, hub_matrix):
        result = t.WeightedAverageThreshold(value=0.5).apply(hub_matrix)
        assert result.metric == pytest.approx(t.node_average_strength(hub_matrix))


class TestPositiveNegativeValueThreshold:
    def test_keeps_only_edges_beyond_either_cutoff(self, pct_matrix):
        result = t.PositiveNegativeValueThreshold(
            positive_value=0.4, negative_value=-0.5
        ).apply(pct_matrix)
        assert result.level == "edge"
        kept = {(0, 1), (0, 2), (1, 2)}
        for i in range(4):
            for j in range(4):
                expected = (i, j) in kept or (j, i) in kept
                assert bool(result.edge_mask[i, j]) == expected, (i, j)

    def test_derived_node_mask_is_has_any_edge(self, pct_matrix):
        result = t.PositiveNegativeValueThreshold(
            positive_value=0.4, negative_value=-0.5
        ).apply(pct_matrix)
        assert result.node_mask.tolist() == [True, True, True, False]


class TestPositiveNegativePercentileThreshold:
    def test_rejects_out_of_range_percentile(self):
        with pytest.raises(ValueError, match="value_positive"):
            t.PositiveNegativePercentileThreshold(value_positive=150.0)
        with pytest.raises(ValueError, match="value_negative"):
            t.PositiveNegativePercentileThreshold(value_negative=-1.0)

    def test_top_half_each_side_matches_hand_computation(self, pct_matrix):
        result = t.PositiveNegativePercentileThreshold(
            value_positive=50.0, value_negative=50.0
        ).apply(pct_matrix)
        kept = {(0, 1), (0, 2), (1, 2)}
        for i in range(4):
            for j in range(4):
                expected = (i, j) in kept or (j, i) in kept
                assert bool(result.edge_mask[i, j]) == expected, (i, j)

    def test_a_negative_edge_is_never_gated_by_the_positive_cutoff(self, pct_matrix):
        # (1, 2) = -0.8 must be evaluated only against the negative
        # population, never accidentally pass because the positive
        # cutoff is lax -- negative_value=100.0 with the default strict
        # ">" comparison means the negative side can never pass (the
        # best possible percentile, 100.0, still isn't > 100.0).
        result = t.PositiveNegativePercentileThreshold(
            value_positive=0.0, value_negative=100.0
        ).apply(pct_matrix)
        assert not result.edge_mask[1, 2]


@pytest.mark.parametrize(
    "method,params",
    [
        ("weighted_average", dict(value=0.2)),
        ("positive_negative_value", dict(positive_value=0.3, negative_value=-0.3)),
        (
            "positive_negative_percentile_value",
            dict(value_positive=80.0, value_negative=80.0),
        ),
    ],
)
def test_structural_invariants_hold_for_every_method(signed_matrix, method, params):
    result = t.apply_threshold(signed_matrix, method, **params)
    n = signed_matrix.shape[0]

    assert result.node_mask.shape == (n,)
    assert result.edge_mask.shape == (n, n)
    assert np.array_equal(result.edge_mask, result.edge_mask.T), "must be symmetric"
    assert not result.edge_mask.diagonal().any(), "no self-edges"
    assert not (result.edge_mask & (signed_matrix == 0)).any(), (
        "must never keep a nonexistent (zero-weight) edge"
    )
