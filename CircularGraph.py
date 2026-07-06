import os
import re
from pathlib import Path
from typing import Optional, Union

import numpy as np
from matplotlib.figure import Figure

from I_O.edge_list2mat import edge_list_to_matrix
from I_O.edge_loader import load_edge_list
from I_O.loader import (
    load_color_palette,
    load_labels,
    load_matrix,
    load_secondary_labels,
)

from Thresholds import thresholds

from Plotting import colors, defaults, layout, renderer
from Plotting.colors import ColorInput, PositiveNegativeInput

VALID_SEC_LABEL_MODES = ("Color", "Bracket", "False")


class CircularGraph:
    """Container for connectivity data used to create a circular graph.

    The class loads connectivity data from either a square matrix or an
    edge-list representation, loads optional ROI labels, secondary labels,
    and color palettes, and validates that all inputs are internally
    consistent before plotting.

    Attributes:
        mat: Symmetric connectivity matrix, shape (n_nodes, n_nodes).
        labels: Primary ROI labels, or None.
        secondary_labels: Optional group/network labels, or None.
        color_palette: Optional dictionary mapping secondary-label names
            to hexadecimal colors.
        mask: Boolean matrix, shape (n_nodes, n_nodes), initialized to
            True for all node pairs.
    """

    def __init__(
        self,
        mat_path: str | Path | np.ndarray,
        mat_type: str = "matrix",
        labels: None | str | Path | list | tuple | np.ndarray = None,
        secondary_labels: None | str | Path | list | tuple | np.ndarray = None,
        color_palette: None | dict[str, str] | str | Path = None,
        subject_idx: int = 0,
    ) -> None:
        """Initialize a CircularGraph object.

        Args:
            mat_path: Connectivity input. For ``mat_type="matrix"``, this
                may be a NumPy array or a path to a matrix file. For
                ``mat_type="edge_list"``, this may be an edge-value array
                or a path to an edge-list file.
            mat_type: Type of connectivity input. Must be either
                ``"matrix"`` or ``"edge_list"``.
            labels: Optional primary ROI labels. May be None, a predefined
                atlas name, a list/tuple/array of labels, or a supported
                label-file path.
            secondary_labels: Optional secondary labels used to group ROIs,
                such as networks, hemispheres, or anatomical regions.
            color_palette: Optional mapping from secondary-label names to
                hexadecimal color values, or a path to a palette file.
            subject_idx: Subject row to use when loading an edge-list file
                containing multiple subjects.

        Raises:
            ValueError: If ``mat_type`` is unsupported or if any loaded
                input is inconsistent with the connectivity matrix.
            TypeError: If matrix, labels, secondary labels, or palette
                values have invalid types.
        """
        if mat_type == "edge_list":
            edge_index, edge_values = load_edge_list(mat_path)
            self.mat = edge_list_to_matrix(edge_values, edge_index, subject_idx)

        elif mat_type == "matrix":
            self.mat = load_matrix(mat_path)

        else:
            raise ValueError(f"Unsupported mat_type: {mat_type}")

        self.labels = load_labels(labels)
        self.secondary_labels = load_secondary_labels(secondary_labels)
        self.color_palette = load_color_palette(color_palette)
        self.mask = np.ones(self.mat.shape, dtype=bool)

        self._validate()

    def apply_threshold(
        self,
        method: Optional[str] = None,
        **params,
    ) -> np.ndarray:
        """Compute and store self.mask for one threshold method at a time.

        This is the CircularGraph-bound counterpart to
        Thresholds.thresholds.apply_threshold(mat, method, **params) --
        same method names and params, just applied to self.mat and stored
        on self.mask instead of returned as a standalone ThresholdResult.
        Calling it again with a different method fully replaces the
        previous mask; it never combines two methods.

        Args:
            method: One of Thresholds.thresholds.VALID_THRESHOLD_METHODS
                ("weighted_average", "positive_negative_value",
                "positive_negative_percentile_value"), or None (the
                default) to clear thresholding and keep every edge.
            **params: Keyword parameters for the chosen method's
                constructor -- see
                Thresholds.thresholds.THRESHOLD_PARAM_SCHEMAS[method] for
                which names each method expects (e.g. value= for
                weighted_average, positive_value=/negative_value= for
                positive_negative_value).

        Returns:
            The new self.mask (n x n boolean array), for convenience.

        Raises:
            ValueError: If method is not None and not a recognized
                method, or if params doesn't match what that method's
                constructor accepts.
        """
        if method is None:
            self.mask = np.ones(self.mat.shape, dtype=bool)
            return self.mask

        if method not in thresholds.VALID_THRESHOLD_METHODS:
            raise ValueError(
                f"Unknown threshold method: {method!r}, expected None or one "
                f"of {thresholds.VALID_THRESHOLD_METHODS}"
            )

        result = thresholds.apply_threshold(self.mat, method, **params)
        self.mask = result.edge_mask
        return self.mask

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
        hemi_flip: bool = defaults.HEMI_FLIP,
    ) -> Figure:
        """Design and create the circular graph figure.
        Stores the result on self (as `_fig`/`_ax`) so that show()/savegraph() can be called later.

        Parameters:
            label: If True, draw each node's label from self.labels next to it.
            label_font: Font family for node labels, or None for default (taken from Matplotlib).
            label_size: Font size (points) for node labels.
            sec_label: Determine the grouping method for the secondary label.
                "Color": shows a legend mapping secondary label to color.
                "Bracket": draws a bracket + curved label over each group.
            sec_label_font: Font family for group labels/legend, or None for default (taken from Matplotlib).
            sec_label_size: Font size (points) for group labels/legend.
            edge_color_method: Determine how to choose edge colors.
                "Uniform": Same color for all edges (default - Gray)
                "PositiveNegative": Color is based on correlation direction (default - Pos=Red, Neg=Blue).
                "Node": Color is based on the sec_label color of the lower-indexed node out of the two.
                "Nodes": Color is a gradient between the two node sec_label colors.
            edge_color: Optional override color(s) for "Uniform" (a single color) or "PositiveNegative"
            (a dict/2-tuple of positive, negative). Ignored for "Node"/"Nodes".
            radius: Radius of the node circle (default - 1.5).
            hemi_flip: Mirror the second half of nodes for symmetrical organization of
            the two halves (typically hemispheres) (default - True)

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

        edges_mat = self.mat * self.mask
        n = len(edges_mat)
        labels_dict = dict(enumerate(self.labels)) if self.labels else {}
        secondary_labels = (
            dict(enumerate(self.secondary_labels)) if self.secondary_labels else {}
        )
        color_palette = self.color_palette or {}

        if hemi_flip:
            order = layout.compute_hemi_flip_order(n)
            edges_mat = edges_mat[np.ix_(order, order)]
            labels_dict = {
                new_i: labels_dict[old_i]
                for new_i, old_i in enumerate(order)
                if old_i in labels_dict
            }
            secondary_labels = {
                new_i: secondary_labels[old_i]
                for new_i, old_i in enumerate(order)
                if old_i in secondary_labels
            }

        positions = layout.compute_node_positions(n, radius=radius)
        angles = layout.compute_node_angles(n)
        hard_breaks = [n // 2 - 1] if hemi_flip and n > 0 else None
        groups = (
            layout.detect_groups(list(range(n)), secondary_labels, hard_breaks=hard_breaks)
            if secondary_labels
            else []
        )

        node_colors = colors.resolve_node_colors(n, secondary_labels, color_palette)

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

        if sec_label == "Bracket" and groups:
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

        Parameters:
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

    def _validate(self) -> None:
        """Validate that the graph data are internally consistent."""
        self._validate_matrix()
        self._validate_labels()
        self._validate_secondary_labels()
        self._validate_color_palette()

    def _validate_matrix(self) -> None:
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

    def _validate_labels(self) -> None:
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

    def _validate_secondary_labels(self) -> None:
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

    def _validate_color_palette(self) -> None:
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

    def _validate_color_format(self) -> None:
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

    def _validate_palette_matches_secondary_labels(self) -> None:
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
