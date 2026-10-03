"""Stop simpleFoam when thrust and torque have converged.
Criterion: |mean(last W) - mean(previous W)| / |mean| < TOL for both, after MIN iterations.
Stops the run by setting stopAt writeNow in system/controlDict (runTimeModifiable)."""
import sys, os, time, glob, subprocess
case, W, TOL, MIN = sys.argv[1], 100, 1e-3, 300
def series(p):
    out = []
    for l in open(p):
        if l.startswith('#'): continue
        v = l.replace('(', ' ').replace(')', ' ').split()
        if len(v) > 1: out.append((float(v[0]), float(v[1])))
    return out
def dev(s):
    t = s[-1][0]
    a = [y for x, y in s if x > t - W]; b = [y for x, y in s if t - 2 * W < x <= t - W]
    if len(a) < 5 or len(b) < 5: return 1.0
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    return abs(ma - mb) / abs(ma) if ma else 1.0
log = open(os.path.join(case, 'log.forceWatch'), 'w')
while True:
    time.sleep(20)
    f = glob.glob(os.path.join(case, 'postProcessing/forces/*/force.dat'))
    m = glob.glob(os.path.join(case, 'postProcessing/forces/*/moment.dat'))
    if not (f and m): continue
    try:
        F, M = series(f[0]), series(m[0])
    except Exception:
        continue
    if not F or not M: continue
    it = F[-1][0]; dT, dQ = dev(F), dev(M)
    log.write(f'it {it:.0f} dKT {100*dT:.3f}% dKQ {100*dQ:.3f}%\n'); log.flush()
    if it >= MIN and dT < TOL and dQ < TOL:
        log.write(f'CONVERGED at it {it:.0f}; stopping\n'); log.flush()
        subprocess.run(['foamDictionary', '-entry', 'stopAt', '-set', 'writeNow', os.path.join(case, 'system/controlDict')],
                       stdout=log, stderr=log)
        break
