# circular-graphs




## Product Requirements Shared Doc (you can edit) 
https://docs.google.com/document/d/1a2ZQJTtFH3H57V8p0iG39yFw9OPO3pakU4-5SBe-X4o/edit?usp=sharing

Shared Presentation:
https://docs.google.com/presentation/d/1jaq3Cncm86KyL8Ov1DoASdZ6KH-fHWH5Bo7b2_KFSHM/edit?usp=sharing


Many neuroscience studies visualize structural or functional connectivity using circular representations (connectograms or chord diagrams). Although these figures are common in publications and are frequently featured in high-impact journals, existing software often requires substantial programming expertise, extensive manual customization, or cumbersome configuration before publication-quality figures can be produced.

Our idea is to develop a Python package, accompanied by a simple graphical user interface (GUI), that enables researchers to generate customizable, publication-quality brain connectivity visualizations directly from connectivity matrices or edge lists.

Potential features include:

* Import connectivity matrices or edge lists.
* Automatic arrangement of brain regions around the circle using a selected atlas or user-provided labels.
* Grouping of regions by hemisphere, functional network, or any user-defined category.
* Flexible color schemes (e.g., network-specific colors or separate color maps for positive and negative connections).
* Edge thickness proportional to connection strength.
* Thresholding and filtering of weak connections.
* Interactive adjustment of visualization parameters through the GUI.
* Export of publication-ready figures in high-resolution formats (SVG, PDF, PNG).

The primary goal is to create an intuitive tool that substantially simplifies the generation of aesthetically pleasing, publication-quality connectograms while requiring minimal manual editing. Such a package could benefit many neuroscience laboratories working with structural or functional connectivity data. For the hackathon, we will either generate synthetic datasets or collaborate with colleagues who can provide suitable connectivity data for development and testing.
