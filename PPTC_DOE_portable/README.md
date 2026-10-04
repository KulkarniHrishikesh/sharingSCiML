# PPTC propeller open-water DOE: portable run kit

Everything needed to run the 128-run PPTC design on any Linux machine, plus the references and
all previous results. Copy this whole folder, follow the steps below, or open it in Claude Code
and use the prompts in `PROMPTS_FOR_CLAUDE.md`.

**Status when packaged (3 Oct 2026):** 15 of 128 runs done (from the RunPod sweep), 113 to run.

---

## 1. What the DOE is

| Factor | Range | Notes |
|---|---|---|
| Advance coefficient J | 0.35 – 1.25 | inlet velocity U = J·n·D, D = 0.25 m |
| Blade pitch change | −5° to +5° | rotation of each blade about its spindle axis; geometry generated per run |
| Shaft speed n | 10 – 15 1/s | SVA measured the design pitch at n = 10 and 15 1/s |

- 113 new points: augmented maximin Latin hypercube around the 15 existing runs (seed 20261003).
- 13 runs flagged `split=test`: hold them out of surrogate training.
- `priority`: run order (farthest-point), so any number of completed runs is spread over the space.
- Numerics (validated against SVA open-water data): M3 mesh (snappyHexMesh, about 1.16M cells,
  3 prism layers), k-ω SST, steady MRF, `simpleFoam`, water at 15.6 °C.
- **Mesh qualification:** a run is solved only if `checkMesh` reports `Mesh OK`.
- **Convergence:** stop when thrust and torque each change < 0.1 % between successive
  100-iteration windows (minimum 300, maximum 1500 iterations). KT and 10KQ are the mean of the
  last 100 iterations.

## 2. Folder layout

| Path | Contents | Needed on the run machine? |
|---|---|---|
| `run/` | **the working directory**: case template, design-pitch STL, run scripts, OpenFOAM .debs | **yes** |
| `run/doe/design_128.csv` | the design (status, split, J, pitch, n, priority, results of done runs) | yes |
| `run/doe/run_doe.sh` | queue: runs all `todo` rows in priority order; resumable | yes |
| `run/doe/run_doe_case.sh` | one run: geometry → mesh → checkMesh gate → solve → outputs | yes |
| `run/doe/install_ubuntu.sh` | installs OpenFOAM v2412 + python3-numpy (Ubuntu 22.04) | yes, unless already installed |
| `design/` | copy of the design, design plot, summary, sampling-cloud coordinates | no (reference) |
| `tools/` | DOE generation, pitch measurement, merging, listing, analysis scripts | optional |
| `references/` | SVA reports 3752–3754, PPTC CAD (STEP, PFF), LDV data, original case notes | optional |
| `previous_cases/` | 17-run sweep + 4 reruns: results, logs, fields (3.2 GB), plots | optional |
| `data_manifest.csv`, `fetch_data.sh` | list (size, SHA-256) and downloader for the large archives on Cloudflare R2 | optional |
| `sample_run/R005/` | example of one run's output folder (real files + an emulated point-cloud sample), for writing converters | optional |

## 3. Requirements on the run machine

- Linux x86_64. Tested setup: Ubuntu 22.04 with OpenFOAM v2412 (OpenCFD) and Open MPI 4.1.
- CPU: the scripts use all physical cores by default. Reference speed: 16 cores (AMD EPYC 9655)
  → about 7–9 min per run.
- RAM: 16 GB or more (M3 meshing on 16 ranks peaks at a few GB).
- Disk: about 10 GB free while running. Heavy files are deleted after each run; about 15 MB is kept per run.
- `python3` with `numpy`, `rsync`, `flock`, `mpirun`.

## 4. Step by step

### Step 0: copy the folder
```bash
rsync -a --progress PPTC_DOE_portable/ user@machine:~/PPTC_DOE_portable/
# minimum: only the run/ folder is required (76 MB); previous_cases/ is 3.2 GB
```

### Step 1: install (skip if OpenFOAM v2412 is already installed)
```bash
cd ~/PPTC_DOE_portable
sudo bash run/doe/install_ubuntu.sh        # prints INSTALL_OK at the end
```
- It tries the official OpenCFD repository first and falls back to the bundled packages in `run/debs/`
  (Ubuntu 22.04 only). The fallback exists because dl.openfoam.com blocked a RunPod datacenter.
- OpenFOAM installed somewhere else: `export FOAM_BASHRC=/path/to/OpenFOAM-v2412/etc/bashrc`.

### Step 2: smoke test (one run, about 10 min on 16 cores)
```bash
cd ~/PPTC_DOE_portable/run
ONLY=R127 bash doe/run_doe.sh
cat results/runs/R127/summary.txt            # status=ok expected
cat results/runs/R127/mesh_quality.txt       # must contain "Mesh OK"
tail -3 results/runs/R127/log.forceWatch     # "CONVERGED at it ..."
ls results/runs/R127/postProcessing/sampleCloud/*/  # point-cloud CSV: confirm file names and header (see sample_run/)
cat results/results_doe.csv
```

### Step 3: full DOE (sequential, resumable)
```bash
cd ~/PPTC_DOE_portable/run
(setsid bash doe/run_doe.sh > doe.log 2>&1 < /dev/null &)       # or run inside tmux/screen
tail -f results/progress.log                                     # one line per finished run
```
- Re-running the same command resumes: runs with `results/runs/RID/DONE` (or `FAILED`) are skipped.
- Options: `NP=8` (MPI ranks), `JOBS=2` (concurrent runs), `ONLY=R016,R017` (subset), `DRY=1` (print only).
- To stop: `pkill -f run_doe.sh; pkill -f simpleFoam; pkill -f snappyHexMesh`. The current run is lost; finished runs are kept.

