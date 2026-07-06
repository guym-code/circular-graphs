import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from I_O.edge_loader import (
    parse_edge,
    load_edge_list,
    dataframe_to_edge_list,
    infer_edge_index_from_n_cols,
)

from I_O.edge_list2mat import edge_list_to_matrix
from I_O.loader import (
    load_matrix,
    load_labels,
    load_secondary_labels,
    load_color_palette,
)
from CircularGraph import CircularGraph


# -------------------------
# parse_edge
# -------------------------

@pytest.mark.parametrize(
    "edge_string, expected",
    [
        ("(1,2)", (1, 2)),
        ("1,2", (1, 2)),
        ("1-2", (1, 2)),
        ("1_2", (1, 2)),
        ("  (3, 7)  ", (3, 7)),
    ],
)
def test_parse_edge_valid_formats(edge_string, expected):
    assert parse_edge(edge_string) == expected


@pytest.mark.parametrize(
    "bad_edge",
    [
        "abc",
        "(1,)",
        "(1, 2, 3)",
        "",
        None,
    ],
)
def test_parse_edge_invalid_formats_raise(bad_edge):
    with pytest.raises(ValueError):
        parse_edge(bad_edge)


# -------------------------
# infer_edge_index_from_n_cols
# -------------------------

def test_infer_edge_index_full_matrix():
    edge_index = infer_edge_index_from_n_cols(9)

    assert len(edge_index) == 9
    assert edge_index[0] == (1, 1)
    assert edge_index[-1] == (3, 3)


def test_infer_edge_index_upper_triangle():
    edge_index = infer_edge_index_from_n_cols(6)

    assert edge_index == [
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 3),
        (2, 4),
        (3, 4),
    ]


def test_infer_edge_index_invalid_number_of_columns_raises():
    with pytest.raises(ValueError):
        infer_edge_index_from_n_cols(5)

# -------------------------
# edge_list_to_matrix
# -------------------------

def test_edge_list_to_matrix_from_upper_triangle():
    edge_index = [(1, 2), (1, 3), (2, 3)]
    edge_values = np.array([0.2, 0.5, -0.7])

    mat = edge_list_to_matrix(edge_values, edge_index)

    expected = np.array([
        [0.0,  0.2,  0.5],
        [0.2,  0.0, -0.7],
        [0.5, -0.7,  0.0],
    ])

    np.testing.assert_allclose(mat, expected)


def test_edge_list_to_matrix_selects_correct_subject():
    edge_index = [(1, 2), (1, 3), (2, 3)]
    edge_values = np.array([
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ])

    mat = edge_list_to_matrix(edge_values, edge_index, subject_idx=1)

    assert mat[0, 1] == 0.4
    assert mat[0, 2] == 0.5
    assert mat[1, 2] == 0.6


def test_edge_list_to_matrix_full_symmetric_valid():
    edge_index = [(1, 2), (2, 1)]
    edge_values = np.array([0.8, 0.8])

    mat = edge_list_to_matrix(edge_values, edge_index)

    assert mat[0, 1] == 0.8
    assert mat[1, 0] == 0.8


def test_edge_list_to_matrix_full_symmetric_inconsistent_raises():
    edge_index = [(1, 2), (2, 1)]
    edge_values = np.array([0.8, 0.3])

    with pytest.raises(ValueError):
        edge_list_to_matrix(edge_values, edge_index)


def test_edge_list_to_matrix_length_mismatch_raises():
    edge_index = [(1, 2), (1, 3)]
    edge_values = np.array([0.1])

    with pytest.raises(ValueError):
        edge_list_to_matrix(edge_values, edge_index)


# -------------------------
# load_edge_list from NumPy arrays
# -------------------------

def test_load_edge_list_numpy_1d_array():
    arr = np.array([0.1, 0.2, 0.3])

    edge_index, edge_values = load_edge_list(arr)

    assert edge_values.shape == (1, 3)
    assert edge_index == [(1, 2), (1, 3), (2, 3)]


def test_load_edge_list_numpy_2d_array():
    arr = np.array([
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ])

    edge_index, edge_values = load_edge_list(arr)

    assert edge_values.shape == (2, 3)
    assert edge_index == [(1, 2), (1, 3), (2, 3)]


