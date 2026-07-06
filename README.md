# NeuroCircles
<img width="3646" height="3646" alt="test_graph" src="https://github.com/user-attachments/assets/7ff0c661-de00-4364-b894-d2062813cb22" />

## Shared Presentation

https://docs.google.com/presentation/d/1jaq3Cncm86KyL8Ov1DoASdZ6KH-fHWH5Bo7b2_KFSHM/edit?usp=sharing

---

# Overview

Circular connectivity graphs (also known as **connectograms** or **chord diagrams**) are widely used in neuroscience to visualize structural and functional connectivity between brain regions. They provide an intuitive representation of complex brain networks and are commonly featured in neuroimaging studies involving functional MRI (fMRI), diffusion MRI, EEG, MEG, and other connectivity analyses.

Despite their popularity, generating publication-quality connectograms often requires extensive manual customization or familiarity with specialized visualization libraries. Existing tools often require extensive programming expertise, manual customization, or complex configuration, making them difficult to adapt to different datasets and visualization styles.

This project aims to simplify the creation of circular connectivity graphs by providing an intuitive Python application with an interactive graphical user interface. Users can import connectivity matrices or edge lists, customize the appearance of nodes and edges, organize regions using atlas-based or custom labels, and export publication-ready figures with minimal effort.

# Features

- Interactive graphical interface for intuitive creation of customizable connectograms.
- Supports connectivity matrices and edge lists.
- Supports built-in brain atlases as well as user-defined labels and annotations.
- Flexible customization of node labels, colors, edge appearance, and layout.
- Generates publication-quality circular connectivity visualizations suitable for scientific publications.

# GUI
<img width="1151" height="825" alt="image" src="https://github.com/user-attachments/assets/26a9c77f-4339-4888-968c-6198776b464f" />

# Getting Started

### Prerequisites

Before running the project, ensure that you have:

- **Python 3.10 or later**
- All required Python packages installed (see `requirements.txt`)

> **Note:** This project was developed and tested using **Python 3.10**. Earlier Python versions are not supported.

### Installation

1. Clone the repository:

```bash
git clone https://github.com/guym-code/circular-graphs.git
cd circular-graphs
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

### Running the Application

Launch the graphical user interface with:

```bash
python GUI.py
```

# Usage

1. Launch the application.
2. Load connectivity data.
3. Select a built-in atlas or import user-defined labels.
4. Optionally add secondary labels.
5. Customize visualization settings.
6. Generate and export the connectogram.
7. The generated connectogram is displayed in a Matplotlib window and simultaneously saved to the selected output file.

# Supported Atlases

- Multi-Modal Parcellation (MMP)
- Schaefer 100
- Schaefer 400
- Schaefer 600
- Schaefer 1000
- User-defined atlases

# Input Files

The application accepts several optional input files for creating and customizing the connectogram.

## Connectivity Data

The connectivity data is the only required input. It can be supplied either as a **connectivity matrix** or as an **edge list**.

### Supported Formats

Connectivity data may be provided as:

- NumPy array
- CSV (`.csv`)
- Excel (`.xls`, `.xlsx`)
- NumPy binary (`.npy`)
- MATLAB (`.mat`)

---

### Connectivity Matrix

A connectivity matrix must be a square matrix of shape **N × N**, where **N** is the number of regions of interest (ROIs).

Each matrix element represents the connection strength between two regions.

Example:

|     | ROI 1 | ROI 2 | ROI 3 |
|-----|-------|-------|-------|
| ROI 1 | 1.0 | 0.42 | -0.18 |
| ROI 2 | 0.42 | 1.0 | 0.25 |
| ROI 3 | -0.18 | 0.25 | 1.0 |

The matrix is assumed to be symmetric. Diagonal values are ignored during visualization.

---

### Edge List

Connectivity may alternatively be supplied as an edge list.

Each row represents one subject (or one connectivity matrix), while each column corresponds to one connection between two ROIs.

The first column is assumed to contain subject identifiers (or any non-edge identifier) and is ignored during loading.

Two edge-list formats are supported.

#### 1. Edge names included

The first row contains ROI pairs:

| Subject | (1,2) | (1,3) | (2,3) | ... |
|---------|------:|------:|------:|----:|
| 001 | 0.42 | -0.18 | 0.25 | ... |

ROI pairs may be written in any of the following formats:

- `(1,2)`
- `1,2`
- `1-2`
- `1_2`

#### 2. Edge names omitted

If edge names are omitted, the software automatically infers the connectivity structure from the number of columns.

The following layouts are recognized automatically:

- **Upper triangular matrix (without the diagonal)** containing `N(N−1)/2` edge columns.
- **Complete symmetric matrix** containing `N²` edge columns.

No additional configuration is required.

---

### Symmetric Edge Lists

The edge list may contain either

- only one entry for each connection (e.g. `(1,2)` but not `(2,1)`), or
- both `(i,j)` and `(j,i)` entries.

When both directions are provided, their values must be identical. Otherwise, an error is raised to prevent inconsistent connectivity matrices.

Diagonal entries such as `(1,1)` are optional and are ignored during visualization.

---

## ROI Labels

ROI labels define the names displayed around the connectogram.

Labels may be supplied as:

- a built-in atlas
- a Python list, tuple, or NumPy array
- CSV (`.csv`)
- TSV (`.tsv`)
- TXT (`.txt`)
- Excel (`.xls`, `.xlsx`)
- NumPy (`.npy`)

For table-based files, the **last column** is interpreted as the label column.

Labels must appear in the same order as the ROIs in the connectivity data.

---

## Secondary Labels

Secondary labels are optional annotations used to group ROIs into higher-level categories such as:

- Functional networks
- Hemispheres
- Anatomical regions
- User-defined groups

Secondary labels support the same input formats as ROI labels and must follow the same ROI ordering.

Built-in secondary labels are available for the included Schaefer atlases.

---

## Color Palette

An optional color palette can be supplied to define colors for secondary-label groups.

Supported formats:

- CSV (`.csv`)
- TSV (`.tsv`)
- TXT (`.txt`)
- Excel (`.xls`, `.xlsx`)

The file must contain at least two columns:

| Group | Color |
|-------|-------|
| Visual | `#4F81BD` |
| Default | `#C0504D` |

