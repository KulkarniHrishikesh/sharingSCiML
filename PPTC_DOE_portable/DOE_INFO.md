# PPTC open-water DOE: information and pipeline status

Status as of 3 Oct 2026: **15 of 128 runs done, 113 to run. None of the 113 has been started**
(no RunPod CPU capacity; no other machine used yet).

## 1. Case
- Propeller: SVA Potsdam PPTC VP1304, D = 0.25 m, 5 blades, P0.7/D = 1.635, right-handed.
- Condition: open water, non-cavitating, water at 15.6 °C (ρ = 998.99 kg/m³, ν = 1.124e-6 m²/s).
- Model: OpenFOAM v2412, `simpleFoam`, steady MRF (rotating cylinder zone r = 0.145 m), k-ω SST,
  M3 mesh (snappyHexMesh, about 1.16M cells, 3 prism layers, blade surface level 6).
- Outputs per run: KT, 10KQ, η0 (mean of last 100 iterations), thrust/torque history, propeller-surface
  fields (p, wall shear stress, y+), U, p, k, ω, νt on a fixed 16,360-point cloud (CSV; about 1,510–1,550
  points inside the body are skipped, so rows must be joined to `design/cloud_points.csv` on x,y,z).
- Example output folder: `sample_run/R005/` (real files plus an emulated point-cloud CSV).

## 2. Design (`design/design_128.csv`)
| Item | Value |
|---|---|
| Runs | 128 = 15 done (RunPod sweep, M3) + 113 todo |
| Factors (todo runs) | J 0.353–1.249, pitch change −4.93° to +4.93°, n 10.01–15.00 1/s |
| Factor ranges (design) | J 0.35–1.25, pitch −5° to +5°, n 10–15 1/s |
| Method | augmented maximin Latin hypercube, seed 20261003, best of 400 candidates; every new point in its own 1/113 stratum per factor |
| Space filling | min distance (normalised) 0.089 overall, 0.091 new-to-existing; centred L2 discrepancy 0.00017 |
| Test split | 13 todo runs, farthest-point selection (spread over the whole space) |
| Run order | `priority` 1–113, farthest-point from the done runs; first 10: R127, R110, R101, R087, R074, R085, R067, R066, R105, R106 |
| Geometry | each run has its own pitch → own STL and mesh; measured pitch change ≈ 0.944 × nominal (`pitch_meas_deg`) |

Columns: `run_id, status, source, split, J, pitch_deg, n_rps, U_inlet, omega, KT, KQ10, eta0, pitch_meas_deg, pitch07_deg, priority`.

## 3. Pipeline per run (`run/doe/run_doe_case.sh`)
1. Copy template, set inlet velocity U = −J·n·D, MRF ω = 2πn.
2. Geometry: `pitch_np.py` rotates each blade of `stl/prop_pitch0.stl` about its spindle axis.
3. Mesh: blockMesh → surfaceFeatureExtract → decomposePar → snappyHexMesh (parallel) → topoSet → checkMesh.
4. **Gate:** continue only if checkMesh reports `Mesh OK`, otherwise `checkmesh_failed` (not solved).
5. Solve: `simpleFoam` (parallel) with `force_watch.py` stopping at ΔKT, ΔKQ < 0.1 % between 100-iteration windows (min 300, max 1500).
6. Post: `post_case.py` → row in `results/results_doe.csv`; reconstructParMesh, reconstructPar, foamToVTK (propeller), postProcess `sampleCloud`.
7. Keep light outputs in `results/runs/RID/`, delete the case folder, mark `DONE` or `FAILED`.

Queue (`run/doe/run_doe.sh`): todo rows in priority order, skips `DONE`/`FAILED`, sequential by default (all physical cores), resumable.

## 4. Pipeline readiness
| Stage | Status | Evidence |
|---|---|---|
| Design generation, run order, test split | **Done, verified** | stratification check OK; dry-run queue lists 113 runs in priority order |
| Geometry (`pitch_np.py`) | **Verified locally** | matches the pyvista version to 1.8 µm; watertight (0 open edges) for +4°, −4.47°, +3.66°; 1.5 s per STL |
| Template, inlet/MRF settings | **Verified on pod** | same template as the 17-run sweep and 4 reruns |
| M3 meshing | **Verified on pod, with one change untested** | 17 runs meshed OK; `maxBoundarySkewness` tightened from 20 to 4 for the gate, not yet run |
| checkMesh gate | **Untested** | grep for `Mesh OK` in the parallel checkMesh log; earlier M3 meshes failed 1 check (1–3 faces skewness > 4) |
| Solver + force-based stop | **Verified on pod** | 4 reruns stopped automatically at 417–623 iterations; results within 0.01 % of 1000-iteration runs |
| `post_case.py` (KT/KQ, convergence flag) | **Verified on pod and locally** | rerun rows; header option tested locally |
| reconstructParMesh, reconstructPar, propeller VTK | **Verified on pod** | sweep and reruns |
| Point-cloud sampling (`sampleCloud`) | **Untested (critical for the field surrogate)** | `sets`/`cloud`, `setFormat csv`, fields U p k omega nut; not yet executed. KT/KQ do not depend on it, but the field dataset does: confirm output in the smoke test before queuing the rest |
| `run_doe_case.sh` end to end | **Untested** | new wrapper: output layout, flock-protected results file, cleanup, DONE/FAILED markers |
| `run_doe.sh` queue | **Verified locally (dry run)** | ordering, subset (`ONLY`), skip of finished runs |
| OpenFOAM install | **Packages verified on pod; script untested** | the bundled .debs installed and ran on the pod; `install_ubuntu.sh` wraps that procedure |
| Cost guard (RunPod) | **Previous version verified; DOE version untested** | v2 stopped the pod at sweep end; DOE version adds rsync and SSH auto-discovery |
| `merge_results.py`, `list_converged.py` | **Verified locally** | merge reports 15/128 done; listing waits for results |

**What closes the untested items:** the one-run smoke test (README step 2, about 10 min on 16 cores)
exercises the new meshing setting, the checkMesh gate, point-cloud sampling and the full
`run_doe_case.sh` wrapper before the remaining 112 runs are queued.

## 5. Cost and time
- 16 physical cores: about 7–9 min per run → about 13–17 h for 113 runs.
- RunPod 32-vCPU CPU pod at $0.96/h: about $13–16 for all 113. With the $10 budget, about 70–85 runs
  in priority order (space-filling at any stopping point).

## 6. Known limits
- Thrust 3–9 % below SVA at design pitch (torque within 3 % for J 0.4–1.0); M2→M3 changes KT by about 2 %.
- No experimental data for pitch changes or for n between 10 and 15 1/s (SVA: design pitch, n = 10 and 15 1/s).
- The 15 done runs used meshes that are not qualified under the new gate (1–3 faces skewness > 4).
