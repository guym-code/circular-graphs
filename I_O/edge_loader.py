import ast
import re
from pathlib import Path
import pandas as pd

def parse_edge(item):
    item = str(item).strip()

    # Expected: "(1,2)"
    try:
        parsed = ast.literal_eval(item)
        if (
            isinstance(parsed, tuple)
            and len(parsed) == 2
            and all(isinstance(x, int) for x in parsed)
        ):
            return parsed
    except Exception:
        pass

    # Alternative: "1,2" or "1-2" or "1_2"
    match = re.search(r"(\d+)\D+(\d+)", item)
    if match:
        return int(match.group(1)), int(match.group(2))

    raise ValueError(f"Could not parse edge definition: {item!r}")


def load_edge_list_matrix_csv(path):
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path, header=None, encoding="utf-8-sig")
    elif suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path, header=None)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    edge_index = []
    valid_cols = []

    for col, item in enumerate(df.iloc[0].values):
        if pd.isna(item):
            continue

        try:
            edge = parse_edge(item)
        except ValueError:
            # skip non-edge columns, e.g. subject ID column
            continue

        edge_index.append(edge)
        valid_cols.append(col)

    if len(edge_index) == 0:
        raise ValueError("No edge definitions found in the first row.")

    data = df.iloc[1:, valid_cols].to_numpy(dtype=float)

    return edge_index, data