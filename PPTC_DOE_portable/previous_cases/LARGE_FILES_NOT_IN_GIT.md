# Large archives not stored in this repository

GitHub rejects files over 100 MB, so these previous-case archives are kept outside git.
They are only needed to re-train on, or re-analyse, the full fields of the earlier runs.

| File | Size | Contents |
|---|---|---|
| `sweep_17runs/fields.tgz` | 2.6 GB | final-time fields + meshes of the 17-run RunPod sweep (M1/M2/M3 mesh study + 14 parametric runs) |
| `sweep_17runs/light.tgz` | 227 MB | force/moment histories, residuals, propeller-surface VTK and logs of the 17 runs |
| `rerun_4cases/fields3.tgz` | 522 MB | final-time fields + meshes of the 4 force-converged reruns |

Location: the owner's workstation, `~/Documents/OpenFOAM_Turbomachinery_Reports/PPTC_DOE_portable/previous_cases/`.
Results tables (`results.csv`), plots and `rerun_4cases/light3.tgz` (45 MB) are in the repository.
To run the DOE itself none of these archives is needed (see `../README.md`).
