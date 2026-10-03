"""Join pod results (results_doe.csv) into the design -> doe_results.csv; report progress."""
import csv, os, sys
here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'run', 'results', 'results_doe.csv')
design = list(csv.DictReader(open(os.path.join(here, '..', 'design', 'design_128.csv'))))
res = {r['case']: r for r in csv.DictReader(open(src))} if os.path.exists(src) else {}
out = []
for d in design:
    r = res.get(d['run_id'])
    if d['status'] == 'todo' and r:
        d.update(status='done' if r['status'] == 'ok' else 'failed', KT=r['KT'], KQ10=r['KQ10'], eta0=r['eta0'])
        d['iters'], d['converged'], d['cells'] = r['iters'], r['converged'], r['cells']
    out.append(d)
keys = list(dict.fromkeys(k for d in out for k in d))
with open(os.path.join(here, '..', 'design', 'doe_results.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(out)
n = {s: sum(1 for d in out if d['status'] == s) for s in ('done', 'todo', 'failed')}
print(f"done {n['done']}/128, todo {n['todo']}, failed {n['failed']} -> doe_results.csv")
