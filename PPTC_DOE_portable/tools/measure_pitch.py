import csv, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'run', 'doe'))
import numpy as np
import pitch_np as P
here = os.path.dirname(os.path.abspath(__file__))
_, base = P.read_stl(os.path.join(here, '..', 'run', 'stl', 'prop_pitch0.stl'))
a0 = P.pitch_angle(base)
rows = list(csv.DictReader(open(os.path.join(here, '..', 'design', 'design_128.csv'))))
cache = {}
for r in rows:
    d = float(r['pitch_deg'])
    if d not in cache:
        if d == 0: cache[d] = 0.0
        else:
            q = P.apply(base, d)
            if np.sign(P.pitch_angle(q) - a0) != np.sign(d): q = P.apply(base, -d)
            cache[d] = P.pitch_angle(q) - a0
    r['pitch_meas_deg'] = f"{cache[d]:.3f}"
    r['pitch07_deg'] = f"{a0 + cache[d]:.3f}"
keys = list(rows[0].keys())
with open(os.path.join(here, '..', 'design', 'design_128.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
m = np.array([[float(r['pitch_deg']), float(r['pitch_meas_deg'])] for r in rows])
print(f"base pitch angle at r/R=0.7: {a0:.2f} deg; measured/nominal ratio {np.polyfit(m[:,0], m[:,1], 1)[0]:.3f}; max |meas-nom| {np.abs(m[:,1]-m[:,0]).max():.2f} deg")
