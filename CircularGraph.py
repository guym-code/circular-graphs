import re

import numpy as np

from I_O.edge_list2mat import edge_list_to_matrix
from I_O.edge_loader import load_edge_list_matrix_csv
from I_O.loader import (
    load_color_palette,
    load_labels,
    load_matrix,
    load_secondary_labels,
)


class CircularGraph:
    def __init__(
        self,
        mat_path,
        mat_type="matrix",
        labels=None,
        secondary_labels=None,
        color_palette=None,
    ):
        if mat_type == "edge_list":
            edge_index, edge_values = load_edge_list_matrix_csv(mat_path)
            self.mat = edge_list_to_matrix(edge_values, edge_index)

        elif mat_type == "matrix":
            self.mat = load_matrix(mat_path)

        else:
            raise ValueError(f"Unsupported mat_type: {mat_type}")

        self.labels = load_labels(labels)
        self.secondary_labels = load_secondary_labels(secondary_labels)
        self.color_palette = load_color_palette(color_palette)

        self._validate()

    def _validate(self):
        """Validate that the graph data are internally consistent."""
        self._validate_matrix()
        self._validate_labels()
        self._validate_secondary_labels()
        self._validate_color_palette()

    def _validate_matrix(self):
        """Validate matrix shape, type, numeric content, and symmetry."""
        if not isinstance(self.mat, np.ndarray):
            raise TypeError("mat must be a NumPy array.")

        if self.mat.ndim != 2:
            raise ValueError(f"mat must be 2D, got shape {self.mat.shape}")

        n_rows, n_cols = self.mat.shape

        if n_rows != n_cols:
            raise ValueError(
                f"Connectivity matrix must be square, got shape {self.mat.shape}"
            )

        if not np.issubdtype(self.mat.dtype, np.number):
            raise TypeError("Connectivity matrix must contain numeric values.")

        if np.isnan(self.mat).any():
            raise ValueError("Connectivity matrix contains NaN values.")

        if not np.allclose(self.mat, self.mat.T):
            raise ValueError("Connectivity matrix must be symmetric.")

    def _validate_labels(self):
        """Validate primary ROI labels."""
        if self.labels is None:
            return

        n_nodes = self.mat.shape[0]

        if len(self.labels) != n_nodes:
            raise ValueError(
                "Number of labels must match matrix size. "
                f"Got {len(self.labels)} labels for {n_nodes} nodes."
            )

        if not all(isinstance(label, str) for label in self.labels):
            raise TypeError("All labels must be strings.")

    def _validate_secondary_labels(self):
        """Validate secondary ROI labels."""
        if self.secondary_labels is None:
            return

        n_nodes = self.mat.shape[0]

        if len(self.secondary_labels) != n_nodes:
            raise ValueError(
                "Number of secondary labels must match matrix size. "
                f"Got {len(self.secondary_labels)} secondary labels "
                f"for {n_nodes} nodes."
            )

        if not all(
            isinstance(label, str)
            for label in self.secondary_labels
        ):
            raise TypeError("All secondary labels must be strings.")

    def _validate_color_palette(self):
        """Validate color palette and its match to secondary labels."""
        if self.color_palette is None:
            return

        if not isinstance(self.color_palette, dict):
            raise TypeError("color_palette must be a dictionary.")

        if not all(
            isinstance(key, str)
            for key in self.color_palette.keys()
        ):
            raise TypeError("All color palette keys must be strings.")

        if not all(
            isinstance(value, str)
            for value in self.color_palette.values()
        ):
            raise TypeError("All color palette values must be strings.")

        self._validate_color_format()

        if self.secondary_labels is None:
            raise ValueError(
                "A color palette was provided, but no "
                "secondary_labels were supplied."
            )

        self._validate_palette_matches_secondary_labels()

    def _validate_color_format(self):
        """Validate that all colors are '#RRGGBB' hex strings."""
        invalid_colors = [
            f"{region}: '{color}'"
            for region, color in self.color_palette.items()
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color)
        ]

        if invalid_colors:
            raise ValueError(
                "All colors must be valid hexadecimal colors of the form "
                "'#RRGGBB'.\n"
                "Invalid entries:\n"
                + "\n".join(invalid_colors)
            )

    def _validate_palette_matches_secondary_labels(self):
        """Validate one-to-one match between palette and secondary labels."""
        palette_regions = set(self.color_palette.keys())
        secondary_regions = set(self.secondary_labels)

        missing_in_palette = secondary_regions - palette_regions
        extra_in_palette = palette_regions - secondary_regions

        if missing_in_palette or extra_in_palette:
            msg = []

            if missing_in_palette:
                msg.append(
                    "Missing colors for: "
                    + ", ".join(sorted(missing_in_palette))
                )

            if extra_in_palette:
                msg.append(
                    "Unused palette entries: "
                    + ", ".join(sorted(extra_in_palette))
                )

            raise ValueError(
                "Color palette does not match secondary labels.\n"
                + "\n".join(msg)
            )
