"""Shared fixtures for the Thresholds test suite."""

import numpy as np
import pytest


@pytest.fixture
def hub_matrix() -> np.ndarray:
    """4-node graph: node 0 is a strong hub; node 3 is fully isolated.

    Hand-verified average-strength metric: [0.85, 0.475, 0.425, 0.0]
    (node 0 is the only one above a 0.5 cutoff).
    """
    return np.array(
        [
            [0.0, 0.9, 0.8, 0.0],
            [0.9, 0.0, 0.05, 0.0],
            [0.8, 0.05, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ]
    )


@pytest.fixture
def pct_matrix() -> np.ndarray:
    """4-node signed matrix with distinct edge weights, chosen so each
    edge's percentile rank (within its own sign's population) is a
    clean, hand-computable number:

    Positive population {0.1, 0.3, 0.5, 0.9} -> percentiles {0, 33.33, 66.67, 100}
    Negative population (by magnitude) {0.2, 0.8} -> percentiles {0, 100}
    """
    return np.array(
        [
            [0.0, 0.9, 0.5, 0.1],
            [0.9, 0.0, -0.8, -0.2],
            [0.5, -0.8, 0.0, 0.3],
            [0.1, -0.2, 0.3, 0.0],
        ]
    )


@pytest.fixture
def signed_matrix() -> np.ndarray:
    """6-node symmetric, signed, fairly dense matrix for generic
    cross-method structural invariant checks."""
    mat = np.array(
        [
            [0.0, 0.9, -0.7, 0.2, 0.05, -0.3],
            [0.9, 0.0, 0.4, -0.6, 0.1, 0.5],
            [-0.7, 0.4, 0.0, 0.15, 0.8, -0.2],
            [0.2, -0.6, 0.15, 0.0, 0.3, 0.05],
            [0.05, 0.1, 0.8, 0.3, 0.0, -0.9],
            [-0.3, 0.5, -0.2, 0.05, -0.9, 0.0],
        ]
    )
    assert np.array_equal(mat, mat.T)
    return mat