def test_load_edge_list_numpy_bad_number_of_edges_raises():
    arr = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]])

    with pytest.raises(ValueError):
        load_edge_list(arr)


# -------------------------
# load_edge_list from CSV / Excel / NPY
# -------------------------

def test_load_edge_list_csv_with_edge_headers(tmp_path):
    path = tmp_path / "edge_list_valid_headers.csv"

    df = pd.DataFrame({
        "subject": ["sub01", "sub02"],
        "(1,2)": [0.1, 0.4],
        "(1,3)": [0.2, 0.5],
        "(2,3)": [0.3, 0.6],
    })
    df.to_csv(path, index=False)

    edge_index, edge_values = load_edge_list(path)

    assert edge_index == [(1, 2), (1, 3), (2, 3)]
    np.testing.assert_allclose(edge_values, [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])


def test_load_edge_list_csv_without_edge_headers(tmp_path):
    path = tmp_path / "edge_list_no_headers.csv"

    df = pd.DataFrame([
        ["sub01", 0.1, 0.2, 0.3],
        ["sub02", 0.4, 0.5, 0.6],
    ])
    df.to_csv(path, index=False, header=False)

    edge_index, edge_values = load_edge_list(path)

    assert edge_index == [(1, 2), (1, 3), (2, 3)]
    assert edge_values.shape == (2, 3)


def test_load_edge_list_excel_with_edge_headers(tmp_path):
    path = tmp_path / "edge_list_valid_headers.xlsx"

    df = pd.DataFrame({
        "subject": ["sub01"],
        "(1,2)": [0.1],
        "(1,3)": [0.2],
        "(2,3)": [0.3],
    })
    df.to_excel(path, index=False)

    edge_index, edge_values = load_edge_list(path)

    assert edge_index == [(1, 2), (1, 3), (2, 3)]
    assert edge_values.shape == (1, 3)


def test_load_edge_list_npy_valid(tmp_path):
    path = tmp_path / "edge_list_valid.npy"

    arr = np.array([
        [1, 0.1, 0.2, 0.3],
        [2, 0.4, 0.5, 0.6],
    ])
    np.save(path, arr)

    edge_index, edge_values = load_edge_list(path)

    assert edge_index == [(1, 2), (1, 3), (2, 3)]
    assert edge_values.shape == (2, 3)


def test_load_edge_list_missing_file_raises(tmp_path):
    path = tmp_path / "missing_edge_list.csv"

    with pytest.raises(FileNotFoundError):
        load_edge_list(path)


def test_load_edge_list_unsupported_file_type_raises(tmp_path):
    path = tmp_path / "edge_list_invalid.json"
    path.write_text("{}")

    with pytest.raises(ValueError):
        load_edge_list(path)


def test_load_edge_list_mat_not_implemented_raises(tmp_path):
    path = tmp_path / "edge_list_not_implemented.mat"
    path.write_bytes(b"fake mat content")

    with pytest.raises(NotImplementedError):
        load_edge_list(path)


# -------------------------
# load_matrix
# -------------------------

def test_load_matrix_numpy_array_sets_diagonal_to_zero():
    mat = np.array([
        [1.0, 0.2],
        [0.2, 1.0],
    ])

    loaded = load_matrix(mat)

    np.testing.assert_allclose(loaded, [[0.0, 0.2], [0.2, 0.0]])


def test_load_matrix_csv(tmp_path):
    path = tmp_path / "matrix_valid.csv"

    pd.DataFrame([
        [1.0, 0.2, 0.3],
        [0.2, 1.0, 0.4],
        [0.3, 0.4, 1.0],
    ]).to_csv(path, header=False, index=False)

    mat = load_matrix(path)

    assert mat.shape == (3, 3)
    np.testing.assert_allclose(np.diag(mat), [0.0, 0.0, 0.0])


def test_load_matrix_npy(tmp_path):
    path = tmp_path / "matrix_valid.npy"

    arr = np.array([
        [1.0, 0.2],
        [0.2, 1.0],
    ])
    np.save(path, arr)

    mat = load_matrix(path)

    assert mat.shape == (2, 2)
    assert mat[0, 0] == 0.0