### Step 4: list converged cases and merge into the design
```bash
cd ~/PPTC_DOE_portable
python3 tools/list_converged.py              # converged + Mesh OK runs only
python3 tools/merge_results.py               # -> design/doe_results.csv (done/todo/failed per run)
```
`merge_results.py` needs only Python's standard library. The other tools need `numpy`, and the
plotting tools need `matplotlib` and `scipy`.

### Step 5: what each run keeps (`run/results/runs/RID/`)
| File | Content |
|---|---|
| `row.csv` | KT, 10KQ, eta0, iterations, convergence flag, cells, y+ |
| `mesh_quality.txt`, `log.checkMesh` | mesh qualification |
| `postProcessing/forces/` | thrust/torque history every 5 iterations |
| `VTK/` | propeller surface: p, wallShearStress, yPlus |
| `postProcessing/sampleCloud/` | U, p, k, omega, nut on the fixed cloud (`design/cloud_points.csv`, 16,360 points); CSV with header; about 1,510–1,550 points inside the body are skipped, so join on x,y,z |
| `propeller.stl` | geometry used for that pitch |
| `log.*`, `summary.txt` | logs and one-line status |

## 5. Expected time

| Physical cores | Per run (approx.) | 113 runs |
|---|---|---|
| 16 | 7–9 min | 13–17 h |
| 8 | 13–17 min | 25–32 h |
| 32 | 5–7 min (communication limited) | 10–13 h |

## 6. Known issues and checks

- **Mesh qualification:** the meshing quality setting `maxBoundarySkewness` was tightened from 20 to 4
  so meshes pass `checkMesh`. The earlier 15 runs used meshes with 1–3 faces above skewness 4
  ("Failed 1 mesh checks"); their results are kept but are not mesh-qualified by this rule.
  If many new runs fail the gate, see `log.snappyHexMesh` and relax `maxInternalSkewness` or
  `maxNonOrtho` in `run/template/system/snappyHexMeshDict.tmpl`.
- **Point-cloud sampling** (`run/doe/sampleCloud`: OpenFOAM `sets`/`cloud`, CSV, fields U p k omega nut) has
  not been executed yet. KT/KQ do not depend on it, but the field surrogate does: confirm the smoke test
  writes it (and check the file names and header against `sample_run/README_SAMPLE.md`) before
  queuing the other 112 runs.
- **Accuracy:** at design pitch, thrust is 3–9 % below SVA and torque within 3 % (J 0.4–1.0).
  M2→M3 changes KT by about 2 %, so results are not fully mesh-independent.
- Pitch changes and n between 10 and 15 1/s have no experimental data; the n = 15 1/s design-pitch
  corner can be checked against SVA report 3752.
- `run_doe_case.sh` adds `--allow-run-as-root` to `mpirun` only when running as root.

## 7. Previous results (`previous_cases/`)

| Item | Summary |
|---|---|
| Mesh study (design pitch, J = 0.8021) | M1 147k: KT −4.2 %, 10KQ −2.7 %; M2 589k: −2.0 %, +4.5 %; M3 1.16M: −3.4 %, +2.3 % vs SVA |
| Sweep (M3, pitch −4/0/+4 × J 0.4–1.2, n = 10) | `sweep_17runs/results.csv`, plot `analysis/pptc_sweep_curves.png` |
| Convergence check | all 17 runs converged within 0.25 % (one oscillating case averaged); `analysis/convergence.csv` |
| Reruns with force-based stopping | `rerun_4cases/`: identical to the original within 0.01 % |
| Archives | `light*.tgz`: force histories, surface VTK, logs; `fields*.tgz`: final fields and meshes |

## 8. References (`references/`)

- SVA Potsdam, *Potsdam Propeller Test Case (PPTC) Open Water Tests*, report 3752 (KT/10KQ tables
  at n = 10 and 15 1/s; text extract `report3752.txt`); reports 3753 (cavitation) and 3754 (LDV).
- PPTC VP1304 geometry: STEP (with and without blade-hub gap), parametric PFF file, data sheet.
- `references/cad/PPTC_geo_no_gap.stp`: source of `run/stl/prop_pitch0.stl` (gmsh surface, 0.9 mm on
  blades, `tools/stlgen.py`).
- `references/original_PPTC_case_notes.md`: original case set-up notes (solver research, conditions).

## 9. Large data on Cloudflare R2

Files over GitHub's 100 MB limit (the previous-case field archives, and in future the DOE run outputs)
are kept in the private R2 bucket `sharingsciml-data`. `data_manifest.csv` lists each file's path,
size and SHA-256; `fetch_data.sh` downloads and verifies them.

1. Get an R2 API token with *Object Read* (or *Read & Write*) on the bucket from the bucket owner
   (Cloudflare dashboard → R2 → Manage API tokens). You need the Access Key ID, the Secret Access Key
   and the endpoint `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.
2. Configure rclone **in a terminal** (keep keys out of chats, scripts and this repository):
   ```bash
   rclone config create r2 s3 provider=Cloudflare access_key_id=<KEY_ID> \
     secret_access_key=<SECRET> endpoint=https://<ACCOUNT_ID>.r2.cloudflarestorage.com \
     acl=private no_check_bucket=true
   chmod 600 ~/.config/rclone/rclone.conf
   rclone ls r2:sharingsciml-data/pptc      # bucket-scoped tokens cannot list all buckets; this works
   ```
3. Download: `bash fetch_data.sh` (all) or `bash fetch_data.sh fields3` (a subset); `LIST=1` previews.
4. Uploading new large outputs (e.g. finished DOE runs):
   `rclone copy run/results r2:sharingsciml-data/pptc/doe_results --progress`, then add the files to
   `data_manifest.csv` (`shasum -a 256 <file>` or `sha256sum <file>`).
