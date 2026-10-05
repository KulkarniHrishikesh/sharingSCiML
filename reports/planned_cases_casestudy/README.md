# Turbomachinery CFD validation portfolio: case study

`Turbomachinery_Planned_Cases_CaseStudy.pdf` is a 49-slide beamer deck covering the 19 planned OpenFOAM v2412 turbomachinery cases that are not yet validated. It is written as a review presented by the lead CFD engineer to the principal CFD lead.

Each case has two slides:
- a fact card: geometry, mesh, fluid, physics, rotation model, boundary conditions, operating point, validation data, references;
- a visual slide: geometry, mesh and results (or the measured validation target), plus an engineering assessment.

The deck opens with the decisions requested and an executive summary. It closes with cross-cutting lessons, a recommended plan and the full reference list. Rig facts were checked against primary sources on 5 October 2026.

Images are our own renders unless the caption names a source; source figures remain the property of their authors and publishers.

Build: `tectonic -X compile cs.tex` (images in `cs/`).
