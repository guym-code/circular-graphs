"""Tests for the procedural entry points: apply_threshold,
filter_graph_by_mask, apply_and_filter."""

import numpy as np
import pytest

from Thresholds import thresholds as t


class TestApplyThreshold:
    def test_unknown_method_raises(self, pct_matrix):
        with pytest.raises(ValueError, match="Unknown threshold method"):
            t.apply_threshold(pct_matrix, "not_a_real_method")

    def test_unknown_param_raises_with_method_name_in_message(self, pct_matrix):
        with pytest.raises(ValueError, match="weighted_average"):
            t.apply_threshold(pct_matrix, "weighted_average", positive_value=0.3)

    def test_matches_calling_the_strategy_class_directly(self, pct_matrix):
        via_procedural = t.apply_threshold(
            pct_matrix, "positive_negative_value", positive_value=0.4, negative_value=-0.5
        )
        via_class = t.PositiveNegativeValueThreshold(
            positive_value=0.4, negative_value=-0.5
        ).apply(pct_matrix)
        assert np.array_equal(via_procedural.edge_mask, via_class.edge_mask)
        assert np.array_equal(via_procedural.node_mask, via_class.node_mask)

    def test_non_square_matrix_raises(self):
        with pytest.raises(ValueError, match="square"):
            t.apply_threshold(np.zeros((3, 4)), "positive_negative_value")


class TestFilterGraphByMask:
    def test_drops_and_renumbers_nodes_in_relative_order(self):
        mat = np.arange(16, dtype=float).reshape(4, 4)
        np.fill_diagonal(mat, 0.0)
        node_mask = [True, False, True, True]  # drop index 1
        labels = {0: "A", 1: "B", 2: "C", 3: "D"}
        secondary = {0: "g1", 1: "g2", 2: "g1", 3: "g3"}

        filtered_mat, filtered_labels, filtered_secondary = t.filter_graph_by_mask(
            mat, node_mask, labels_dict=labels, secondary_labels=secondary
        )

        assert filtered_mat.shape == (3, 3)
        assert np.array_equal(filtered_mat, mat[np.ix_([0, 2, 3], [0, 2, 3])])
        assert filtered_labels == {0: "A", 1: "C", 2: "D"}
        assert filtered_secondary == {0: "g1", 1: "g1", 2: "g3"}

    def test_edge_mask_zeroes_edges_before_node_dropping(self):
        mat = np.array(
            [
                [0.0, 1.0, 2.0],
                [1.0, 0.0, 3.0],
                [2.0, 3.0, 0.0],
            ]
        )
        edge_mask = np.array(
            [
                [False, False, True],
                [False, False, True],
                [True, True, False],
            ]
        )
        filtered_mat, _, _ = t.filter_graph_by_mask(
            mat, node_mask=[True, True, True], edge_mask=edge_mask
        )
        assert filtered_mat[0, 1] == 0.0  # zeroed by edge_mask
        assert filtered_mat[0, 2] == 2.0  # kept
        assert filtered_mat[1, 2] == 3.0  # kept

    def test_mismatched_edge_mask_shape_raises(self):
        mat = np.zeros((3, 3))
        with pytest.raises(ValueError, match="edge_mask shape"):
            t.filter_graph_by_mask(mat, [True, True, True], edge_mask=np.zeros((2, 2)))

    def test_mismatched_node_mask_length_raises(self):
        mat = np.zeros((3, 3))
        with pytest.raises(ValueError, match="node_mask length"):
            t.filter_graph_by_mask(mat, [True, True])

    def test_all_true_node_mask_keeps_everything(self, pct_matrix):
        filtered_mat, _, _ = t.filter_graph_by_mask(
            pct_matrix, node_mask=np.ones(4, dtype=bool)
        )
        assert filtered_mat.shape == pct_matrix.shape
        assert np.array_equal(filtered_mat, pct_matrix)


class TestApplyAndFilter:
    def test_default_keeps_every_node_only_zeroes_edges(self, pct_matrix):
        filtered_mat, _, _, result = t.apply_and_filter(
            pct_matrix,
            "positive_negative_value",
            positive_value=0.4,
            negative_value=-0.5,
        )
        assert filtered_mat.shape == pct_matrix.shape
        assert np.count_nonzero(filtered_mat) == np.count_nonzero(result.edge_mask)

    def test_drop_isolated_nodes_shrinks_the_graph(self, pct_matrix):
        filtered_mat, _, _, _ = t.apply_and_filter(
            pct_matrix,
            "positive_negative_value",
            positive_value=0.4,
            negative_value=-0.5,
            drop_isolated_nodes=True,
        )
        assert filtered_mat.shape == (3, 3)  # node 3 is isolated at this cutoff

    def test_weighted_average_respects_the_same_flag(self, hub_matrix):
        kept_shape, _, _, _ = t.apply_and_filter(
            hub_matrix, "weighted_average", value=0.5
        )
        dropped_shape, _, _, _ = t.apply_and_filter(
            hub_matrix, "weighted_average", value=0.5, drop_isolated_nodes=True
        )
        assert kept_shape.shape == (4, 4)
        assert dropped_shape.shape == (3, 3)

    def test_result_reflects_the_original_unfiltered_matrix(self, hub_matrix):
        _, _, _, result = t.apply_and_filter(
            hub_matrix, "weighted_average", value=0.5, drop_isolated_nodes=True
        )
        # result indices must still line up with the *original* 4-node
        # matrix, not the filtered 3-node one
        assert result.node_mask.shape == (4,)
        assert result.edge_mask.shape == (4, 4)
