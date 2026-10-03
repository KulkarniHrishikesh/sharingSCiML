"""Append one CSV row with KT, 10KQ, eta0 and convergence data for a finished case."""
import sys, os, re, glob, math
case, J, n, pitch, mesh, status, tmesh, tsolve, npr = sys.argv[1:10]
J, n = float(J), float(n); rho, D = 998.99, 0.25
row = dict(case=os.path.basename(case), mesh=mesh, pitch_deg=pitch, J=J, n_rps=n, status=status,
           cells='', iters='', converged='', T_N='', Q_Nm='', KT='', KQ10='', eta0='',
           KT_drift_pct='', t_mesh_s=tmesh, t_solve_s=tsolve, np=npr, yplus_mean='', yplus_max='')
try:
    row['cells'] = open(os.path.join(case, 'mesh_cells.txt')).read().strip()
except OSError:
    pass
fd = glob.glob(os.path.join(case, 'postProcessing/forces/*/force.dat'))
md = glob.glob(os.path.join(case, 'postProcessing/forces/*/moment.dat'))
def series(path):
    out = []
    for l in open(path):
        if l.startswith('#'): continue
        v = l.replace('(', ' ').replace(')', ' ').split()
        if len(v) >= 4: out.append((float(v[0]), float(v[1])))
    return out
if fd and md:
    F = series(sorted(fd)[-1]); M = series(sorted(md)[-1])
    tl = F[-1][0]
    T = sum(f for it, f in F if it > tl - 100) / max(1, sum(1 for it, f in F if it > tl - 100))
    Q = abs(sum(q for it, q in M if it > tl - 100) / max(1, sum(1 for it, q in M if it > tl - 100)))
    KT = T / (rho * n**2 * D**4); KQ = Q / (rho * n**2 * D**5)
    row.update(T_N=f'{T:.3f}', Q_Nm=f'{Q:.4f}', KT=f'{KT:.5f}', KQ10=f'{10*KQ:.5f}',
               eta0=f'{J/(2*math.pi)*KT/KQ:.5f}' if KQ > 0 else '')
    # drift of thrust over the last 100 iterations (convergence of the integral)
    tail = [f for it, f in F if it >= F[-1][0] - 100]
    if len(tail) > 2 and T != 0:
        row['KT_drift_pct'] = f'{100*(max(tail)-min(tail))/abs(T):.3f}'
log = os.path.join(case, 'log.simpleFoam')
if os.path.exists(log):
    t = open(log, errors='ignore').read()
    its = re.findall(r'^Time = (\d+)', t, re.M)
    row['iters'] = its[-1] if its else ''
    fw = os.path.join(case, 'log.forceWatch')
    row['converged'] = 'forces' if os.path.exists(fw) and 'CONVERGED' in open(fw).read() else ('residuals' if 'SIMPLE solution converged' in t else 'no')
    yp = re.findall(r'patch propeller y\+ : min = [0-9.eE+-]+, max = ([0-9.eE+-]+), average = ([0-9.eE+-]+)', t)
    if yp: row['yplus_max'], row['yplus_mean'] = yp[-1]
hdr = list(row.keys())
csv = os.path.join(os.path.dirname(os.path.dirname(case)), 'results', 'results.csv')
if os.environ.get('ALWAYS_HEADER') or not os.path.exists(csv) or os.path.getsize(csv) == 0:
    print(','.join(hdr))
print(','.join(str(row[k]) for k in hdr))
