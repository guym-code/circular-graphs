"""Default parameter values for circular graph plotting"""

from typing import Tuple

LABEL: bool = False
LABEL_FONT: str = "DejaVu Sans"
LABEL_SIZE: int = 10

SEC_LABEL: str = "Color"
SEC_LABEL_FONT: str = "DejaVu Sans"
SEC_LABEL_SIZE: int = 10

EDGE_COLOR_METHOD: str = "Uniform"
EDGE_COLOR_UNIFORM: str = "#BBBBBB"  # Black
EDGE_COLOR_POSITIVE: str = "#ff0000"  # Red
EDGE_COLOR_NEGATIVE: str = "#0000ff"  # Blue

SAVE_NAME: str = "untitled"
SAVE_FORMAT: str = "png"
SAVE_DPI: int = 300
SAVE_BACKGROUND: str = "#ffffff"  # White

# Used when color palette was not loaded, but there are secondary labels.
SEC_LABEL_FALLBACK_COLORMAP: str = "Set2"
# Used only when a graph has no secondary_labels, so edge_color_method 'Node'/'Nodes' still has a color to draw from.
NODE_FALLBACK_COLORMAP: str = "hsv"

# Mirror the second half of nodes (typically left/right hemispheres)
HEMI_FLIP: bool = True

NODE_RADIUS: float = 2
# 0.0 = chords bow through the center; 1.0 = straight lines.
EDGE_CURVATURE: float = 0.0
EDGE_LINEWIDTH_RANGE: Tuple[float, float] = (0.5, 1.7)

# Half-width/height of the (square) plot view, in data units.
PLOT_EXTENT: float = 2.5

# Figure size (inches) at NODE_RADIUS/PLOT_EXTENT's default scale.
FIGSIZE: Tuple[float, float] = (10.0, 10.0)
