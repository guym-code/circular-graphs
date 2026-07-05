from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

labels_dict = {
    "Schaefer 100": Path("Atlases\\labels_scf_100.csv"),
    "Schaefer 400": Path("Atlases\\labels_scf_400.csv"),
    "Schaefer 600": Path("Atlases\\labels_scf_600.csv"),
    "Schaefer 1000": Path("Atlases\\labels_scf_1000.csv"),
    "Multi-Modal Parcellation (MMP)": Path("Atlases\\MMP_labels.csv"),
    }

secondary_labels_dict = {
    "Schaefer 100": Path("Atlases\\secondary_labels\\schaefer_100_yeo7_network_labels.csv"),
    "Schaefer 400": Path("Atlases\\secondary_labels\\schaefer_400_yeo7_network_labels.csv"),
    "Schaefer 600": Path("Atlases\\secondary_labels\\schaefer_600_yeo7_network_labels.csv"),
    "Schaefer 1000": Path("Atlases\\secondary_labels\\schaefer_1000_yeo7_network_labels.csv"),
    }

def load_matrix(matrix, variable=None):
    """
    Load a connectivity matrix.

    Parameters
    ----------
    matrix : str | pathlib.Path | np.ndarray
        Either:
        - a NumPy array
        - path to a .csv, .xls, .xlsx, .mat or .npy file

    variable : str, optional
        Variable name to load from a MATLAB (.mat) file.

    Returns
    -------
    np.ndarray
        Connectivity matrix.
    """

    # Already a NumPy array
    if isinstance(matrix, np.ndarray):
        return matrix

    path = Path(matrix)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path, header=None).to_numpy()

    elif suffix in (".xls", ".xlsx"):
        return pd.read_excel(path, header=None).to_numpy()

    elif suffix == ".npy":
        return np.load(path)

    elif suffix == ".mat":
        data = loadmat(path)

        # Ignore MATLAB metadata
        variables = {
            k: v for k, v in data.items()
            if not k.startswith("__")
        }

        if variable is not None:
            if variable not in variables:
                raise ValueError(
                    f"Variable '{variable}' not found. "
                    f"Available variables: {list(variables.keys())}"
                )
            return variables[variable]

        matrices = {
            k: v
            for k, v in variables.items()
            if isinstance(v, np.ndarray) and v.ndim == 2
        }

        if len(matrices) == 0:
            raise ValueError("No 2D matrix found in .mat file.")

        if len(matrices) > 1:
            raise ValueError(
                "Multiple matrices found in .mat file. "
                f"Specify one using the 'variable' argument.\n"
                f"Available matrices: {list(matrices.keys())}"
            )

        return next(iter(matrices.values()))

    raise ValueError(
        f"Unsupported file type '{suffix}'. "
        "Supported formats are: .csv, .xls, .xlsx, .mat, .npy"
    )

def load_labels(obj):
    """
    Load ROI labels.

    Parameters
    ----------
    obj : None | list | tuple | np.ndarray | str | pathlib.Path
        Either:
        - None
        - a list/array of labels
        - path to a .csv, .txt, .tsv, .xls, .xlsx, .mat or .npy file

    Returns
    -------
    list[str] | None
        ROI labels, or None if obj is None.
    """

    if obj is None:
        return None
    
    if isinstance(obj, str) and obj in labels_dict:
        obj = labels_dict[obj]

    if isinstance(obj, (list, tuple, np.ndarray)):
        arr = np.asarray(obj).squeeze()
        return arr.astype(str).tolist()

    path = Path(obj)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path, header=None)
        labels = df.iloc[:, -1]

    elif suffix == ".tsv":
        df = pd.read_csv(path, sep="\t", header=None)
        labels = df.iloc[:, -1]

    elif suffix == ".txt":
        df = pd.read_csv(path, sep=None, engine="python", header=None)
        labels = df.iloc[:, -1]

    elif suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path, header=None)
        labels = df.iloc[:, -1]

    elif suffix == ".npy":
        arr = np.load(path, allow_pickle=True).squeeze()
        return arr.astype(str).tolist()

    elif suffix == ".mat":
        data = loadmat(path)

        variables = {
            k: v for k, v in data.items()
            if not k.startswith("__")
        }

        label_arrays = {
            k: v
            for k, v in variables.items()
            if isinstance(v, np.ndarray)
        }

        if len(label_arrays) == 0:
            raise ValueError("No label array found in .mat file.")

        if len(label_arrays) > 1:
            raise ValueError(
                "Multiple arrays found in .mat file. "
                "Please load the desired variable manually or save labels separately.\n"
                f"Available arrays: {list(label_arrays.keys())}"
            )

        arr = next(iter(label_arrays.values())).squeeze()
        return arr.astype(str).tolist()

    else:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            "Supported formats are: .csv, .tsv, .txt, .xls, .xlsx, .mat, .npy"
        )

    return labels.astype(str).tolist()


def load_secondary_labels(obj):
    """
    Load secondary ROI labels, such as network, hemisphere, module,
    or any other grouping variable.

    Same behavior as load_labels.
    """

    if isinstance(obj, str) and obj in secondary_labels_dict:
        obj = secondary_labels_dict[obj]

    return load_labels(obj)

def load_color_palette(obj):
    """
    Load a color palette mapping.

    Parameters
    ----------
    obj : None | dict | str | pathlib.Path

        Either:
        - None
        - dictionary {group: color}
        - path to a .csv, .txt, .tsv, .xls or .xlsx file

    Expected file format
    --------------------
    First row may optionally contain headers.

    Example:

        Network,Color
        Visual,#A450AE
        Somatomotor,#779AC0
        ...

    Returns
    -------
    dict[str, str] | None
    """

    if obj is None:
        return None

    if isinstance(obj, dict):
        return obj

    path = Path(obj)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path, header=None)

    elif suffix == ".tsv":
        df = pd.read_csv(path, sep="\t", header=None)

    elif suffix == ".txt":
        df = pd.read_csv(path, sep=None, engine="python", header=None)

    elif suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path, header=None)

    else:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            "Supported formats are: .csv, .tsv, .txt, .xls, .xlsx"
        )

    # Remove title row:
    df = df.iloc[1:].reset_index(drop=True)

    if df.shape[1] < 2:
        raise ValueError("Color palette file must contain at least two columns.")

    palette = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))

    return palette
