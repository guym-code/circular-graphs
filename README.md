# [Project Name]

## Shared Documentation

https://docs.google.com/document/d/1a2ZQJTtFH3H57V8p0iG39yFw9OPO3pakU4-5SBe-X4o/edit?usp=sharing

## Shared Presentation

https://docs.google.com/presentation/d/1jaq3Cncm86KyL8Ov1DoASdZ6KH-fHWH5Bo7b2_KFSHM/edit?usp=sharing

---

# Overview

Circular connectivity graphs (also known as **connectograms** or **chord diagrams**) are widely used in neuroscience to visualize structural and functional connectivity between brain regions. They provide an intuitive representation of complex brain networks and are commonly featured in neuroimaging studies involving functional MRI (fMRI), diffusion MRI, EEG, MEG, and other connectivity analyses.

Despite their popularity, generating publication-quality connectograms often requires extensive manual customization or familiarity with specialized visualization libraries. Existing tools often require extensive programming expertise, manual customization, or complex configuration, making them difficult to adapt to different datasets, atlases, and visualization styles. Overall, the process is time-consuming for many researchers.

This project aims to simplify the creation of circular connectivity graphs by providing an intuitive Python application with an interactive graphical user interface. Users can import connectivity matrices or edge lists, customize the appearance of nodes and edges, organize regions using atlas-based or custom labels, and export publication-ready figures with minimal effort.

# Features

- Interactive graphical interface for intuitive creation of customizable connectograms.
- Supports connectivity matrices and edge lists.
- Supports built-in brain atlases as well as user-defined labels and annotations.
- Flexible customization of node labels, colors, edge appearance, and layout.
- Generates publication-quality circular connectivity visualizations suitable for scientific publications.

# Supported Atlases

- Multi-Modal Parcellation (MMP)
- Schaefer 100
- Schaefer 400
- Schaefer 600
- Schaefer 1000
- User-defined atlases

# Getting Started

*To be completed.*

# Usage

1. Launch the application.
2. Load connectivity data.
3. Select a built-in atlas or import user-defined labels.
4. Optionally add secondary labels.
5. Customize visualization settings.
6. Generate and export the connectogram.

# Input Files

The program accepts several input files for creating and customizing the connectogram.

## Connectivity Data

The main input can be either a **connectivity matrix** or an **edge list**.

A connectivity matrix should be a square matrix where rows and columns represent brain regions, and each value represents the connection strength between two regions.

An edge list should describe connections between pairs of regions and their corresponding edge weights.

## ROI Labels

The program supports predefined atlas labels as well as user-provided label files.

Label files should contain one label per region, in the same order as the connectivity data.

## Secondary Labels

Secondary labels are optional and can be used to group regions by network, hemisphere, anatomical region, or any user-defined category.

Secondary label files should contain one secondary label for each region, in the same order as the connectivity data.

## Color Palette

An optional CSV file can be provided to define colors for secondary labels.

Each row should map a secondary-label name to a color. Colors should be specified using hexadecimal (hex) color codes (e.g., `#FF0000`).

# Customization

The software allows users to customize the appearance and organization of the connectogram.

## Node Labels

- Display or hide primary ROI labels.
- Choose predefined atlas labels or custom label files.

## Secondary Labels

Users can choose how secondary labels are presented:

- No secondary labels
- Node coloring
- Group brackets
- Combined node coloring and group brackets

A custom color palette can also be provided for secondary-label groups.

## Edge Appearance

Choose one of four edge-coloring methods:

- **Uniform** – all edges share the same color.
- **Positive/Negative** – positive and negative edges are colored differently.
- **Node** – each edge is colored according to one of its connected nodes.
- **Nodes** – edges are displayed as a gradient between the colors of the connected nodes.

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

# Examples

*To be completed.*

# Repository Structure

*To be completed.*

# Future Work

*To be completed.*

# Authors

*To be completed.*

# License

*To be completed.*
