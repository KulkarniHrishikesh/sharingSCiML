# Planned turbomachinery cases: not yet validated

`Turbomachinery_Planned_Cases.pdf` is a 27-slide beamer deck with one slide per planned OpenFOAM v2412 turbomachinery case (19 cases). Each slide covers geometry, domain and mesh, fluid, physics and solver, rotation model (MRF, sliding mesh/AMI, mixingPlane, SRF), boundary conditions, operating point, validation data, references and status.

- Rig facts were checked against primary sources on 5 October 2026. The full reference list is at the end of the deck.
- Set-ups marked *Planned* are proposals, not results.

Build from source (needs a LaTeX distribution with beamer, or `tectonic`):

```bash
tectonic -X compile planned_cases.tex
```

Images used by the source are in `plots/`.
