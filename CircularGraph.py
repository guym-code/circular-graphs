import os
import re
from typing import Optional, Union

import numpy as np
from matplotlib.figure import Figure

from I_O.edge_list2mat import edge_list_to_matrix
from I_O.edge_loader import load_edge_list_matrix_csv
from I_O.loader import (
    load_color_palette,
    load_labels,
    load_matrix,
    load_secondary_labels,
)
from plotting import colors, defaults, layout, renderer
from plotting.colors import ColorInput, PositiveNegativeInput

VALID_SEC_LABEL_MODES = ("Color", "Bracket", "ColorBracket", "False")


class CircularGraph:
    def __init__(
        self,
        mat_path,
        mat_type="matrix",
        labels=None,
        secondary_labels=None,
        color_palette=None,
        subject_idx=0
    ):
        if mat_type == "edge_list":
            edge_index, edge_values = load_edge_list_matrix_csv(mat_path)
            self.mat = edge_list_to_matrix(edge_values, edge_index, subject_idx)

        elif mat_type == "matrix":
            self.mat = load_matrix(mat_path)

        else:
            raise ValueError(f"Unsupported mat_type: {mat_type}")

        self.labels = load_labels(labels)
        self.secondary_labels = load_secondary_labels(secondary_labels)
        self.color_palette = load_color_palette(color_palette)

        self._validate()

    def plot(
        self,
        label: bool = defaults.LABEL,
        label_font: Optional[str] = defaults.LABEL_FONT,
        label_size: float = defaults.LABEL_SIZE,
        sec_label: Union[str, bool] = defaults.SEC_LABEL,
        sec_label_font: Optional[str] = defaults.SEC_LABEL_FONT,
        sec_label_size: float = defaults.SEC_LABEL_SIZE,
        edge_color_method: str = defaults.EDGE_COLOR_METHOD,
        edge_color: Optional[Union[ColorInput, PositiveNegativeInput]] = None,
        radius: float = defaults.NODE_RADIUS,
    ) -> Figure:
        """Design and create the circular graph figure.

        Builds node layout and colors, draws nodes/edges/labels/group annotations,
        and stores the result on self (as `_fig`/`_ax`) so that show()/savegraph() can later be called afterwards.

        Args:
            label: If True, draw each node's label from self.labels next
                to it.
            label_font: Font family for node labels, or None for default.
            label_size: Font size (points) for node labels.
            sec_label: One of "Color", "Bracket", "ColorBracket", "False"
                (or the boolean False, treated as "False").
                "Color" colors nodes by secondary label and shows a legend
                "Bracket" draws a bracket + curved label over each group.
                "ColorBracket" does both (no legend needed).
            sec_label_font: Font family for group labels/legend, or None for default.
            sec_label_size: Font size (points) for group labels/legend.
            edge_color_method: One of "Uniform", "PositiveNegative", "Node", "Nodes".
            edge_color: Optional override color(s) for "Uniform" (a single color) or "PositiveNegative"
            (a dict/2-tuple of positive, negative). Ignored for "Node"/"Nodes".
            radius: Radius of the node circle, 1 is the default.

        Returns:
            The created matplotlib Figure (also stored as self._fig).

        Raises:
            ValueError: If `sec_label` is not a recognized mode.
        """
        if sec_label is False:
            sec_label = "False"
        if sec_label not in VALID_SEC_LABEL_MODES:
            raise ValueError(
                f"sec_label must be one of {VALID_SEC_LABEL_MODES}, got {sec_label!r}"
            )

        edges_mat = self.mat
        n = len(edges_mat)
        labels_dict = dict(enumerate(self.labels)) if self.labels else {}
        secondary_labels = (
            dict(enumerate(self.secondary_labels)) if self.secondary_labels else {}
        )
        color_scheme = self.color_palette or {}

        positions = layout.compute_node_positions(n, radius=radius)
        angles = layout.compute_node_angles(n)
        groups = (
            layout.detect_groups(list(range(n)), secondary_labels)
            if secondary_labels
            else []
        )

        node_colors = colors.resolve_node_colors(n, secondary_labels, color_scheme)

        scale = radius / defaults.NODE_RADIUS
        extent = defaults.PLOT_EXTENT * scale
        figsize = (defaults.FIGSIZE[0] * scale, defaults.FIGSIZE[1] * scale)

        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                weight = edges_mat[i][j]
                if not weight:
                    continue
                color_a, color_b = colors.resolve_edge_color_pair(
                    edge_color_method, edge_color, node_colors, i, j, weight
                )
                edges.append((i, j, weight, color_a, color_b))

        fig, ax = renderer.create_figure(figsize=figsize)
        renderer.draw_edges(ax, positions, edges)
        renderer.draw_nodes(ax, positions, node_colors)

        if label:
            node_labels = [labels_dict.get(i) for i in range(n)]
            renderer.draw_labels(
                ax, angles, node_labels, font=label_font, size=label_size, radius=radius
            )

        if sec_label in ("Bracket", "ColorBracket") and groups:
            renderer.draw_group_brackets(
                ax,
                fig,
                n,
                groups,
                node_colors,
                font=sec_label_font,
                size=sec_label_size,
                radius=radius,
                extent=extent,
            )
        if sec_label == "Color" and groups:
            renderer.draw_group_legend(
                ax, node_colors, groups, font=sec_label_font, size=sec_label_size
            )

        renderer.finalize_axes(ax, extent=extent)

        self._fig = fig
        self._ax = ax
        return fig

    def show(self) -> None:
        """Show the figure created by a prior call to plot().

        Raises:
            RuntimeError: If plot() has not been called yet.
        """
        fig = getattr(self, "_fig", None)
        if fig is None:
            raise RuntimeError("show() requires plot() to be called first")
        fig.show()

    def savegraph(
        self,
        fname: Union[str, "os.PathLike[str]"] = defaults.SAVE_NAME,
        format: str = defaults.SAVE_FORMAT,
        dpi: int = defaults.SAVE_DPI,
        background: Optional[str] = defaults.SAVE_BACKGROUND,
    ) -> None:
        """Save the figure created by a prior call to plot().

        Args:
            fname: Output path, as a string or path-like object, including
                the filename.
            format: Image format (e.g. "png", "svg", "pdf").
            dpi: Resolution in dots per inch.
            background: Hex color for the saved image's background, or None
                for a transparent background.

        Raises:
            RuntimeError: If plot() has not been called yet.
        """
        fig = getattr(self, "_fig", None)
        if fig is None:
            raise RuntimeError("savegraph() requires plot() to be called first")
        facecolor = colors.normalize_hex(background) if background else "none"
        fig.savefig(
            fname,
            format=format,
            dpi=dpi,
            facecolor=facecolor,
            transparent=(background is None),
            bbox_inches="tight",
        )

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