def test_load_matrix_non_numeric_csv_raises(tmp_path):
    path = tmp_path / "matrix_non_numeric.csv"

    pd.DataFrame([
        ["a", "b"],
        ["c", "d"],
    ]).to_csv(path, header=False, index=False)

    with pytest.raises(ValueError):
        load_matrix(path)


def test_load_matrix_missing_file_raises(tmp_path):
    path = tmp_path / "missing_matrix.csv"

    with pytest.raises(FileNotFoundError):
        load_matrix(path)


def test_load_matrix_unsupported_file_type_raises(tmp_path):
    path = tmp_path / "matrix_invalid.json"
    path.write_text("{}")

    with pytest.raises(ValueError):
        load_matrix(path)


# -------------------------
# load_labels / load_secondary_labels
# -------------------------

def test_load_labels_none_returns_none():
    assert load_labels(None) is None


def test_load_labels_from_list():
    labels = load_labels(["ROI1", "ROI2", "ROI3"])

    assert labels == ["ROI1", "ROI2", "ROI3"]


def test_load_labels_from_numpy_array():
    labels = load_labels(np.array(["ROI1", "ROI2"]))

    assert labels == ["ROI1", "ROI2"]


def test_load_labels_csv_uses_final_column(tmp_path):
    path = tmp_path / "labels_valid.csv"

    pd.DataFrame([
        [1, "LH", "ROI1"],
        [2, "RH", "ROI2"],
    ]).to_csv(path, header=False, index=False)

    labels = load_labels(path)

    assert labels == ["ROI1", "ROI2"]


def test_load_secondary_labels_from_list():
    secondary = load_secondary_labels(["Visual", "Default"])

    assert secondary == ["Visual", "Default"]


def test_load_labels_missing_file_raises(tmp_path):
    path = tmp_path / "missing_labels.csv"

    with pytest.raises(FileNotFoundError):
        load_labels(path)


def test_load_labels_unsupported_file_type_raises(tmp_path):
    path = tmp_path / "labels_invalid.json"
    path.write_text("{}")

    with pytest.raises(ValueError):
        load_labels(path)


# -------------------------
# load_color_palette
# -------------------------

def test_load_color_palette_none_returns_none():
    assert load_color_palette(None) is None


def test_load_color_palette_dict_returns_dict():
    palette = {"Visual": "#FF0000"}

    assert load_color_palette(palette) == palette


def test_load_color_palette_csv(tmp_path):
    path = tmp_path / "color_palette_valid.csv"

    pd.DataFrame([
        ["network", "color"],
        ["Visual", "#FF0000"],
        ["Default", "#0000FF"],
    ]).to_csv(path, header=False, index=False)

    palette = load_color_palette(path)

    assert palette == {
        "Visual": "#FF0000",
        "Default": "#0000FF",
    }


def test_load_color_palette_too_few_columns_raises(tmp_path):
    path = tmp_path / "color_palette_one_column.csv"

    pd.DataFrame([
        ["network"],
        ["Visual"],
    ]).to_csv(path, header=False, index=False)

    with pytest.raises(ValueError):
        load_color_palette(path)


def test_load_color_palette_missing_file_raises(tmp_path):
    path = tmp_path / "missing_color_palette.csv"

    with pytest.raises(FileNotFoundError):
        load_color_palette(path)


def test_load_color_palette_unsupported_file_type_raises(tmp_path):
    path = tmp_path / "color_palette_invalid.json"
    path.write_text("{}")

    with pytest.raises(ValueError):
        load_color_palette(path)


# -------------------------
# CircularGraph integration tests
# -------------------------

def test_circular_graph_from_matrix_numpy_valid():
    mat = np.array([
        [0.0, 0.2, 0.3],
        [0.2, 0.0, 0.4],
        [0.3, 0.4, 0.0],
    ])

    g = CircularGraph(
        mat_path=mat,
        mat_type="matrix",
        labels=["ROI1", "ROI2", "ROI3"],
        secondary_labels=["Visual", "Visual", "Default"],
        color_palette={
            "Visual": "#FF0000",
            "Default": "#0000FF",
        },
    )

    assert g.mat.shape == (3, 3)
    assert g.mask.shape == (3, 3)
    assert g.mask.dtype == bool


