# Large archives: stored on Cloudflare R2, not in git

GitHub rejects files over 100 MB, so these previous-case archives live in the private Cloudflare R2
bucket `sharingsciml-data` under `pptc/previous_cases/`. Sizes and SHA-256 checksums are in
`../data_manifest.csv`.

| File | Size | Contents |
|---|---|---|
| `sweep_17runs/fields.tgz` | 2.6 GB | final-time fields + meshes of the 17-run sweep (M1/M2/M3 mesh study + 14 parametric runs) |
| `sweep_17runs/light.tgz` | 227 MB | force/moment histories, residuals, propeller-surface VTK and logs of the 17 runs |
| `rerun_4cases/fields3.tgz` | 522 MB | final-time fields + meshes of the 4 force-converged reruns |

Download and verify (needs an rclone remote for the bucket, see `../README.md`, section 9):
```bash
cd PPTC_DOE_portable
bash fetch_data.sh            # all three
bash fetch_data.sh light      # only light.tgz
```
Results tables (`results.csv`), plots and `rerun_4cases/light3.tgz` (45 MB) are in the repository.
Running the DOE itself does not need any of these archives.
