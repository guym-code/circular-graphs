from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat


LABELS_DICT = {
    "Schaefer 100": Path("Atlases", "labels_scf_100.csv"),
    "Schaefer 400": Path("Atlases", "labels_scf_400.csv"),
    "Schaefer 600": Path("Atlases", "labels_scf_600.csv"),
    "Schaefer 1000": Path("Atlases", "labels_scf_1000.csv"),
    "Multi-Modal Parcellation (MMP)": Path("Atlases", "MMP_labels.csv"),
}

SECONDARY_LABELS_DICT = {
    "Schaefer 100": Path(
        "Atlases", "secondary_labels", "schaefer_100_yeo7_network_labels.csv"
    ),
    "Schaefer 400": Path(
        "Atlases", "secondary_labels", "schaefer_400_yeo7_network_labels.csv"
    ),
    "Schaefer 600": Path(
        "Atlases", "secondary_labels", "schaefer_600_yeo7_network_labels.csv"
    ),
    "Schaefer 1000": Path(
        "Atlases", "secondary_labels", "schaefer_1000_yeo7_network_labels.csv"
    ),
}

def load_matrix(matrix, variable=None):
    """
    Load a connectivity matrix.

    Parameters
    ----------
    matrix : str | pathlib.Path | np.ndarray
        Connectivity matrix supplied either as:

        - a NumPy array,
        - a path to a .csv, .xls, .xlsx, .mat or .npy file.

    variable : str, optional
        Variable name to load from a MATLAB (.mat) file.
        If omitted, the function attempts to automatically identify
        the unique 2D matrix stored in the file.

    Returns
    -------
    np.ndarray
        Square connectivity matrix.

    Raises
    ------
    FileNotFoundError
        If the supplied file does not exist.

    ValueError
        If the file format is unsupported, no valid matrix is found,
        or multiple candidate matrices exist in a MATLAB file.

    TypeError
        If the loaded object is not a numeric matrix.
    """

    if isinstance(matrix, np.ndarray):
        return matrix

    path = Path(matrix)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path, header=None).to_numpy()

    if suffix in (".xls", ".xlsx"):
        return pd.read_excel(path, header=None).to_numpy()

    if suffix == ".npy":
        return np.load(path)

    if suffix == ".mat":
        return _load_mat_matrix(path, variable)

    raise ValueError(
        f"Unsupported file type '{suffix}'. "
        "Supported formats are: .csv, .xls, .xlsx, .mat, .npy"
    )


def _load_mat_matrix(path, variable=None):
    """Load a 2D matrix from a MATLAB .mat file."""

    data = loadmat(path)
    variables = {
        key: value
        for key, value in data.items()
        if not key.startswith("__")
    }

    if variable is not None:
        if variable not in variables:
            raise ValueError(
                f"Variable '{variable}' not found. "
                f"Available variables: {list(variables.keys())}"
            )
        return variables[variable]

    matrices = {
        key: value
        for key, value in variables.items()
        if isinstance(value, np.ndarray) and value.ndim == 2
    }

    if len(matrices) == 0:
        raise ValueError("No 2D matrix found in .mat file.")

    if len(matrices) > 1:
        raise ValueError(
            "Multiple matrices found in .mat file. "
            "Specify one using the 'variable' argument.\n"
            f"Available matrices: {list(matrices.keys())}"
        )

    return next(iter(matrices.values()))


def load_labels(obj):
    """
    Load ROI labels.

    Parameters
    ----------
    obj : None | str | pathlib.Path | list | tuple | np.ndarray
        ROI labels supplied as one of:

        - None,
        - a list, tuple or NumPy array of labels,
        - a predefined atlas name (see LABELS_DICT),
        - a path to a .csv, .tsv, .txt, .xls, .xlsx,
          .mat or .npy file.

        For table-based files, labels are assumed to be stored
        in the final column.

    Returns
    -------
    list[str] | None
        Ordered ROI labels corresponding to the rows and columns
        of the connectivity matrix.

    Raises
    ------
    FileNotFoundError
        If the supplied file does not exist.

    ValueError
        If the file format is unsupported or labels cannot be
        uniquely identified.
    """

    if obj is None:
        return None

    if isinstance(obj, str) and obj in LABELS_DICT:
        obj = LABELS_DICT[obj]

    if isinstance(obj, (list, tuple, np.ndarray)):
        arr = np.asarray(obj).squeeze()
        return arr.astype(str).tolist()

    path = Path(obj)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix in (".csv", ".tsv", ".txt", ".xls", ".xlsx"):
        return _load_labels_table(path, suffix)

    if suffix == ".npy":
        arr = np.load(path, allow_pickle=True).squeeze()
        return arr.astype(str).tolist()

    if suffix == ".mat":
        return _load_mat_labels(path)

    raise ValueError(
        f"Unsupported file type '{suffix}'. "
        "Supported formats are: .csv, .tsv, .txt, .xls, .xlsx, .mat, .npy"
    )


