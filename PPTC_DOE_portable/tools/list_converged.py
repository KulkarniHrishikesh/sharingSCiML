"""List only converged, mesh-qualified DOE runs (and count the rest).
Converged = force-based stop triggered (thrust and torque change < 0.1 % between successive
100-iteration windows). Mesh-qualified = checkMesh reported "Mesh OK".
Usage: python3 tools/list_converged.py [path/to/results_doe.csv]"""
import csv, os, sys
here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'run', 'results', 'results_doe.csv')
runs = os.path.join(os.path.dirname(src), 'runs')
if not os.path.exists(src):
    sys.exit(f"no results yet: {src}")
rows = list(csv.DictReader(open(src)))
def mesh_ok(rid):
    f = os.path.join(runs, rid, 'mesh_quality.txt')
    return os.path.exists(f) and any(l.startswith('Mesh OK') for l in open(f))
conv = [r for r in rows if r['status'] == 'ok' and r['converged'] == 'forces' and mesh_ok(r['case'])]
print(f"{'run':<6}{'J':>8}{'pitch':>8}{'n':>7}{'KT':>9}{'10KQ':>9}{'eta0':>8}{'iters':>7}{'cells':>10}")
for r in sorted(conv, key=lambda r: r['case']):
    print(f"{r['case']:<6}{float(r['J']):8.4f}{float(r['pitch_deg']):8.2f}{float(r['n_rps']):7.2f}{float(r['KT']):9.4f}{float(r['KQ10']):9.4f}{float(r['eta0']):8.4f}{r['iters']:>7}{r['cells']:>10}")
other = len(rows) - len(conv)
print(f"\nconverged and mesh-qualified: {len(conv)}   other (failed / not converged / mesh not qualified): {other}")
