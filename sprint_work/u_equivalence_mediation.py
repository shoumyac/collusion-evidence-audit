"""Analysis U (numpy only, no API calls): is the swap result evidence of EQUIVALENCE, and how much of the collusion effect
runs through communication?

The report says the interval of (intact effect - swapped effect) contains zero for every model. That is absence of evidence for a
difference, not evidence of no difference. Here we add:
  * a two one-sided tests (TOST) equivalence check on D = intact - swapped, with margin delta = 25% (and 50%) of the intact effect,
    declared before looking at the result: equivalent if the 90% bootstrap CI of D lies inside +-delta;
  * the share mediated by communication, D / intact effect, with a bootstrap 95% CI (ratio of resampled run means).
Intact effect = mean(collude) - mean(honest); swapped effect = mean(collude_swap) - mean(honest_swap), on run-mean prices.
Six models under the main prompt, plus Claude under prompt 3 (strict independent honest baseline).
Writes out/u_equivalence_mediation.json and out/table_equivalence.tex.
"""
import glob
import json
from pathlib import Path

import numpy as np

out = Path(__file__).parent / "out" / "llm"
B = 10000
SETS = [("Qwen2.5-7B-Instruct", "Qwen2.5-7B"), ("Qwen2.5-32B-Instruct", "Qwen2.5-32B"), ("phi-4", "Phi-4"), ("Mistral-Nemo-12B", "Mistral-Nemo-12B"),
        ("claude-haiku-5-5", "Claude Haiku 5.5"), ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
        ("claude-haiku-5-5-v3", "Claude Haiku 5.5, prompt 3"), ("claude-sonnet-5-5-v3", "Claude Sonnet 5.5, prompt 3")]


def pm(tag, cond):
    v = []
    for f in sorted(glob.glob(str(out / tag / cond / "*.jsonl"))):
        recs = [json.loads(l) for l in open(f) if l.strip()]
        if recs:
            v.append(float(np.mean([float(r["action"]) for r in recs])))
    return np.array(v)


res, rows = {}, []
for i, (tag, label) in enumerate(SETS):
    cells = {c: pm(tag, c) for c in ("honest", "collude", "honest_swap", "collude_swap")}
    if any(len(v) == 0 for v in cells.values()):
        continue
    g = np.random.default_rng(2400 + i)
    bs = {c: g.choice(v, (B, len(v))).mean(axis=1) for c, v in cells.items()}
    eff_i = bs["collude"] - bs["honest"]
    eff_s = bs["collude_swap"] - bs["honest_swap"]
    D = eff_i - eff_s
    point_i = cells["collude"].mean() - cells["honest"].mean()
    point_s = cells["collude_swap"].mean() - cells["honest_swap"].mean()
    d0 = point_i - point_s
    ci90 = [float(np.percentile(D, 5)), float(np.percentile(D, 95))]
    ci95 = [float(np.percentile(D, 2.5)), float(np.percentile(D, 97.5))]
    share = D / eff_i
    sh = [float(np.percentile(share, 2.5)), float(np.percentile(share, 97.5))]
    r = {"n": {c: int(len(v)) for c, v in cells.items()}, "intact": float(point_i), "swapped": float(point_s), "D": float(d0), "D_ci95": ci95, "D_ci90": ci90,
         "share_mediated": float(d0 / point_i), "share_ci95": sh}
    for frac in (0.25, 0.5):
        delta = frac * abs(point_i)
        r[f"equivalent_{int(frac * 100)}pct"] = {"delta": float(delta), "pass": bool(ci90[0] > -delta and ci90[1] < delta)}
    res[tag] = r
    f = lambda p: "yes" if r[p]["pass"] else "no"
    rows.append(f"{label} & {point_i:+.2f} & {point_s:+.2f} & {d0:+.2f} [{ci95[0]:+.2f}, {ci95[1]:+.2f}] & {100 * r['share_mediated']:+.0f}\\% [{100 * sh[0]:+.0f}, {100 * sh[1]:+.0f}] & {f('equivalent_50pct')} & {f('equivalent_25pct')} \\\\")
    print(label, json.dumps({k: r[k] for k in ("intact", "swapped", "D", "D_ci95", "share_mediated", "share_ci95", "equivalent_25pct", "equivalent_50pct")}), flush=True)

(out.parent / "u_equivalence_mediation.json").write_text(json.dumps(res, indent=1))
tex = ("\\begin{tabular}{lccccc c}\n\\toprule\n set & intact & swapped & D = intact $-$ swapped [95\\% CI] & share through messages [95\\% CI] & equiv.\\ $\\pm$50\\% & equiv.\\ $\\pm$25\\% \\\\\n\\midrule\n"
       + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
(out.parent / "table_equivalence.tex").write_text(tex)
