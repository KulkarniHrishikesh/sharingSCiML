#!/bin/bash
# Run all 'todo' rows of design_128.csv. Resumable: finished runs (results/runs/RID/DONE) are skipped.
# Usage: bash run_doe.sh                       # sequential, all physical cores (default)
#        JOBS=2 NP=8 bash run_doe.sh            # 2 concurrent runs x 8 MPI ranks
#        DRY=1 bash run_doe.sh                  # print the commands only
#        ONLY=R016,R017 bash run_doe.sh         # run a subset (smoke test)
ROOT=${PPTC_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}; export PPTC_ROOT=$ROOT
TPC=$(lscpu 2>/dev/null | awk -F: '/Thread\(s\) per core/{print $2+0}' | head -1); TPC=${TPC:-1}
NCPU=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN); JOBS=${JOBS:-1}; NP=${NP:-$(( NCPU / TPC ))}
cd $ROOT; mkdir -p results/runs
DESIGN=$ROOT/doe/design_128.csv
echo "doe start $(date '+%F %T') JOBS=$JOBS NP=$NP" >> results/progress.log
python3 - "$DESIGN" "${ONLY:-}" "$ROOT" <<'E' > results/queue.txt
import csv, sys, os
only = set(filter(None, sys.argv[2].split(',')))
rows = sorted(csv.DictReader(open(sys.argv[1])), key=lambda r: int(r.get('priority') or 999))
for r in rows:
    if r['status'] != 'todo': continue
    if only and r['run_id'] not in only: continue
    d = f"{sys.argv[3]}/results/runs/{r['run_id']}"
    if os.path.exists(d + "/DONE") or os.path.exists(d + "/FAILED"): continue
    print(r['run_id'], r['J'], r['pitch_deg'], r['n_rps'])
E
echo "queued $(wc -l < results/queue.txt) runs" | tee -a results/progress.log
if [ -n "${DRY:-}" ]; then
    awk -v np=$NP '{print "bash doe/run_doe_case.sh", $1, $2, $3, $4, np}' results/queue.txt; exit 0
fi
# job pool: each line -> one run_doe_case.sh invocation
xargs -P $JOBS -L 1 bash -c 'bash '"$ROOT"'/doe/run_doe_case.sh "$0" "$1" "$2" "$3" '"$NP"' >> '"$ROOT"'/results/progress.log 2>&1' < results/queue.txt
echo "sweep end $(date '+%F %T')" >> results/progress.log
