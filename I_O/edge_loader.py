import ast
import re
from pathlib import Path

import pandas as pd


def parse_edge(item):
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


def load_edge_list_matrix_csv(path):
    """
    Load an edge-list connectivity table from CSV or Excel.

    Parameters
    ----------
    path : str | pathlib.Path
        Path to an edge-list file.

        Expected file structure:

        - Row 0 contains edge definitions, for example:
          "(1,2)", "(1,3)", "(2,3)", ...
        - Rows 1 onward contain edge values.
        - Non-edge columns in the first row, such as subject IDs,
          are ignored automatically.

        Supported formats:

        - .csv
        - .xls
        - .xlsx

    Returns
    -------
    edge_index : list[tuple[int, int]]
        List of ROI pairs defining the edges. ROI indices are expected
        to be 1-based.

    data : np.ndarray
        Numeric edge-value matrix with shape:

        - (n_subjects, n_edges), if multiple rows are present
        - (1, n_edges), if a single data row is present

    Raises
    ------
    FileNotFoundError
        If the supplied file does not exist.

    ValueError
        If the file type is unsupported or no valid edge definitions
        are found in the first row.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path, header=0, encoding="utf-8-sig", low_memory=False)

        try:
            edge_index = [parse_edge(col) for col in df.columns[1:]]
            edge_values = df.iloc[:, 1:].astype(float).to_numpy()
            return edge_index, edge_values

        except ValueError:
            df = pd.read_csv(path, header=None, encoding="utf-8-sig", low_memory=False)

            n_edge_cols = df.shape[1] - 1

            edge_index = infer_edge_index_from_n_cols(n_edge_cols)
            edge_values = df.iloc[:, 1:].astype(float).to_numpy()

            return edge_index, edge_values

    elif suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path, header=None)

    else:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            "Supported formats are: .csv, .xls, .xlsx"
        )

    edge_index = []
    valid_cols = []

    for col, item in enumerate(df.iloc[0].values):
        if pd.isna(item):
            continue

        try:
            edge = parse_edge(item)

        except ValueError:
            continue

        edge_index.append(edge)
        valid_cols.append(col)

    if len(edge_index) == 0:
        raise ValueError("No edge definitions found in the first row.")

    data = df.iloc[1:, valid_cols].to_numpy(dtype=float)

    return edge_index, data


def infer_edge_index_from_n_cols(n_edge_cols):
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
