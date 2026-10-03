# PPTC open-water DOE

128-run parametric study of the PPTC VP1304 propeller in OpenFOAM v2412 (factors: J, blade pitch
change, shaft speed). 15 runs done, 113 to run. Full procedure: `README.md`. Prompts: `PROMPTS_FOR_CLAUDE.md`.

## Working rules
- Work in `run/`; it is the case root (`PPTC_ROOT` defaults to it). Scripts: `run/doe/run_doe.sh`
  (queue), `run/doe/run_doe_case.sh` (one run).
- Run cases sequentially, in `priority` order, with all physical cores unless told otherwise, so
  that finished runs are complete if the work stops early.
- Always use the M3 mesh. A run may be solved only if `checkMesh` reports `Mesh OK`; otherwise it is
  recorded as `checkmesh_failed` and skipped.
- Convergence is force-based (`run/force_watch.py`), not residual-based. Report only converged,
  mesh-qualified runs (`tools/list_converged.py`) unless asked for the rest.
- Never delete `run/results/` or anything in `previous_cases/`. Partial folders in `run/runs/` may be removed.
- Ask before using sudo or installing packages.
- The 13 `split=test` runs are held out from surrogate training.

## Key facts
- Validation data: SVA report 3752 (`references/SVA_PPTC/report3752.txt`), KT/10KQ vs J at
  n = 10 and 15 1/s, design pitch only.
- At design pitch the M3 setup gives thrust 3–9 % below SVA and torque within 3 % (J 0.4–1.0).
- Geometry per run: `run/doe/pitch_np.py` rotates each blade about its spindle axis (smoothstep
  ramp above the root fillets); the measured pitch change is about 0.944 × nominal.
