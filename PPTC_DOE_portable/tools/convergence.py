"""Convergence assessment of the PPTC sweep from force/moment and residual histories."""
import os, glob, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "..", "previous_cases", "sweep_17runs", "light", "runs")  # extract light.tgz there first
OUT = os.path.join(HERE, "..", "previous_cases", "analysis"); os.makedirs(OUT, exist_ok=True)
rho, D, n = 998.99, 0.25, 10.0

def series(path):
    a = []
    for l in open(path):
        if l.startswith("#"): continue
        v = l.replace("(", " ").replace(")", " ").split()
        a.append((float(v[0]), float(v[1])))
    return np.array(a)

def residuals(path):
    hdr = None; rows = []
    for l in open(path):
        if l.startswith("# Time"):
            hdr = l[1:].split()
        elif not l.startswith("#"):
            rows.append(l.split())
    idx = {h: i for i, h in enumerate(hdr)}
    out = {}
    for f in ("Ux", "p", "k", "omega"):
        j = idx.get(f + "_initial")
        if j is not None:
            out[f] = np.array([[float(r[0]), float(r[j])] for r in rows if len(r) > j])
    return out

def window_metrics(t, y):
    """Metrics on the last 200 iterations (or what exists)."""
    tend = t[-1]
    w2 = (t > tend - 200)
    a = (t > tend - 100); b = (t > tend - 200) & (t <= tend - 100)
    mean = y[a].mean()
    dmean = 100 * (y[a].mean() - y[b].mean()) / abs(mean) if b.any() else np.nan
    p2p = 100 * (y[w2].max() - y[w2].min()) / abs(mean)
    slope = np.polyfit(t[w2], y[w2], 1)[0] if w2.sum() > 3 else np.nan
    trend100 = 100 * slope * 100 / abs(mean)
    return mean, dmean, p2p, trend100

def verdict(vals):
    worst = max(abs(v) for v in vals if np.isfinite(v))
    if worst < 0.25: return "converged", worst
    if worst < 1.0: return "nearly", worst
    return "not converged", worst

cases = sorted(d for d in os.listdir(RUNS) if os.path.isdir(os.path.join(RUNS, d)))
rows = []
hist = {}
for c in cases:
    fp = glob.glob(os.path.join(RUNS, c, "postProcessing/forces/*/force.dat"))
    mp = glob.glob(os.path.join(RUNS, c, "postProcessing/forces/*/moment.dat"))
    rp = glob.glob(os.path.join(RUNS, c, "postProcessing/residuals/*/solverInfo.dat"))
    if not fp: continue
    F = series(fp[0]); M = series(mp[0]); M[:, 1] = np.abs(M[:, 1])
    KT = F[:, 1] / (rho * n**2 * D**4); KQ = 10 * M[:, 1] / (rho * n**2 * D**5)
    t = F[:, 0]
    mT, dT, pT, sT = window_metrics(t, KT)
    mQ, dQ, pQ, sQ = window_metrics(M[:, 0], KQ)
    res = residuals(rp[0]) if rp else {}
    fin = {k: v[-1, 1] for k, v in res.items()}
    v, worst = verdict([dT, pT, sT, dQ, pQ, sQ])
    rows.append(dict(case=c, iters=int(t[-1]), KT=mT, KQ10=mQ, dKT=dT, ppKT=pT, trKT=sT, dKQ=dQ, ppKQ=pQ, trKQ=sQ,
                     res_U=fin.get("Ux", np.nan), res_p=fin.get("p", np.nan), res_k=fin.get("k", np.nan),
                     res_w=fin.get("omega", np.nan), verdict=v, worst=worst))
    hist[c] = (t, KT, M[:, 0], KQ, res)

# ---- table
hdr = ["case", "iters", "KT", "KQ10", "dKT", "ppKT", "trKT", "dKQ", "ppKQ", "trKQ", "res_U", "res_p", "res_k", "res_w", "verdict", "worst"]
with open(os.path.join(OUT, "convergence.csv"), "w") as f:
    w = csv.writer(f); w.writerow(hdr)
    for r in rows: w.writerow([r[h] if not isinstance(r[h], float) else f"{r[h]:.5g}" for h in hdr])
print(f"{'case':<16}{'its':>5} {'KT':>7} {'10KQ':>7} | {'dKT%':>6} {'ppKT%':>6} {'trKT%':>6} | {'dKQ%':>6} {'ppKQ%':>6} {'trKQ%':>6} | {'res U':>8} {'res p':>8} | verdict")
for r in rows:
    print(f"{r['case']:<16}{r['iters']:>5} {r['KT']:7.4f} {r['KQ10']:7.4f} | {r['dKT']:6.2f} {r['ppKT']:6.2f} {r['trKT']:6.2f} | {r['dKQ']:6.2f} {r['ppKQ']:6.2f} {r['trKQ']:6.2f} | {r['res_U']:8.1e} {r['res_p']:8.1e} | {r['verdict']} (worst {r['worst']:.2f}%)")

# ---- histories: KT and 10KQ normalised by their final-window mean
fig, axs = plt.subplots(4, 5, figsize=(18, 12), dpi=130, sharex=True)
for ax, c in zip(axs.ravel(), cases):
    if c not in hist: ax.axis("off"); continue
    t, KT, tq, KQ, res = hist[c]
    r = next(x for x in rows if x["case"] == c)
    ax.plot(t, 100 * (KT / r["KT"] - 1), lw=0.9, label="$K_T$")
    ax.plot(tq, 100 * (KQ / r["KQ10"] - 1), lw=0.9, label="$10K_Q$")
    ax.axhspan(-0.25, 0.25, color="g", alpha=0.12)
    ax.set_ylim(-5, 5); ax.grid(alpha=0.3)
    ax.set_title(f"{c}  [{r['verdict']}]", fontsize=9)
    ax2 = ax.twinx()
    for k, col in (("Ux", "0.5"), ("p", "k")):
        if k in res: ax2.semilogy(res[k][:, 0], res[k][:, 1], c=col, lw=0.5, alpha=0.6)
    ax2.set_ylim(1e-7, 1); ax2.tick_params(labelsize=6)
for ax in axs.ravel()[len(cases):]: ax.axis("off")
axs[0, 0].legend(fontsize=7, loc="upper right")
fig.supxlabel("Iteration"); fig.supylabel("Deviation from final 100-iteration mean (%)   [green band: +-0.25%]")
fig.suptitle("PPTC sweep: thrust/torque convergence (left axis) and residuals Ux (grey), p (black) (right axis, log)", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "pptc_convergence_histories.png"))
print("wrote", os.path.join(OUT, "pptc_convergence_histories.png"))