The first row is assumed to contain column headers and is ignored.

Colors should be specified using hexadecimal RGB notation (e.g. `#A450AE`).

# Customization

The software allows users to customize the appearance and organization of the connectogram.

## Node Labels

- Display or hide primary ROI labels, customize font and font size
- Choose predefined atlas labels or custom label files.

## Secondary Labels

Users can choose how secondary labels are presented:

- No secondary labels
- Node coloring (With secondary label legend)
- Group brackets

A custom color palette can also be provided for secondary-label groups.
Custom font and font size can be specified for secondary labels.

## Edge Appearance

Choose one of four edge-coloring methods:

- **Uniform** – all edges share the same color, can be customized.
- **Positive/Negative** – positive and negative edges are colored differently, colors can be customized.
- **Node** – each edge is colored according to its lower-indexed connected nodes.
- **Nodes** – edges are displayed as a gradient between the colors of the connected nodes.

## Graph
Graph layout can be customized, including:
- **Hemisphere flip** - Indices of nodes after the midway point are flipped, to create hemisphere symmetry. Can be altered.
- **Radius** - Graph radius can be adjusted to fit the node amount, change spacing between nodes, etc.

## Thresholding

Several thresholding methods are available to simplify network visualization:

- **No thresholding** – display all edges.
- **Weighted average threshold** – display only edges connected to nodes whose average absolute edge weight is greater than the specified threshold (exclusive).
- **Positive/negative value threshold** – display only edges whose weight is greater than the specified positive threshold or less than the specified negative threshold (exclusive).
- **Positive/negative percentile threshold** – display only edges whose weights fall within the selected percentile of the positive or negative edge-weight distribution.

Depending on the selected method, users can define one or two threshold values.

## Output

- Specify the output filename.
- Export figures in **PNG**, **JPEG**, **SVG**, or **PDF** formats.


## Repository Structure

```text
circular-graphs/
│
├── I_O/                         # Input/output utilities
│   ├── loader.py                # Loads connectivity matrices and label files
│   ├── edge_loader.py           # Loads edge-list files
│   └── edge_list2mat.py         # Converts edge lists into connectivity matrices
│
├── Plotting/                    # Circular graph visualization utilities
│   ├── renderer.py              # Draws nodes, edges, and labels
│   ├── layout.py                # Computes node positions and graph layout
│   ├── colors.py                # Handles node and edge coloring
│   └── defaults.py              # Default plotting parameters
│
├── Thresholds/                  # Thresholding algorithms
│   ├── thresholds.py            # Thresholding implementations
│   └── defaults_thresholds.py   # Default threshold parameters
│
├── icons/                       # GUI icons and images
├── Main_Data/                   # Example datasets and label files
├── tests/                       # Test scripts
│
├── CircularGraph.py             # Main circular graph class
├── GUI.py                       # Graphical user interface
├── pyproject.toml               # Project configuration                      
├── requirements.txt             # Required Python packages
├── LICENSE                      # Software license (MIT)
└── README.md                    # Project documentation
```

# Authors

- Amit Keinan
- Guy Malka
- Yoav Melamed
- Gilad Shilo
- Tom Zemer

# License

This project is licensed under the MIT License.
See the LICENSE file for details.
