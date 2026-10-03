# Prompts for running the DOE with Claude Code

Open a terminal in the copied folder, start `claude`, and paste these one at a time.
Claude reads `CLAUDE.md` automatically; `README.md` has the full procedure.

## 1. Check the machine
```
Read README.md and CLAUDE.md. Check whether this machine meets the requirements in section 3:
CPU cores (physical and logical), RAM, free disk, Ubuntu version, whether OpenFOAM v2412,
python3-numpy, rsync and flock are installed. Report what is missing. Do not install anything yet.
```

## 2. Install
```
Install what is missing using run/doe/install_ubuntu.sh (ask me before using sudo).
Confirm INSTALL_OK and that simpleFoam, snappyHexMesh, foamDictionary and mpirun are available.
```

## 3. Smoke test
```
Run the smoke test from README step 2 (ONLY=R127). When it finishes, check summary.txt,
mesh_quality.txt ("Mesh OK"), log.forceWatch ("CONVERGED"), the sampleCloud output and
results_doe.csv. Report the run time, KT, 10KQ and eta0, and fix anything that failed before going on.
```

## 4. Full DOE
```
Start the full DOE from README step 3, detached so it survives closing the terminal, sequential,
using all physical cores. Check that the first run starts, then tell me how to monitor it.
```

## 5. Progress and converged cases
```
Show DOE progress: runs finished, failed (with reason), and the remaining time estimate.
List only the converged and mesh-qualified cases with tools/list_converged.py.
```

## 6. Resume after an interruption
```
The DOE was interrupted. Check results/progress.log and results/runs for the last finished run,
remove the partial case folder of the interrupted run if any, and restart run_doe.sh (it skips
finished runs).
```

## 7. Analysis when done
```
Merge the results into the design (tools/merge_results.py). Plot KT, 10KQ and eta0 against J,
coloured by pitch and grouped by n, overlay the SVA open-water data at design pitch for n = 10 and
15 1/s (references/SVA_PPTC/report3752.txt), and report the agreement. Keep the 13 test runs separate.
```
