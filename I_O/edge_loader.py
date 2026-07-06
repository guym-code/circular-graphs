import ast
import re
from pathlib import Path

import numpy as np
import pandas as pd


def parse_edge(item: object) -> tuple[int, int]:
    """
    Parse a single edge definition into a pair of ROI indices.

    Parameters
    ----------
    item : object
        Edge definition read from a file header. Supported examples include:

        - "(1,2)"
        - "1,2"
        - "1-2"
        - "1_2"

        The function assumes 1-based ROI indices, because this is the
        common convention in atlas files and edge-list tables.

    Returns
    -------
    tuple[int, int]
        Pair of ROI indices defining one edge.

    Raises
    ------
    ValueError
        If the item cannot be interpreted as an edge definition.
    """

    item = str(item).strip()

    try:
        parsed = ast.literal_eval(item)

        if (
            isinstance(parsed, tuple)
            and len(parsed) == 2
            and all(isinstance(value, int) for value in parsed)
        ):
            return parsed

    except (ValueError, SyntaxError):
        pass

    match = re.search(r"(\d+)\D+(\d+)", item)

    if match:
        return int(match.group(1)), int(match.group(2))

    raise ValueError(f"Could not parse edge definition: {item!r}")

def load_edge_list(
    data: np.ndarray | str | Path,
) -> tuple[list[tuple[int, int]], np.ndarray]:
    """
    Load an edge-list representation.

    Parameters
    ----------
    data : np.ndarray | str | pathlib.Path
        One of:

        - a NumPy array,
        - a path to a .csv, .xls, .xlsx, .mat or .npy file.

    Returns
    -------
    edge_index : list[tuple[int, int]]
        List of ROI pairs.

    edge_values : np.ndarray
        Edge values with shape (n_subjects, n_edges).

    Raises
    ------
    FileNotFoundError
        If the supplied file does not exist.

    ValueError
        If the input type or file format is unsupported.
    """

    # ------- already loaded edges list -------
    if isinstance(data, np.ndarray):
        edge_values = np.asarray(data, dtype=float)

        if edge_values.ndim == 1:
            edge_values = edge_values[np.newaxis, :]

        edge_index = infer_edge_index_from_n_cols(edge_values.shape[1])
        return edge_index, edge_values


    # ------------ Path to file ------------
    path = Path(data)

    if not path.exists():
        raise FileNotFoundError(path)

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path, header=0, encoding="utf-8-sig", low_memory=False)
        return dataframe_to_edge_list(df, path)

    if suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path, header=0)
        return dataframe_to_edge_list(df, path)

    if suffix == ".npy":
        arr = np.load(path)
        edge_index = infer_edge_index_from_n_cols(arr.shape[1] - 1)
        edge_values = arr[:, 1:].astype(float)
        return edge_index, edge_values

    if suffix == ".mat":
        raise NotImplementedError(".mat loading not implemented yet")

    raise ValueError(f"Unsupported file type: {suffix}")

def dataframe_to_edge_list(
    df: pd.DataFrame,
    path: str | Path | None = None,
) -> tuple[list[tuple[int, int]], np.ndarray]:
    """
    Convert a dataframe into edge_index and edge_values.

    Accepts either

    1. edge names in the header
    2. no edge names (infers from number of columns)
    """

    try:
        edge_index = [parse_edge(col) for col in df.columns[1:]]
        edge_values = df.iloc[:, 1:].astype(float).to_numpy()
        return edge_index, edge_values

    except ValueError:
        pass

    # Reload without header if we came from a file
    if path is not None:
        suffix = path.suffix.lower()

        if suffix == ".csv":
            df = pd.read_csv(
                path,
                header=None,
                encoding="utf-8-sig",
                low_memory=False,
            )

        else:
            df = pd.read_excel(path, header=None)

    n_edge_cols = df.shape[1] - 1

    edge_index = infer_edge_index_from_n_cols(n_edge_cols)
    edge_values = df.iloc[:, 1:].astype(float).to_numpy()

    return edge_index, edge_values

def infer_edge_index_from_n_cols(
    n_edge_cols: int,
) -> list[tuple[int, int]]:
    """
    Infer edge indices from the number of edge columns.

    Supports either:

    - full square matrix: n_nodes * n_nodes columns
    - upper triangle without diagonal: n_nodes * (n_nodes - 1) / 2 columns

    Returns
    -------
    list[tuple[int, int]]
        Inferred 1-based ROI edge indices.
    """

    # Full matrix: n * n
    n_full = int(n_edge_cols ** 0.5)

    if n_full * n_full == n_edge_cols:
        return [
            (i, j)
            for i in range(1, n_full + 1)
            for j in range(1, n_full + 1)
        ]

    # Upper triangle without diagonal: n * (n - 1) / 2
    n_tri = int((1 + (1 + 8 * n_edge_cols) ** 0.5) / 2)

    if n_tri * (n_tri - 1) // 2 == n_edge_cols:
        return [
            (i, j)
            for i in range(1, n_tri + 1)
            for j in range(i + 1, n_tri + 1)
        ]

    raise ValueError(
        f"Could not infer edge structure from {n_edge_cols} edge columns. "
        "Expected either n*n columns for a full matrix or "
        "n*(n-1)/2 columns for a triangular matrix."
    )
