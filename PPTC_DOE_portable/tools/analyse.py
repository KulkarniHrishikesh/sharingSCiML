import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "..", "previous_cases", "sweep_17runs", "results.csv"))))
OUT = os.path.join(HERE, "..", "previous_cases", "analysis"); os.makedirs(OUT, exist_ok=True)

# SVA report 3752, n = 10 1/s polynomial fits (valid 0 <= J <= 1.656)
aKT = [0.956454, -0.347156, -0.584163, 0.525066, -0.156480]
aKQ = [2.086429, -0.908317, -0.748857, 0.857837, -0.298699]
poly = lambda a, J: sum(c * J**i for i, c in enumerate(a))
Jexp = np.array([0, .16, .3217, .4816, .6418, .8021, .9610, 1.1212, 1.2830, 1.4422])
KTexp = np.array([.9545, .8929, .7986, .7014, .6034, .5100, .4202, .3239, .2318, .1404])
KQexp = np.array([2.0801, 1.9412, 1.7370, 1.5463, 1.3669, 1.1994, 1.0399, .8606, .6832, .5029])

ok = [r for r in rows if r["status"] == "ok" and r["KT"]]
for r in ok:
    for k in ("J", "KT", "KQ10", "eta0", "pitch_deg"):
        r[k] = float(r[k])

# ---- mesh study table
ms = sorted([r for r in ok if r["case"].startswith("A_")], key=lambda r: int(r["cells"]))
print("Mesh study (J = 0.8021, design pitch):")
for r in ms:
    print(f"  {r['mesh']}: {int(r['cells']):>9,} cells  KT {r['KT']:.4f} ({100*(r['KT']/0.5100-1):+.1f}%)  "
          f"10KQ {r['KQ10']:.4f} ({100*(r['KQ10']/1.1994-1):+.1f}%)  eta {r['eta0']:.3f}  "
          f"y+ mean {r['yplus_mean']}  iters {r['iters']} conv {r['converged']}  solve {r['t_solve_s']} s")

# ---- sweep curves (M3 runs: C_ cases + A_M3 baseline)
sw = [r for r in ok if r["mesh"] == "M3"]
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), dpi=200)
Jf = np.linspace(0.3, 1.3, 100)
ax[0].plot(Jf, [poly(aKT, j) for j in Jf], "k-", lw=1, label="Exp. fit, design pitch")
ax[0].plot(Jf, [poly(aKQ, j) for j in Jf], "k--", lw=1)
ax[0].plot(Jexp, KTexp, "ko", ms=3); ax[0].plot(Jexp, KQexp, "ks", ms=3)
cols = {0.0: "tab:blue", 4.0: "tab:red", -4.0: "tab:green"}
print("\nSweep (M3):")
for p in sorted(set(r["pitch_deg"] for r in sw)):
    s = sorted([r for r in sw if r["pitch_deg"] == p], key=lambda r: r["J"])
    J = [r["J"] for r in s]; KT = [r["KT"] for r in s]; KQ = [r["KQ10"] for r in s]; eta = [r["eta0"] for r in s]
    c = cols.get(p, "gray")
    ax[0].plot(J, KT, "o-", c=c, label=f"CFD $K_T$, pitch {p:+.0f}$^\\circ$")
    ax[0].plot(J, KQ, "s--", c=c, mfc="none", label=f"CFD $10K_Q$, pitch {p:+.0f}$^\\circ$")
    ax[1].plot(J, eta, "o-", c=c, label=f"CFD, pitch {p:+.0f}$^\\circ$")
    for r in s:
        e = ""
        if p == 0:
            e = f"  exp KT {poly(aKT, r['J']):.4f} ({100*(r['KT']/poly(aKT, r['J'])-1):+.1f}%)  exp 10KQ {poly(aKQ, r['J']):.4f} ({100*(r['KQ10']/poly(aKQ, r['J'])-1):+.1f}%)"
        print(f"  pitch {p:+.0f}  J {r['J']:.3f}  KT {r['KT']:.4f}  10KQ {r['KQ10']:.4f}  eta {r['eta0']:.3f}  iters {r['iters']} conv {r['converged']} drift {r['KT_drift_pct']}%{e}")
etaf = [Jj / (2 * np.pi) * poly(aKT, Jj) / (poly(aKQ, Jj) / 10) for Jj in Jf]
ax[1].plot(Jf, etaf, "k-", lw=1, label="Exp. fit, design pitch")
ax[0].set_xlabel("Advance coefficient J"); ax[0].set_ylabel("$K_T$ (solid), $10K_Q$ (dashed)")
ax[1].set_xlabel("Advance coefficient J"); ax[1].set_ylabel("Open-water efficiency $\\eta_0$")
ax[0].legend(fontsize=6.5, ncol=2); ax[1].legend(fontsize=8)
for a in ax: a.grid(alpha=.3)
ax[0].set_title("PPTC open-water: CFD sweep (M3) vs SVA experiment"); ax[1].set_title("Efficiency")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "pptc_sweep_curves.png"))
print("\nwrote", os.path.join(OUT, "pptc_sweep_curves.png"))
