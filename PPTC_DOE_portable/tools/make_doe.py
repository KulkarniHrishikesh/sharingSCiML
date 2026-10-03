"""128-run DOE for the PPTC open-water surrogate: 15 existing M3 runs + 113 new
points from an augmented, space-filling Latin hypercube.

Factors (physical ranges):
    J        advance coefficient           0.35 .. 1.25
    pitch    blade pitch change [deg]      -5   .. +5   (rotation about spindle axis)
    n        shaft speed [1/s]              10   .. 15

Method
  * Existing runs (n = 10, pitch {-4,0,+4}, J {0.4,0.6,0.8021,1.0,1.2}) are kept as fixed points.
  * 113 new points: NCAND scrambled LHS designs (scipy qmc, centred-discrepancy optimised) are
    generated; the one with the largest minimum distance (normalised space) to all other points,
    existing ones included, is kept (maximin augmentation). Each new point is in its own 1/113
    stratum of every factor.
  * 13 of the new points (10 % of 128) are flagged as a held-out test set for the surrogate,
    chosen by farthest-point selection so they cover the space evenly.
Outputs: design_128.csv, doe_summary.txt, doe_pairs.png
"""
import csv, os, math
import numpy as np
from scipy.stats import qmc
from scipy.spatial.distance import cdist, pdist
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(HERE, "..", "design")
SEED, NNEW, NCAND, NTEST = 20261003, 113, 400, 13
LO = np.array([0.35, -5.0, 10.0]); HI = np.array([1.25, 5.0, 15.0])
NAMES = ["J", "pitch_deg", "n_rps"]
D = 0.25

# ---- existing M3 runs (results from the RunPod sweep)
res = {}
for r in csv.DictReader(open(os.path.join(HERE, "..", "previous_cases", "sweep_17runs", "results.csv"))):
    if r["mesh"] == "M3" and r["status"] == "ok":
        res[(round(float(r["J"]), 4), round(float(r["pitch_deg"]), 2), round(float(r["n_rps"]), 2))] = r
existing = np.array(sorted(res.keys()))
assert len(existing) == 15, len(existing)
norm = lambda X: (X - LO) / (HI - LO)
E = norm(existing)

# ---- augmented maximin LHS
rng = np.random.default_rng(SEED)
best, best_score = None, -1
for k in range(NCAND):
    s = qmc.LatinHypercube(d=3, optimization="random-cd", seed=rng.integers(1 << 31)).random(NNEW)
    score = min(pdist(s).min(), cdist(s, E).min())
    if score > best_score:
        best, best_score = s, score
new = LO + best * (HI - LO)
new = np.c_[np.round(new[:, 0], 4), np.round(new[:, 1], 2), np.round(new[:, 2], 2)]

# ---- stratification check (each new point in its own stratum per factor)
strata_ok = all(len(set(np.floor(best[:, j] * NNEW).astype(int))) == NNEW for j in range(3))

# ---- test-set flags
# farthest-point (k-centre) selection: spreads the test runs evenly over the design space
_c = [int(np.argmin(np.linalg.norm(best - 0.5, axis=1)))]          # start nearest the centre
_d = np.linalg.norm(best - best[_c[0]], axis=1)
while len(_c) < NTEST:
    k = int(np.argmax(_d)); _c.append(k); _d = np.minimum(_d, np.linalg.norm(best - best[k], axis=1))
test_idx = set(_c)

# ---- write design
rows = []
for i, (J, p, n) in enumerate(existing):
    r = res[(J, p, n)]
    rows.append(dict(run_id=f"R{i+1:03d}", status="done", source=r["case"], split="train", J=J, pitch_deg=p, n_rps=n,
                     U_inlet=round(-J * n * D, 6), omega=round(2 * math.pi * n, 6), KT=r["KT"], KQ10=r["KQ10"], eta0=r["eta0"]))
order = np.lexsort((new[:, 0], new[:, 1], new[:, 2]))  # run order: by n, then pitch, then J
for k, i in enumerate(order):
    J, p, n = new[i]
    rows.append(dict(run_id=f"R{len(existing)+k+1:03d}", status="todo", source="", split="test" if i in test_idx else "train",
                     J=J, pitch_deg=p, n_rps=n, U_inlet=round(-J * n * D, 6), omega=round(2 * math.pi * n, 6), KT="", KQ10="", eta0=""))
with open(os.path.join(OUTD, "design_128.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# ---- summary
allp = norm(np.array([[r["J"], r["pitch_deg"], r["n_rps"]] for r in rows], float))
disc_new = qmc.discrepancy(best)
summ = [
    f"PPTC DOE: {len(rows)} runs = {len(existing)} existing + {NNEW} new (seed {SEED}, {NCAND} candidate LHS designs)",
    f"Factor ranges: J {LO[0]}-{HI[0]}, pitch {LO[1]:+.0f} to {HI[1]:+.0f} deg, n {LO[2]:.0f}-{HI[2]:.0f} 1/s",
    f"Stratification of new points (one per 1/{NNEW} stratum, every factor): {'OK' if strata_ok else 'FAILED'}",
    f"Min distance among all 128 points (normalised): {pdist(allp).min():.4f}",
    f"Min distance new-to-existing (normalised): {cdist(best, E).min():.4f}",
    f"Centred L2 discrepancy of new points: {disc_new:.5f} (lower is more uniform)",
    f"Test split: {NTEST} new runs flagged 'test' (held out from surrogate training)",
    f"Unique pitch values (each needs its own geometry and mesh): {len(set(new[:,1]))} new + 3 existing",
    f"Reynolds-number note: n 10->15 1/s changes Re(0.7R) by 1.5x at fixed J",
]
open(os.path.join(OUTD, "doe_summary.txt"), "w").write("\n".join(summ) + "\n")
print("\n".join(summ))

# ---- pair plot
X = np.array([[r["J"], r["pitch_deg"], r["n_rps"]] for r in rows], float)
st = np.array([r["status"] for r in rows]); sp = np.array([r["split"] for r in rows])
labels = ["J", "pitch change (deg)", "n (1/s)"]
fig, axs = plt.subplots(3, 3, figsize=(10, 10), dpi=150)
for a in range(3):
    for b in range(3):
        ax = axs[a, b]
        if a == b:
            ax.hist(X[st == "todo", a], bins=12, color="#9aa", edgecolor="k"); ax.set_xlabel(labels[a]); continue
        m1 = (st == "todo") & (sp == "train"); m2 = (st == "todo") & (sp == "test"); m3 = st == "done"
        ax.scatter(X[m1, b], X[m1, a], s=14, c="tab:blue", label="new (train)")
        ax.scatter(X[m2, b], X[m2, a], s=28, marker="^", c="tab:orange", label="new (test)")
        ax.scatter(X[m3, b], X[m3, a], s=40, marker="s", c="k", label="existing (done)")
        ax.set_xlabel(labels[b]); ax.set_ylabel(labels[a]); ax.grid(alpha=0.3)
axs[0, 1].legend(fontsize=7, loc="upper right")
fig.suptitle("PPTC 128-run DOE: augmented maximin Latin hypercube", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(OUTD, "doe_pairs.png"))
