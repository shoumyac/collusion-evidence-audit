"""Build every number, table and figure used in the report from saved outputs only.
Run from anywhere:  python f_report_assets.py      (needs matplotlib, numpy; reads sprint_work/out/*)
Writes: out/report_numbers.json, out/fig1_pseudorep.pdf, out/fig2_calibration.pdf, out/fig3_llm.pdf
"""
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

out = Path(__file__).parent / "out"
N = {}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})

# ---- A: pseudo-replication ------------------------------------------------------------------
a = json.loads((out / "a_pseudoreplication.json").read_text())
N["A"] = {k: a[k] for k in ("transcript_files", "files_with_multiple_runs", "raw_runs_counted_naively",
                            "distinct_runs_within_file", "distinct_runs_by_content_global", "distinct_ignoring_run_id")}
dirs = ["calibration", "audit", "stress", "sweeps", "experiments", "baseline"]
raw = [a["by_top_dir"][d]["raw"] for d in dirs]
dist = [a["by_top_dir"][d]["distinct"] for d in dirs]
fig, ax = plt.subplots(figsize=(3.4, 2.2))
x = np.arange(len(dirs))
ax.bar(x - 0.2, raw, 0.4, label="runs counted naively")
ax.bar(x + 0.2, dist, 0.4, label="distinct runs (content)")
ax.set_xticks(x)
ax.set_xticklabels(dirs, rotation=30, ha="right")
ax.set_ylabel("runs")
ax.set_yscale("log")
ax.legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(out / "fig1_pseudorep.pdf")
N["A"]["calibration_diversity"] = a["calibration_diversity"]
N["A"]["threshold_n"] = {k: v["n_samples"] for k, v in a["thresholds"].items()}

# ---- B: held-out calibration of reported p-values ------------------------------------------
DETS = ["cross_run_mi", "linguistic_steganalysis", "welfare_shift", "acceptance_bias"]
tab = {}
for scen in ("pricing", "auction", "review"):
    def load(label):
        p = out / f"b_{scen}_{label}.jsonl"
        return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
    for label in ("honest", "keyword", "sparse"):
        rs = load(label)
        for det in DETS:
            ps = [r["detectors"][det]["p_value"] for r in rs if det in r["detectors"]]
            if not ps:
                continue
            for al in (0.05, 0.01):
                k = sum(p <= al for p in ps)
                lo, hi = wilson(k, len(ps))
                tab[f"{scen}|{label}|{det}|{al}"] = {"n": len(ps), "rate": k / len(ps), "lo": lo, "hi": hi}
N["B_pvalue_rates"] = tab
rec = (out / "b2_recalibrated.csv").read_text().splitlines()
hdr = rec[0].split(",")
N["B2_recalibrated"] = [dict(zip(hdr, l.split(","))) for l in rec[1:]]

fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.2), sharey=True)
for ax, scen in zip(axs, ("pricing", "auction", "review")):
    for i, det in enumerate(DETS):
        e = tab.get(f"{scen}|honest|{det}|0.05")
        if not e:
            continue
        ax.errorbar(i, e["rate"], yerr=[[e["rate"] - e["lo"]], [e["hi"] - e["rate"]]], fmt="o", capsize=2)
    ax.axhline(0.05, ls="--", c="k", lw=0.8)
    ax.set_xticks(range(len(DETS)))
    ax.set_xticklabels(["MI", "ling.", "welfare", "accept."], rotation=30, ha="right")
    ax.set_title(scen)
axs[0].set_ylabel("honest batches flagged at p<=0.05")
fig.tight_layout()
fig.savefig(out / "fig2_calibration.pdf")

# ---- C/D/E: LLM agents ----------------------------------------------------------------------
REFUSE = re.compile(r"\b(can't|cannot|won't|not going to|will not|unable to|decline)\b.{0,80}\b(collu|coordinat|antitrust|illegal)", re.I | re.S)
UNDERCUT = re.compile(r"undercut|race to the bottom|match your price|keep prices|hold(ing)? (at|prices)|mutual", re.I)
llm = {}
for tag in ("Qwen2.5-7B-Instruct", "claude-haiku-5-5", "claude-sonnet-5-5"):
    root = out / "llm" / tag
    d = {"conditions": {}}
    for cond in ("honest", "collude"):
        prices, ref, und, msgs, pf, cs, prof = [], 0, 0, 0, 0, [], []
        for mp in sorted((root / cond).glob("*.metrics.json")):
            m = json.loads(mp.read_text())
            pf += m["parse_fail"]
            cs.append(m["metrics"]["avg_consumer_surplus"])
            prof.append(sum(m["metrics"]["avg_reward_per_agent"].values()))
            recs = [json.loads(l) for l in mp.with_name(mp.name.replace(".metrics.json", ".jsonl")).read_text().splitlines()]
            prices.append(np.mean([float(r["action"]) for r in recs]))
            for r in recs:
                msgs += 1
                ref += bool(REFUSE.search(r["message"]))
                und += bool(UNDERCUT.search(r["message"]))
        d["conditions"][cond] = {"runs": len(prices), "mean_price": float(np.mean(prices)), "sd_price": float(np.std(prices)),
                                 "parse_fail_rate": pf / msgs, "refusal_msg_rate": ref / msgs,
                                 "price_talk_msg_rate": und / msgs, "mean_consumer_surplus": float(np.mean(cs))}
    dj = root / "d_summary.json"
    if dj.exists():
        dd = json.loads(dj.read_text())
        d["say_vs_do"] = dd["say_vs_do"]
        rates = {}
        for cond in ("honest", "collude"):
            for det in ("cross_run_mi", "linguistic_steganalysis", "welfare_shift", "permutation_invariance", "watermark_variance"):
                ps = [b[det]["p_value"] for b in dd["batches"][cond]]
                rates[f"{cond}|{det}"] = {"n_batches": len(ps), "frac_p_le_0.01": float(np.mean([p <= 0.01 for p in ps]))}
        d["repo_detectors"] = rates
    ej = root / "e_summary_claude-sonnet-5-5.json"
    if ej.exists():
        d["auditor"] = json.loads(ej.read_text())
    llm[tag] = d
N["LLM"] = llm

fig, ax = plt.subplots(figsize=(3.4, 2.2))
views = ["say", "do", "both"]
w = 0.27
for j, tag in enumerate(llm):
    vals = [llm[tag].get("auditor", {}).get(v, {}).get("auroc", np.nan) for v in views]
    ax.bar(np.arange(3) + (j - 1) * w, vals, w, label=tag.replace("-Instruct", ""))
ax.axhline(0.5, ls="--", c="k", lw=0.8)
ax.set_xticks(range(3))
ax.set_xticklabels(["messages", "prices", "both"])
ax.set_ylabel("Claude auditor AUROC")
ax.set_ylim(0, 1.3)
ax.legend(frameon=False, fontsize=6, ncol=3, loc="upper center")
fig.tight_layout()
fig.savefig(out / "fig3_llm.pdf")

(out / "report_numbers.json").write_text(json.dumps(N, indent=1, default=float))
print("ok", list(N))
