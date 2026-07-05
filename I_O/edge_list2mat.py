import numpy as np


def edge_list_to_matrix(edge_values, edge_index, subject_idx=0):
    """
    Convert edge-list representation to a symmetric connectivity matrix.

    Parameters
    ----------
    edge_values : np.ndarray
        Shape:
        - (n_edges,) single subject
        - (n_subjects, n_edges) → only first subject is used

    edge_index : list[tuple[int, int]]
        List of (i, j) ROI pairs (1-based indexing)

    Returns
    -------
    np.ndarray
        (n_nodes, n_nodes) connectivity matrix
    """

    edge_values = np.asarray(edge_values)

    # If multiple subjects, take only first
    if edge_values.ndim == 2:
        edge_values = edge_values[subject_idx]

    if edge_values.ndim != 1:
        raise ValueError(f"Expected 1D edge values, got shape {edge_values.shape}")

    # ---- infer number of nodes from edge index ----
    max_node = max(max(i, j) for i, j in edge_index)
    n_nodes = max_node

    mat = np.zeros((n_nodes, n_nodes))

    for val, (i, j) in zip(edge_values, edge_index):
        mat[i - 1, j - 1] = val
        mat[j - 1, i - 1] = val  # symmetric

    return mat
