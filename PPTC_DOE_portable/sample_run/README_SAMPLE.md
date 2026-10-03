# Sample DOE run folder: `R005` (design pitch, J = 0.6, n = 10 1/s)

Layout matches what `run/doe/run_doe_case.sh` writes to `run/results/runs/RID/`. It was built from
the RunPod sweep case `C_p0_J0.6` (M3 mesh, 1,161,568 cells), because no DOE-format run exists yet.

## Real vs emulated
| File | Status |
|---|---|
| `row.csv` | **real** (results row of C_p0_J0.6, renamed to R005). Note: from the earlier post-processing version, so `converged` = `yes` (residual stop) instead of the DOE values `forces`/`residuals`/`no`, and KT/KQ are last-iteration values rather than the last-100 mean (difference < 0.01 %) |
| `mesh_quality.txt`, `log.checkMesh` | **real**. This mesh shows "Failed 1 mesh checks" (3 faces skewness > 4); DOE meshes use a tighter setting and must show "Mesh OK" |
| `postProcessing/forces/0/{force,moment}.dat` | **real** (OpenFOAM v2412 format, every 5 iterations) |
| `postProcessing/residuals/`, `postProcessing/yPlus/` | **real** |
| `VTK/` | **real** `foamToVTK -patches propeller` output (multiblock: `.vtm` → `boundary/propeller.vtp`), fields p, U, k, omega, nut, wallShearStress, yPlus |
| `propeller.stl` | **real** (design-pitch surface) |
| `log.*` | **real** |
| `postProcessing/sampleCloud/356/cloud_EMULATED.csv` | **EMULATED**: interpolated from the run's full fields with VTK (cell data → point data, then probe). Values are physically real; the **file name and column naming are not OpenFOAM's** |

## What the real `sampleCloud` output will look like
- Dictionary: `run/doe/sampleCloud` (`type sets; setFormat csv; fields (U p k omega nut);` cloud of 16,360 points).
- Written by `postProcess -latestTime -func sampleCloud` into `postProcessing/sampleCloud/<latestTime>/`.
- OpenFOAM's exact file names and header conventions for the CSV set writer (one file or one per field
  type; vector components as `U_0..U_2` or similar) are **confirmed only by the first real run**.
  A robust converter should glob `postProcessing/sampleCloud/*/*.csv`, read columns by header name,
  and join files on `x,y,z`.
- **Missing points:** OpenFOAM skips cloud points that are not inside any cell. About 1,510–1,550 of the
  16,360 points lie inside the hub, shaft or blades, and the exact set changes slightly with pitch.
  The emulated file has 14,845 rows. Map rows back to `design/cloud_points.csv` by coordinates
  (6 decimals) and keep a validity mask.

## Units and conventions
- Coordinates in m; propeller axis = x; inflow from +x towards −x (U_inlet = −J·n·D in x).
- U in m/s (absolute frame), **p kinematic** (m²/s²; multiply by ρ = 998.99 for Pa), k in m²/s², omega in 1/s, nut in m²/s.
- Rotation: MRF about +x at ω = 2πn; thrust is positive Fx; torque is |Mx| about the origin.
