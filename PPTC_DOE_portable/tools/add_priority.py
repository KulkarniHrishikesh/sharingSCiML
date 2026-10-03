"""Add the 'priority' run-order column to design_128.csv (farthest-point order over the todo runs,
starting away from the completed ones), so any prefix of the queue is space-filling."""
import csv, os
import numpy as np
f = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'design', 'design_128.csv')
rows = list(csv.DictReader(open(f)))
LO = np.array([0.35, -5, 10.]); HI = np.array([1.25, 5, 15.])
Z = (np.array([[float(r['J']), float(r['pitch_deg']), float(r['n_rps'])] for r in rows]) - LO) / (HI - LO)
done = [i for i, r in enumerate(rows) if r['status'] == 'done']; todo = [i for i, r in enumerate(rows) if r['status'] == 'todo']
d = np.min(np.linalg.norm(Z[todo][:, None] - Z[done][None], axis=2), axis=1)
order, rem = [], list(range(len(todo)))
while rem:
    k = rem[int(np.argmax(d[rem]))]; order.append(todo[k]); rem.remove(k)
    d = np.minimum(d, np.linalg.norm(Z[todo] - Z[todo[k]], axis=1))
for r in rows: r['priority'] = ''
for p, i in enumerate(order, 1): rows[i]['priority'] = str(p)
w = csv.DictWriter(open(f, 'w', newline=''), fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('priority written for', len(order), 'runs')
