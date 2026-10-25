"""How much independent evidence is enough to calibrate? Held-out FPR and TPR as a function of the number of independent
honest audit batches used to set the threshold (rule: 95th percentile of the calibration batches' statistic).
Usage: python j_evidence_curve.py   (reads out/b_*.jsonl; writes out/j_curve.json, out/fig5_curve.pdf)
"""
import json
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

out = Path(__file__).parent / "out"
SC = ("pricing", "auction", "review")
DET = {"pricing": "cross_run_mi", "auction": "cross_run_mi", "review": "cross_run_mi"}
NS = [3, 5, 8, 12, 20, 40, 80]
res = {}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.3))
for scen in SC:
    def load(label):
        rs = []
        for p in sorted(out.glob(f"b_{scen}_{label}*.jsonl")):
            rs += [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        return rs
    det = DET[scen]
    h = [r["detectors"][det]["statistic"] for r in load("honest")]
    k = [r["detectors"][det]["statistic"] for r in load("keyword")]
    s = [r["detectors"][det]["statistic"] for r in load("sparse")]
    if len(h) < 100:
        continue
    rng = random.Random(1)
    rows = []
    for n in NS:
        fpr, tpr_k, tpr_s = [], [], []
        for _ in range(400):
            idx = list(range(len(h)))
            rng.shuffle(idx)
            cal = sorted(h[i] for i in idx[:n])
            test = [h[i] for i in idx[n:n + 80]] if len(h) >= n + 80 else [h[i] for i in idx[n:]]
            thr = cal[min(len(cal) - 1, int(0.95 * len(cal)))]
            fpr.append(np.mean([x > thr for x in test]))
            tpr_k.append(np.mean([x > thr for x in k]))
            if s:
                tpr_s.append(np.mean([x > thr for x in s]))
        rows.append({"n_cal": n, "fpr_mean": float(np.mean(fpr)), "fpr_sd": float(np.std(fpr)),
                     "tpr_keyword": float(np.mean(tpr_k)), "tpr_sparse": float(np.mean(tpr_s)) if tpr_s else None})
    res[scen] = {"detector": det, "n_honest": len(h), "rows": rows}
    axs[0].errorbar(NS, [r["fpr_mean"] for r in rows], yerr=[r["fpr_sd"] for r in rows], marker="o", ms=3, capsize=1.5, label=scen)
    axs[1].plot(NS, [r["tpr_keyword"] for r in rows], marker="o", ms=3, label=scen)
axs[0].axhline(0.05, ls="--", c="k", lw=0.8)
for a in axs:
    a.set_xscale("log")
    a.set_xticks(NS)
    a.set_xticklabels([str(n) for n in NS])
    a.minorticks_off()
    a.set_xlabel("honest batches used to set the threshold")
axs[0].set_ylabel("held-out FPR (mean, sd)")
axs[0].set_ylim(0, 0.5)
axs[0].legend(frameon=False, fontsize=6)
axs[1].set_ylim(0, 1.05)
axs[1].set_ylabel("detection rate (keyword)")
fig.tight_layout()
fig.savefig(out / "fig5_curve.pdf")
(out / "j_curve.json").write_text(json.dumps(res, indent=1))
for scen, v in res.items():
    print(scen, v["detector"], v["n_honest"])
    for r in v["rows"]:
        print("  ", r)