def load_secondary_labels(obj):
    """
    Load secondary labels describing each ROI.

    Secondary labels define higher-level groupings of ROIs,
    such as functional networks, hemispheres, modules or any
    other categorical annotation.

    Parameters
    ----------
    obj : None | str | pathlib.Path | list | tuple | np.ndarray
        Secondary labels supplied as one of:

        - None,
        - a list, tuple or NumPy array,
        - a predefined atlas name (see SECONDARY_LABELS_DICT),
        - a path to a supported label file.

    Returns
    -------
    list[str] | None
        Ordered secondary labels aligned with the connectivity
        matrix.

    Notes
    -----
    This function behaves identically to ``load_labels()``,
    except that predefined atlas names are resolved using
    ``SECONDARY_LABELS_DICT``.
    """

    if obj is None:
        return None

    if isinstance(obj, str) and obj in SECONDARY_LABELS_DICT:
        obj = SECONDARY_LABELS_DICT[obj]

    return load_labels(obj)


def _load_labels_table(path, suffix):
    """Load labels from the final column of a table-like file."""

    if suffix == ".csv":
        df = pd.read_csv(path, header=None)
    elif suffix == ".tsv":
        df = pd.read_csv(path, sep="\t", header=None)
    elif suffix == ".txt":
        df = pd.read_csv(path, sep=None, engine="python", header=None)
    elif suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path, header=None)
    else:
        raise ValueError(f"Unsupported label table type: {suffix}")

    labels = df.iloc[:, -1]
    return labels.astype(str).tolist()


def _load_mat_labels(path):
    """Load labels from a MATLAB .mat file."""

    data = loadmat(path)
    variables = {
        key: value
        for key, value in data.items()
        if not key.startswith("__")
    }

    label_arrays = {
        key: value
        for key, value in variables.items()
        if isinstance(value, np.ndarray)
    }

    if len(label_arrays) == 0:
        raise ValueError("No label array found in .mat file.")

    if len(label_arrays) > 1:
        raise ValueError(
            "Multiple arrays found in .mat file. "
            "Please load the desired variable manually or save labels "
            "separately.\n"
            f"Available arrays: {list(label_arrays.keys())}"
        )

    arr = next(iter(label_arrays.values())).squeeze()
    return arr.astype(str).tolist()


def load_color_palette(obj):
    """
    Load a color palette.

    Parameters
    ----------
    obj : None | dict | str | pathlib.Path
        Color palette supplied as one of:

        - None,
        - a dictionary mapping group names to colors,
        - a path to a .csv, .tsv, .txt, .xls or .xlsx file.

        Table-based files must contain at least two columns:

        - column 1 : group name
        - column 2 : hexadecimal color (e.g. '#A450AE')

        The first row is assumed to contain column headers and
        is ignored.

    Returns
    -------
    dict[str, str] | None
        Dictionary mapping each group to its display color.

    Raises
    ------
    FileNotFoundError
        If the supplied file does not exist.

    ValueError
        If the file format is unsupported or the table contains
        fewer than two columns.
    """
    
    if obj is None:
        return None

    if isinstance(obj, dict):
        return obj

    path = Path(obj)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    df = _load_palette_table(path, suffix)

    # Remove title row.
    df = df.iloc[1:].reset_index(drop=True)

    if df.shape[1] < 2:
        raise ValueError("Color palette file must contain at least two columns.")

    return dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))


def _load_palette_table(path, suffix):
    """Load a color palette table from disk."""

    if suffix == ".csv":
        return pd.read_csv(path, header=None)

    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t", header=None)

    if suffix == ".txt":
        return pd.read_csv(path, sep=None, engine="python", header=None)

    if suffix in (".xls", ".xlsx"):
        return pd.read_excel(path, header=None)

    raise ValueError(
        f"Unsupported file type '{suffix}'. "
        "Supported formats are: .csv, .tsv, .txt, .xls, .xlsx"
    )
