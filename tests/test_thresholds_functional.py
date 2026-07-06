"""Tests for the functional core of Thresholds/thresholds.py: pure,
stateless metric functions with no knowledge of "thresholds"."""

import numpy as np
import pytest

from Thresholds import thresholds as t


class TestNodeConnectionCounts:
    def test_counts_ignore_diagonal_and_zeros(self):
        mat = np.array(
            [
                [5.0, 0.0, 1.0],
                [0.0, 3.0, 0.0],
                [1.0, 0.0, 9.0],
            ]
        )
        assert t.node_connection_counts(mat).tolist() == [1, 0, 1]

    def test_nonzero_diagonal_input_never_counted(self):
        mat = np.array([[7.0, 0.0], [0.0, 7.0]])
        assert t.node_connection_counts(mat).tolist() == [0, 0]


class TestNodeStrength:
    def test_absolute_sums_magnitudes(self):
        mat = np.array(
            [
                [0.0, 0.5, -0.5],
                [0.5, 0.0, 0.0],
                [-0.5, 0.0, 0.0],
            ]
        )
        assert t.node_strength(mat, absolute=True).tolist() == [1.0, 0.5, 0.5]

    def test_signed_lets_positive_and_negative_cancel(self):
        mat = np.array(
            [
                [0.0, 0.5, -0.5],
                [0.5, 0.0, 0.0],
                [-0.5, 0.0, 0.0],
            ]
        )
        assert t.node_strength(mat, absolute=False).tolist() == [0.0, 0.5, -0.5]


class TestNodeAverageStrength:
    def test_average_is_strength_over_count(self, hub_matrix):
        avg = t.node_average_strength(hub_matrix)
        expected = [(0.9 + 0.8) / 2, (0.9 + 0.05) / 2, (0.8 + 0.05) / 2, 0.0]
        assert avg == pytest.approx(expected)

    def test_isolated_node_is_zero_not_nan(self):
        mat = np.zeros((3, 3))
        avg = t.node_average_strength(mat)
        assert not np.isnan(avg).any()
        assert avg.tolist() == [0.0, 0.0, 0.0]


class TestEdgeStrength:
    def test_absolute_and_signed(self):
        mat = np.array([[0.0, -0.4], [-0.4, 0.0]])
        assert t.edge_strength(mat, absolute=True)[0, 1] == pytest.approx(0.4)
        assert t.edge_strength(mat, absolute=False)[0, 1] == pytest.approx(-0.4)

    def test_diagonal_always_zeroed_even_if_input_nonzero(self):
        mat = np.array([[3.0, 0.2], [0.2, 3.0]])
        out = t.edge_strength(mat)
        assert out[0, 0] == 0.0
        assert out[1, 1] == 0.0


class TestPercentileRank:
    def test_known_values_average_rank_method(self):
        values = [10, 30, 20, 40]  # ranks: 10->1, 20->2, 30->3, 40->4
        pct = t.percentile_rank(values)
        assert pct.tolist() == pytest.approx([0.0, 200 / 3, 100 / 3, 100.0])

    def test_ties_share_average_rank(self):
        values = [1, 1, 2]  # the two 1's tie for ranks 1,2 -> average rank 1.5
        pct = t.percentile_rank(values)
        assert pct[0] == pytest.approx(pct[1])
        assert pct[2] > pct[0]

    def test_single_value_population_is_zero_not_nan(self):
        assert t.percentile_rank([5.0]).tolist() == [0.0]

    def test_empty_population_is_empty(self):
        assert t.percentile_rank([]).tolist() == []


class TestEdgePositiveNegativePercentileRank:
    def test_positive_percentiles_match_hand_computation(self, pct_matrix):
        pos = t.edge_positive_percentile_rank(pct_matrix)
        assert pos[0, 1] == pytest.approx(100.0)  # 0.9 is the max positive
        assert pos[0, 2] == pytest.approx(200 / 3)  # 0.5
        assert pos[0, 3] == pytest.approx(0.0)  # 0.1 is the min positive
        assert pos[2, 3] == pytest.approx(100 / 3)  # 0.3

    def test_negative_percentiles_match_hand_computation(self, pct_matrix):
        neg = t.edge_negative_percentile_rank(pct_matrix)
        assert neg[1, 2] == pytest.approx(100.0)  # |-0.8| is the max magnitude
        assert neg[1, 3] == pytest.approx(0.0)  # |-0.2| is the min magnitude

    def test_non_matching_sign_and_diagonal_are_sentinel(self, pct_matrix):
        pos = t.edge_positive_percentile_rank(pct_matrix)
        neg = t.edge_negative_percentile_rank(pct_matrix)
        # negative edges must never get a positive-side percentile, and vice versa
        assert pos[1, 2] == -1.0 and pos[1, 3] == -1.0
        assert neg[0, 1] == -1.0 and neg[0, 2] == -1.0 and neg[0, 3] == -1.0
        assert np.all(np.diagonal(pos) == -1.0)
        assert np.all(np.diagonal(neg) == -1.0)

    def test_symmetric(self, pct_matrix):
        pos = t.edge_positive_percentile_rank(pct_matrix)
        neg = t.edge_negative_percentile_rank(pct_matrix)
        assert np.array_equal(pos, pos.T)
        assert np.array_equal(neg, neg.T)

    def test_population_excludes_opposite_sign_not_just_clips_it(self):
        # A matrix with a huge number of zero/near-zero entries must not
        # dilute the positive population -- only the two real positive
        # edges should be ranked against each other.
        mat = np.zeros((5, 5))
        mat[0, 1] = mat[1, 0] = 0.9
        mat[0, 2] = mat[2, 0] = 0.1
        pos = t.edge_positive_percentile_rank(mat)
        assert pos[0, 1] == pytest.approx(100.0)
        assert pos[0, 2] == pytest.approx(0.0)
        # every zero entry (no edge) must stay at the sentinel, not join
        # the positive population as a "weak" positive edge
        assert pos[3, 4] == -1.0
