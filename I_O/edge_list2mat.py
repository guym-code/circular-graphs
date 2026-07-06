import numpy as np


def edge_list_to_matrix(edge_values, edge_index, subject_idx=0):
    """
    Convert an edge-list representation to a symmetric connectivity matrix.

    The input edge list may represent either:

    - the upper (or lower) triangle of a symmetric matrix
    (e.g. (1,2), (1,3), (2,3), ...), or
    - the complete symmetric matrix
    (e.g. (1,2) and (2,1), including optional diagonal entries).

    When both (i,j) and (j,i) are present, their values must be identical;
    otherwise a ValueError is raised.

    Parameters
    ----------
    edge_values : np.ndarray
        Edge values with shape:

        - (n_edges,) for a single subject.
        - (n_subjects, n_edges) for multiple subjects. The subject specified
        by ``subject_idx`` is converted.

    edge_index : list[tuple[int, int]]
        List of ROI pairs (1-based indexing) corresponding to each edge value.

    subject_idx : int, default=0
        Subject index to convert when ``edge_values`` contains multiple
        subjects.

    Returns
    -------
    np.ndarray
        Symmetric connectivity matrix of shape (n_nodes, n_nodes).

    Raises
    ------
    ValueError
        If ``edge_values`` and ``edge_index`` have different lengths, the
        selected subject does not produce a one-dimensional edge vector, or
        a complete symmetric edge list contains inconsistent values for
        (i,j) and (j,i).
    """

    edge_values = np.asarray(edge_values)

    if edge_values.ndim == 2:
        edge_values = edge_values[subject_idx]

    if edge_values.ndim != 1:
        raise ValueError(f"Expected 1D edge values, got shape {edge_values.shape}")

    if len(edge_values) != len(edge_index):
        raise ValueError(
            f"edge_values length ({len(edge_values)}) does not match "
            f"edge_index length ({len(edge_index)})"
        )

    n_nodes = max(max(i, j) for i, j in edge_index)
    mat = np.zeros((n_nodes, n_nodes), dtype=float)

    seen = {}

    for val, (i, j) in zip(edge_values, edge_index):
        i0 = i - 1
        j0 = j - 1

        if i == j:
            mat[i0, j0] = val
            seen[(i, j)] = val
            continue

        reverse = (j, i)

        if reverse in seen:
            if not np.isclose(val, seen[reverse]):
                raise ValueError(
                    f"Full symmetric matrix contains inconsistent values: "
                    f"({i},{j})={val}, but ({j},{i})={seen[reverse]}"
                )
            continue

        mat[i0, j0] = val
        mat[j0, i0] = val
        seen[(i, j)] = val

    # Ignore self-connections for visualization
    np.fill_diagonal(mat, 0.0)

    return mat