def test_circular_graph_from_edge_list_csv_valid(tmp_path):
    path = tmp_path / "edge_list_valid.csv"

    pd.DataFrame({
        "subject": ["sub01"],
        "(1,2)": [0.1],
        "(1,3)": [0.2],
        "(2,3)": [0.3],
    }).to_csv(path, index=False)

    g = CircularGraph(
        mat_path=path,
        mat_type="edge_list",
        labels=["ROI1", "ROI2", "ROI3"],
    )

    assert g.mat.shape == (3, 3)
    assert g.mat[0, 1] == 0.1


def test_circular_graph_invalid_mat_type_raises():
    with pytest.raises(ValueError):
        CircularGraph(np.eye(3), mat_type="bad_type")


def test_circular_graph_non_square_matrix_raises():
    mat = np.ones((2, 3))

    with pytest.raises(ValueError):
        CircularGraph(mat, mat_type="matrix")


def test_circular_graph_non_symmetric_matrix_raises():
    mat = np.array([
        [0.0, 0.1],
        [0.7, 0.0],
    ])

    with pytest.raises(ValueError):
        CircularGraph(mat, mat_type="matrix")


def test_circular_graph_matrix_with_nan_raises():
    mat = np.array([
        [0.0, np.nan],
        [np.nan, 0.0],
    ])

    with pytest.raises(ValueError):
        CircularGraph(mat, mat_type="matrix")


def test_circular_graph_wrong_number_of_labels_raises():
    mat = np.eye(3)

    with pytest.raises(ValueError):
        CircularGraph(
            mat,
            mat_type="matrix",
            labels=["ROI1", "ROI2"],
        )


def test_circular_graph_wrong_number_of_secondary_labels_raises():
    mat = np.eye(3)

    with pytest.raises(ValueError):
        CircularGraph(
            mat,
            mat_type="matrix",
            secondary_labels=["Visual", "Default"],
        )


def test_circular_graph_palette_without_secondary_labels_raises():
    mat = np.eye(3)

    with pytest.raises(ValueError):
        CircularGraph(
            mat,
            mat_type="matrix",
            color_palette={"Visual": "#FF0000"},
        )


def test_circular_graph_invalid_color_format_raises():
    mat = np.eye(2)

    with pytest.raises(ValueError):
        CircularGraph(
            mat,
            mat_type="matrix",
            secondary_labels=["Visual", "Visual"],
            color_palette={"Visual": "red"},
        )


def test_circular_graph_palette_missing_group_raises():
    mat = np.eye(3)

    with pytest.raises(ValueError):
        CircularGraph(
            mat,
            mat_type="matrix",
            secondary_labels=["Visual", "Default", "Default"],
            color_palette={"Visual": "#FF0000"},
        )


def test_circular_graph_palette_extra_group_raises():
    mat = np.eye(3)

    with pytest.raises(ValueError):
        CircularGraph(
            mat,
            mat_type="matrix",
            secondary_labels=["Visual", "Visual", "Visual"],
            color_palette={
                "Visual": "#FF0000",
                "Default": "#0000FF",
            },
        )


# -------------------------
# Optional future tests
# -------------------------
# These tests depend on rules you may want to add.
# For example, if connectivity values must be in [-1, 1],
# these should raise errors once validation is implemented.
# -------------------------

def test_edge_list_larger_than_1_csv_raises(tmp_path):
    path = tmp_path / "edge_list_larger_than"
    "_1.csv"

    pd.DataFrame({
        "subject": ["sub01"],
        "(1,2)": [1.2],
        "(1,3)": [0.2],
        "(2,3)": [0.3],
    }).to_csv(path, index=False)

    with pytest.raises(ValueError):
        CircularGraph(path, mat_type="edge_list")


def test_matrix_values_smaller_than_minus_1_csv_raises(tmp_path):
    path = tmp_path / "matrix_smaller_than_minus_1.csv"

    pd.DataFrame([
        [0.0, -1.4],
        [-1.4, 0.0],
    ]).to_csv(path, header=False, index=False)

    with pytest.raises(ValueError):
        CircularGraph(path, mat_type="matrix")