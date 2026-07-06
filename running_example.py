from pathlib import Path
from CircularGraph import CircularGraph

# Object loading:
g3 = CircularGraph(
    mat_path=Path("Main__Data", "mat_scf100.mat"),
    mat_type="matrix",
    labels="Schaefer 100",
    secondary_labels="Schaefer 100",
    color_palette=Path("Color Palettes","yeo_7_network_colors.csv")
)
print(g3.mat.shape)
print(g3.labels)
print(g3.secondary_labels)
print(g3.color_palette)

# Thresholding:
g3.apply_threshold(method='positive_negative_percentile_value', value_positive=99, value_negative=99)

# Plotting:
g3.plot(label=False, sec_label='Color', edge_color_method="Uniform")
g3.show()
g3.savegraph('test_graph.png', dpi=500)
