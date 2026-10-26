"""Analysis P (numpy only): confidence intervals that treat runs with an identical price path as ONE cluster.
Runs that repeat the same path (both firms, all rounds) are replicates, not independent samples. The point estimate is unchanged
(mean over all runs); the bootstrap resamples whole clusters of identical-path runs with replacement, so the interval widens
where paths repeat. Compared with the ordinary run-level bootstrap. Main prompt (v1), six agent models.
Writes out/p_path_cluster.json and out/table_cluster.tex."""
import glob
import json
from pathlib import Path

import numpy as np

out = Path(__file__).parent / "out"
MODELS = {"Qwen2.5-7B-Instruct": "Qwen2.5-7B", "Qwen2.5-32B-Instruct": "Qwen2.5-32B", "phi-4": "Phi-4",
          "Mistral-Nemo-12B": "Mistral-Nemo-12B", "claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5"}
B = 10000


def clusters(tag, cond):
    """returns list of (sum_of_run_mean_prices, n_runs) per distinct price path"""
    groups = {}
    for f in sorted(glob.glob(str(out / "llm" / tag / cond / "*.jsonl"))):
        recs = [json.loads(l) for l in open(f) if l.strip()]
        if not recs:
            continue
        key = tuple((r["agent_id"], r["round_id"], r["action"]) for r in recs)
        m = float(np.mean([float(r["action"]) for r in recs]))
        s, n = groups.get(key, (0.0, 0))
        groups[key] = (s + m, n + 1)
    return np.array(list(groups.values()))  # columns: sum, count


def run_level(c):
    # expand to run means is not needed: ordinary bootstrap over runs uses per-run values; rebuild approximately from clusters
    vals = np.concatenate([np.full(int(n), s / n) for s, n in c])
    return vals


def boot_cluster(c, g):
    k = len(c)
    idx = g.integers(0, k, (B, k))
    return c[idx, 0].sum(axis=1) / c[idx, 1].sum(axis=1)


def boot_runs(v, g):
    return g.choice(v, (B, len(v))).mean(axis=1)


res, rows = {}, []
for i, (tag, label) in enumerate(MODELS.items()):
    cells = {k: clusters(tag, k) for k in ("honest", "collude", "honest_silent", "collude_silent")}
    g1, g2 = np.random.default_rng(1500 + i), np.random.default_rng(1600 + i)
    e = {}
    for name, (c1, c0) in {"messages": ("collude", "honest"), "silent": ("collude_silent", "honest_silent")}.items():
        a, b = cells[c1], cells[c0]
        est = a[:, 0].sum() / a[:, 1].sum() - b[:, 0].sum() / b[:, 1].sum()
        d_run = boot_runs(run_level(a), g1) - boot_runs(run_level(b), g1)
        d_cl = boot_cluster(a, g2) - boot_cluster(b, g2)
        e[name] = {"effect": float(est), "ci_runs": [float(np.percentile(d_run, 2.5)), float(np.percentile(d_run, 97.5))],
                   "ci_clusters": [float(np.percentile(d_cl, 2.5)), float(np.percentile(d_cl, 97.5))],
                   "clusters": {k: [int(len(cells[k])), int(cells[k][:, 1].sum())] for k in (c1, c0)}}
    res[tag] = e
    f = lambda v: f"[{v[0]:+.2f}, {v[1]:+.2f}]"
    m, s = e["messages"], e["silent"]
    rows.append(f"{label} & {m['effect']:+.2f} & {f(m['ci_runs'])} & {f(m['ci_clusters'])} & {s['effect']:+.2f} & {f(s['ci_runs'])} & {f(s['ci_clusters'])} \\\\")
    print(label, json.dumps({k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk != 'clusters'} for k, v in e.items()})[:300], flush=True)
tab = ("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{3}{c}{with messages} & \\multicolumn{3}{c}{silent}\\\\\n\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\n"
       "model & effect & CI, runs & CI, path clusters & effect & CI, runs & CI, path clusters \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table_cluster.tex").write_text(tab)
(out / "p_path_cluster.json").write_text(json.dumps(res, indent=1))
