from I_O.loader import load_matrix, load_labels, load_secondary_labels, load_color_palette
from I_O.edge_loader import load_edge_list_matrix_csv
from I_O.edge_list2mat import edge_list_to_matrix

import numpy as np

class CircularGraph:
    def __init__(self, mat_path, mat_type='matrix', labels=None, secondary_labels=None, color_palette=None):

        if mat_type == 'edge_list':
            edge_index, edge_values = load_edge_list_matrix_csv(mat_path)
            self.mat = edge_list_to_matrix(edge_values, edge_index)

        elif mat_type == 'matrix':
            self.mat = load_matrix(mat_path)

        else:
            raise ValueError(f"Unsupported mat_type: {mat_type}")

        self.labels = load_labels(labels)
        self.secondary_labels = load_secondary_labels(secondary_labels)
        self.color_palette = load_color_palette(color_palette)

        self._validate()

    def _validate(self):
        """
        Validate that the loaded graph data are internally consistent.
        """
        # ---- matrix validation ----
        if not isinstance(self.mat, np.ndarray):
            raise TypeError("mat must be a NumPy array.")

        if self.mat.ndim != 2:
            raise ValueError(f"mat must be 2D, got shape {self.mat.shape}")

        n_rows, n_cols = self.mat.shape

        if n_rows != n_cols:
            raise ValueError(
                f"Connectivity matrix must be square, got shape {self.mat.shape}"
            )

        n_nodes = n_rows

        if not np.issubdtype(self.mat.dtype, np.number):
            raise TypeError("Connectivity matrix must contain numeric values.")

        if np.isnan(self.mat).any():
            raise ValueError("Connectivity matrix contains NaN values.")

        # ---- labels validation ----
        if self.labels is not None:
            if len(self.labels) != n_nodes:
                raise ValueError(
                    f"Number of labels must match matrix size. "
                    f"Got {len(self.labels)} labels for {n_nodes} nodes."
                )

            if not all(isinstance(label, str) for label in self.labels):
                raise TypeError("All labels must be strings.")

        # ---- secondary labels validation ----
        if self.secondary_labels is not None:
            if len(self.secondary_labels) != n_nodes:
                raise ValueError(
                    f"Number of secondary labels must match matrix size. "
                    f"Got {len(self.secondary_labels)} secondary labels "
                    f"for {n_nodes} nodes."
                )

            if not all(isinstance(label, str) for label in self.secondary_labels):
                raise TypeError("All secondary labels must be strings.")

        # ---- optional symmetry check ----
        if not np.allclose(self.mat, self.mat.T):
            raise ValueError("Connectivity matrix must be symmetric.")
        
        # ---- color palette validation ----
        if self.color_palette is not None:

            if not isinstance(self.color_palette, dict):
                raise TypeError("color_palette must be a dictionary.")

            if not all(isinstance(k, str) for k in self.color_palette.keys()):
                raise TypeError("All color palette keys must be strings.")

            if not all(isinstance(v, str) for v in self.color_palette.values()):
                raise TypeError("All color palette values must be strings.")

            if self.secondary_labels is not None:

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
