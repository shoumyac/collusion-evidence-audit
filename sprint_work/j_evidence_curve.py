"""How much independent evidence is enough to calibrate? Held-out FPR and TPR as a function of the number of independent
honest audit batches used to set the threshold (rule: threshold = the order statistic at rank r = min(n-1, int(0.95 n)) + 1
of the calibration batches' statistics, i.e. the 95th percentile).

Theory overlay: for a continuous statistic the exceedance probability of a fresh honest batch above the r-th order statistic of
n calibration batches is Beta(n - r + 1, r), mean (n - r + 1) / (n + 1). The plotted empirical curve should follow it.

Usage: python j_evidence_curve.py   (reads out/b_*.jsonl; writes out/j_curve.json, out/fig5_curve.pdf)
"""
import json
import math
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

out = Path(__file__).parent / "out"
SC = ("pricing", "auction", "review")
NS = [3, 5, 8, 12, 20, 40, 80]
LABELS = ("keyword", "sparse", "smart", "adaptive")
DET = "cross_run_mi"


def theory(n):
    r = min(n - 1, int(0.95 * n)) + 1
    a, b = n - r + 1, r
    return a / (a + b), math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))


res = {}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.4))
tpr_all = {l: [] for l in LABELS}
for scen in SC:
    def load(label):
        rs = []
        for p in sorted(out.glob(f"b_{scen}_{label}*.jsonl")):
            rs += [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        return rs
    h = [r["detectors"][DET]["statistic"] for r in load("honest")]
    col = {l: [r["detectors"][DET]["statistic"] for r in load(l)] for l in LABELS}
    rng = random.Random(1)
    rows = []
    for n in NS:
        fpr, tpr = [], {l: [] for l in LABELS}
        for _ in range(400):
            idx = list(range(len(h)))
            rng.shuffle(idx)
            cal = sorted(h[i] for i in idx[:n])
            test = [h[i] for i in idx[n:n + 80]]
            thr = cal[min(len(cal) - 1, int(0.95 * len(cal)))]
            fpr.append(np.mean([x > thr for x in test]))
            for l in LABELS:
                if col[l]:
                    tpr[l].append(np.mean([x > thr for x in col[l]]))
        tm, ts = theory(n)
        rows.append({"n_cal": n, "fpr_mean": float(np.mean(fpr)), "fpr_sd": float(np.std(fpr)), "theory_mean": tm, "theory_sd": ts,
                     **{f"tpr_{l}": (float(np.mean(tpr[l])) if tpr[l] else None) for l in LABELS}})
    res[scen] = {"n_honest": len(h), "n_colluding": {l: len(col[l]) for l in LABELS}, "rows": rows}
    axs[0].plot(NS, [r["fpr_mean"] for r in rows], marker="o", ms=3, label=f"{scen} (empirical)")
    for l in LABELS:
        if col[l]:
            tpr_all[l].append([r[f"tpr_{l}"] for r in rows])
tm = [theory(n) for n in NS]
axs[0].plot(NS, [m for m, _ in tm], "k--", lw=1.0, label="theory: Beta mean")
axs[0].fill_between(NS, [max(0, m - s) for m, s in tm], [m + s for m, s in tm], color="k", alpha=0.10, label="theory: $\\pm$1 sd")
axs[0].axhline(0.05, c="gray", lw=0.6, ls=":")
for l, v in tpr_all.items():
    if v:
        axs[1].plot(NS, np.mean(v, axis=0), marker="o", ms=3, label=l)
for a in axs:
    a.set_xscale("log")
    a.set_xticks(NS)
    a.set_xticklabels([str(n) for n in NS])
    a.minorticks_off()
    a.set_xlabel("honest batches used to set the threshold")
axs[0].set_ylabel("held-out FPR")
axs[0].set_ylim(0, 0.5)
axs[0].legend(frameon=False, fontsize=5.5)
axs[1].set_ylabel("detection rate (mean of 3 scenarios)")
axs[1].set_ylim(0, 1.05)
axs[1].legend(frameon=False, fontsize=6, loc="lower right")
fig.tight_layout()
fig.savefig(out / "fig5_curve.pdf")
(out / "j_curve.json").write_text(json.dumps(res, indent=1))
for scen, v in res.items():
    print(scen, v["n_honest"], v["n_colluding"])
    for r in v["rows"]:
        print("  ", {k: (round(x, 3) if isinstance(x, float) else x) for k, x in r.items()})
