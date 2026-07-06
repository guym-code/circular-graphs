"""Robustness tests for CircularGraph.plot(), .show(), and .savegraph().

Uses the non-interactive Agg backend throughout, so figures never need a
real display -- .show() still runs its normal code path (it just can't
paint to a screen), which is exactly what these tests want to exercise.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure
from PIL import Image

from CircularGraph import CircularGraph
from Plotting import layout as plotting_layout
from Plotting import renderer as plotting_renderer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _close_figures_after_each_test():
    """Every test creates at least one Figure via plot(); close them all
    afterward so a full run doesn't trip matplotlib's open-figure-count
    warning or accumulate memory."""
    yield
    plt.close("all")


def _make_graph(n=6, labels=True, secondary=True, palette=True, **kwargs):
    """Build a small, self-contained, symmetric-matrix CircularGraph.

    Args:
        n: Number of nodes.
        labels: If True, generate primary "ROI {i}" labels.
        secondary: If True, split nodes into 3 secondary-label groups.
        palette: If True (and secondary), supply an explicit color palette
            covering every group.
        **kwargs: Forwarded to CircularGraph's constructor.
    """
    rng = np.random.default_rng(0)
    mat = rng.uniform(-1, 1, size=(n, n))
    mat = (mat + mat.T) / 2
    np.fill_diagonal(mat, 0.0)

    lbls = [f"ROI {i}" for i in range(n)] if labels else None

    groups = None
    pal = None
    if secondary:
        names = ["A", "B", "C"]
        groups = [names[i % 3] for i in range(n)]
        if palette:
            pal = {"A": "#ff0000", "B": "#00ff00", "C": "#0000ff"}

    return CircularGraph(
        mat_path=mat,
        mat_type="matrix",
        labels=lbls,
        secondary_labels=groups,
        color_palette=pal,
        **kwargs,
    )


@pytest.fixture
def graph():
    """Graph with labels, secondary labels, and a matching color palette."""
    return _make_graph()


@pytest.fixture
def bare_graph():
    """Minimal graph: no labels, no secondary labels, no color palette."""
    return _make_graph(labels=False, secondary=False, palette=False)


# ---------------------------------------------------------------------------
# plot()
# ---------------------------------------------------------------------------


class TestPlotBasics:
    def test_returns_a_figure(self, graph):
        assert isinstance(graph.plot(), Figure)

    def test_stores_fig_and_ax_on_self(self, graph):
        fig = graph.plot()
        assert graph._fig is fig
        assert graph._ax is not None

    def test_bare_graph_with_no_labels_or_palette(self, bare_graph):
        assert isinstance(bare_graph.plot(), Figure)

    def test_with_primary_labels(self, graph):
        assert isinstance(graph.plot(label=True), Figure)

    def test_secondary_labels_without_a_color_palette(self):
        g = _make_graph(secondary=True, palette=False)
        assert isinstance(g.plot(sec_label="Color"), Figure)

    def test_can_be_called_multiple_times(self, graph):
        first = graph.plot()
        second = graph.plot()
        assert isinstance(second, Figure)
        assert graph._fig is second
        assert first is not second


class TestPlotSecLabelModes:
    @pytest.mark.parametrize("sec_label", ["Color", "Bracket", "False", False])
    def test_every_valid_mode_succeeds(self, graph, sec_label):
        assert isinstance(graph.plot(sec_label=sec_label), Figure)

    def test_invalid_mode_raises_value_error(self, graph):
        with pytest.raises(ValueError, match="sec_label"):
            graph.plot(sec_label="ColorBracket")

    def test_bracket_mode_with_no_secondary_labels_does_not_raise(self, bare_graph):
        # No groups to draw brackets for, should just be a no-op.
        assert isinstance(bare_graph.plot(sec_label="Bracket"), Figure)


class TestPlotHemiFlip:
    def test_hemi_flip_true_does_not_raise(self, graph):
        assert isinstance(graph.plot(hemi_flip=True), Figure)

    def test_hemi_flip_false_does_not_raise(self, graph):
        assert isinstance(graph.plot(hemi_flip=False), Figure)

    def test_hemi_flip_with_odd_node_count(self):
        g = CircularGraph(
            mat_path=np.zeros((5, 5)),
            mat_type="matrix",
            secondary_labels=["A", "A", "B", "B", "B"],
            color_palette={"A": "#111111", "B": "#222222"},
        )
        assert isinstance(g.plot(hemi_flip=True, sec_label="Bracket"), Figure)

    @staticmethod
    def _distinct_weight_matrix(n):
        """Symmetric n x n matrix where every ROI pair gets a unique,
        traceable weight (i, j) -> (10*i + j) / 100, scaled to stay
        within the [-1, 1] range the loader enforces."""
        mat = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                v = (10 * i + j) / 100.0
                mat[i, j] = v
                mat[j, i] = v
        return mat

    def test_edges_follow_their_rois_after_flip(self, monkeypatch):
        # Every drawn edge must still carry the *original* weight between
        # whichever two ROIs actually ended up at those two draw
        # positions -- hemi_flip must never scramble which edge value
        # belongs to which pair of ROIs, only where they're drawn.
        n = 6
        mat = self._distinct_weight_matrix(n)
        labels = [f"ROI{i}" for i in range(n)]
        g = CircularGraph(mat_path=mat, mat_type="matrix", labels=labels)

        captured = {}

        def _spy_draw_edges(ax, positions, edges, *args, **kwargs):
            captured["edges"] = edges

        monkeypatch.setattr(plotting_renderer, "draw_edges", _spy_draw_edges)

        g.plot(hemi_flip=True)

        order = plotting_layout.compute_hemi_flip_order(n)
        assert captured.get("edges"), "expected draw_edges to be called with edges"
        for i, j, weight, _color_a, _color_b in captured["edges"]:
            orig_i, orig_j = order[i], order[j]
            expected = mat[orig_i, orig_j]
            assert weight == pytest.approx(expected), (
                f"edge drawn at positions ({i}, {j}) -- ROI{orig_i}/ROI{orig_j} "
                f"-- has weight {weight}, expected {expected}"
            )

    def test_edges_match_original_indices_without_flip(self, monkeypatch):
        # Baseline: with hemi_flip disabled, draw position == original
        # ROI index, so every edge weight should match the untouched
        # matrix entry at the same (i, j).
        n = 6
        mat = self._distinct_weight_matrix(n)
        g = CircularGraph(mat_path=mat, mat_type="matrix")

        captured = {}

        def _spy_draw_edges(ax, positions, edges, *args, **kwargs):
            captured["edges"] = edges

        monkeypatch.setattr(plotting_renderer, "draw_edges", _spy_draw_edges)

        g.plot(hemi_flip=False)

        assert captured.get("edges"), "expected draw_edges to be called with edges"
        for i, j, weight, _color_a, _color_b in captured["edges"]:
            assert weight == pytest.approx(mat[i, j])


class TestPlotRadius:
    def test_figsize_scales_linearly_with_radius(self, graph):
        small = graph.plot(radius=2.0).get_size_inches()
        large = graph.plot(radius=4.0).get_size_inches()
        assert large[0] == pytest.approx(small[0] * 2.0)
        assert large[1] == pytest.approx(small[1] * 2.0)

    def test_large_radius_does_not_raise(self, graph):
        # Regression guard: bracket-label spacing math must stay correct
        # (not collapse into overlapping glyphs) even at extreme radii.
        assert isinstance(graph.plot(radius=20.0, sec_label="Bracket"), Figure)

    def test_small_radius_does_not_raise(self, graph):
        assert isinstance(graph.plot(radius=0.25), Figure)


class TestPlotEdgeColorMethods:
    @pytest.mark.parametrize(
        "method", ["Uniform", "PositiveNegative", "Node", "Nodes"]
    )
    def test_every_method_succeeds(self, graph, method):
        assert isinstance(graph.plot(edge_color_method=method), Figure)

    def test_uniform_with_color_override(self, graph):
        fig = graph.plot(edge_color_method="Uniform", edge_color="#123456")
        assert isinstance(fig, Figure)

    def test_positive_negative_with_dict_override(self, graph):
        fig = graph.plot(
            edge_color_method="PositiveNegative",
            edge_color={"positive": "#ff0000", "negative": "#0000ff"},
        )
        assert isinstance(fig, Figure)

    def test_positive_negative_with_invalid_override_raises(self, graph):
        with pytest.raises(ValueError):
            graph.plot(edge_color_method="PositiveNegative", edge_color=123)


class TestPlotSizesAndMasking:
    def test_fully_masked_graph_has_no_edges_but_still_plots(self, graph):
        graph.mask = np.zeros_like(graph.mat, dtype=bool)
        assert isinstance(graph.plot(), Figure)

    def test_single_node_graph(self):
        g = CircularGraph(mat_path=np.zeros((1, 1)), mat_type="matrix")
        assert isinstance(g.plot(), Figure)

    def test_two_node_graph(self):
        mat = np.array([[0.0, 0.7], [0.7, 0.0]])
        g = CircularGraph(mat_path=mat, mat_type="matrix")
        assert isinstance(g.plot(), Figure)


# ---------------------------------------------------------------------------
# show()
# ---------------------------------------------------------------------------


class TestShow:
    def test_before_plot_raises_runtime_error(self, graph):
        with pytest.raises(RuntimeError, match="plot"):
            graph.show()

    def test_after_plot_does_not_raise(self, graph):
        graph.plot()
        with pytest.warns(UserWarning, match="non-interactive"):
            graph.show()

    def test_can_be_called_multiple_times(self, graph):
        graph.plot()
        with pytest.warns(UserWarning, match="non-interactive"):
            graph.show()
        with pytest.warns(UserWarning, match="non-interactive"):
            graph.show()


# ---------------------------------------------------------------------------
# savegraph()
# ---------------------------------------------------------------------------


class TestSaveGraph:
    def test_before_plot_raises_runtime_error(self, graph, tmp_path):
        with pytest.raises(RuntimeError, match="plot"):
            graph.savegraph(tmp_path / "out.png")

    def test_writes_a_nonempty_file(self, graph, tmp_path):
        graph.plot()
        out = tmp_path / "out.png"
        graph.savegraph(out)
        assert out.exists()
        assert out.stat().st_size > 0

    @pytest.mark.parametrize("fmt", ["png", "jpeg", "svg", "pdf"])
    def test_every_format_is_written(self, graph, tmp_path, fmt):
        graph.plot()
        out = tmp_path / f"out.{fmt}"
        graph.savegraph(out, format=fmt)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_accepts_a_pathlib_path(self, graph, tmp_path):
        graph.plot()
        out = tmp_path / "nested" / "out.png"
        out.parent.mkdir()
        graph.savegraph(out)
        assert out.exists()

    def test_can_be_called_multiple_times_to_the_same_path(self, graph, tmp_path):
        graph.plot()
        out = tmp_path / "out.png"
        graph.savegraph(out)
        first_size = out.stat().st_size
        graph.savegraph(out)
        assert out.exists()
        assert out.stat().st_size > 0
        # Not asserting equality with first_size: just that a second write
        # over the same path succeeds cleanly.
        assert first_size > 0

    def test_higher_dpi_yields_larger_pixel_dimensions(self, graph, tmp_path):
        graph.plot(radius=1.0)
        low = tmp_path / "low.png"
        high = tmp_path / "high.png"
        graph.savegraph(low, dpi=50)
        graph.savegraph(high, dpi=200)
        with Image.open(low) as im_low, Image.open(high) as im_high:
            assert im_high.size[0] > im_low.size[0]
            assert im_high.size[1] > im_low.size[1]

    def test_background_none_is_transparent(self, graph, tmp_path):
        graph.plot(radius=1.0)
        out = tmp_path / "out.png"
        graph.savegraph(out, background=None)
        with Image.open(out) as im:
            im = im.convert("RGBA")
            corner_alpha = im.getpixel((0, 0))[3]
        assert corner_alpha == 0

    def test_default_background_is_opaque(self, graph, tmp_path):
        graph.plot(radius=1.0)
        out = tmp_path / "out.png"
        graph.savegraph(out)
        with Image.open(out) as im:
            im = im.convert("RGBA")
            corner_alpha = im.getpixel((0, 0))[3]
        assert corner_alpha == 255
