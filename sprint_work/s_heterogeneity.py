"""Analysis S (numpy, scipy optional): how much of the collusion effect belongs to the wording and the model?

No API calls. Reads the saved transcripts in out/llm and answers three questions with random-effects meta-analysis:
 1. Across the four prompt wordings, how heterogeneous is the collusion effect for each Claude model (tau^2, I^2, Q) and what
    effect should we expect under a NEW wording (prediction interval)?
 2. Across the six agent models under the main prompt, how heterogeneous is the effect?
 3. A crossed 2 x 4 table (Claude model x wording): descriptive share of the variation in the effect due to model, wording and
    their interaction (one cell each, so the interaction is confounded with noise).
It also reports effective sample size read from distinct price paths, and how the prediction interval changes if we add more
runs per wording versus more wordings. Writes out/s_heterogeneity.json and out/table_heterogeneity.tex.
Method: DerSimonian-Laird random effects; prediction interval mu +- t_{k-2} sqrt(tau^2 + se_mu^2) (Higgins, Thompson, Spiegelhalter 2009).
"""
import glob
import json
from pathlib import Path

import numpy as np

try:
    from scipy import stats
    TQ = lambda df: float(stats.t.ppf(0.975, df))
except Exception:  # fallback: two-sided 97.5% t quantiles for small df, normal beyond
    _T = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
    TQ = lambda df: _T.get(int(df), 1.96)

out = Path(__file__).parent / "out"
CLAUDE = {"claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5"}
WORDINGS = [("", "prompt 1"), ("-v2", "prompt 2"), ("-v3", "prompt 3"), ("-v4", "prompt 4")]
ALL6 = {"Qwen2.5-7B-Instruct": "Qwen2.5-7B", "Qwen2.5-32B-Instruct": "Qwen2.5-32B", "phi-4": "Phi-4",
        "Mistral-Nemo-12B": "Mistral-Nemo-12B", "claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5"}


def run_means(tag, cond):
    ms, paths = [], set()
    for f in sorted(glob.glob(str(out / "llm" / tag / cond / "*.jsonl"))):
        recs = [json.loads(l) for l in open(f) if l.strip()]
        if recs:
            ms.append(float(np.mean([float(r["action"]) for r in recs])))
            paths.add(tuple((r["agent_id"], r["round_id"], r["action"]) for r in recs))
    return np.array(ms), len(paths)


def effect(tag):
    h, kh = run_means(tag, "honest")
    c, kc = run_means(tag, "collude")
    d = c.mean() - h.mean()
    se = float(np.sqrt(c.var(ddof=1) / len(c) + h.var(ddof=1) / len(h)))
    return {"d": float(d), "se": se, "n": [len(h), len(c)], "distinct_paths": [kh, kc]}


def dl(d, se):
    """DerSimonian-Laird random effects. Returns dict with mu, se_mu, tau2, Q, I2, prediction interval."""
    d, se = np.asarray(d, float), np.asarray(se, float)
    k = len(d)
    w = 1 / se ** 2
    mu_f = (w * d).sum() / w.sum()
    Q = float((w * (d - mu_f) ** 2).sum())
    tau2 = max(0.0, (Q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    wr = 1 / (se ** 2 + tau2)
    mu = float((wr * d).sum() / wr.sum())
    se_mu = float(np.sqrt(1 / wr.sum()))
    I2 = max(0.0, (Q - (k - 1)) / Q) if Q > 0 else 0.0
    half = TQ(k - 2) * float(np.sqrt(tau2 + se_mu ** 2)) if k > 2 else float("nan")
    return {"k": k, "mu": mu, "se_mu": se_mu, "ci": [mu - 1.96 * se_mu, mu + 1.96 * se_mu], "tau2": float(tau2), "tau": float(np.sqrt(tau2)),
            "Q": Q, "Q_df": k - 1, "I2": float(I2), "pred_interval": [mu - half, mu + half]}


res = {"by_wording": {}, "by_model": {}, "crossed": {}, "projection": {}}
tab = []

# 1. heterogeneity across wordings, per Claude model
eff = {}
for tag, name in CLAUDE.items():
    e = [effect(tag + s) for s, _ in WORDINGS]
    eff[tag] = e
    m = dl([x["d"] for x in e], [x["se"] for x in e])
    m["effects"] = [{"wording": w, **x} for (_, w), x in zip(WORDINGS, e)]
    res["by_wording"][name] = m
    tab.append((name + ", across 4 wordings", m))

# 2. heterogeneity across models, main prompt
e6 = {tag: effect(tag) for tag in ALL6}
m6 = dl([v["d"] for v in e6.values()], [v["se"] for v in e6.values()])
m6["effects"] = [{"model": ALL6[t], **v} for t, v in e6.items()]
res["by_model"] = m6
tab.append(("Six models, main prompt", m6))

# 3. crossed Claude model x wording table (descriptive two-way decomposition of the effect, one cell each)
M = np.array([[x["d"] for x in eff[t]] for t in CLAUDE])  # 2 x 4
grand = M.mean()
ss_model = 4 * ((M.mean(axis=1) - grand) ** 2).sum()
ss_word = 2 * ((M.mean(axis=0) - grand) ** 2).sum()
ss_res = ((M - M.mean(axis=1, keepdims=True) - M.mean(axis=0, keepdims=True) + grand) ** 2).sum()
tot = ss_model + ss_word + ss_res
res["crossed"] = {"cells": M.tolist(), "share_model": float(ss_model / tot), "share_wording": float(ss_word / tot),
                  "share_interaction_plus_noise": float(ss_res / tot),
                  "note": "descriptive: one cell per model x wording, so the interaction cannot be separated from noise"}

# 4. what buys precision: more runs per wording, or more wordings?  Uses the Sonnet tau^2 and mean se.
for tag, name in CLAUDE.items():
    m = res["by_wording"][name]
    se_bar = float(np.mean([x["se"] for x in m["effects"]]))
    proj = {}
    for k in (4, 8, 16):
        for mult in (1, 4):  # runs per wording x mult
            se_k = se_bar / np.sqrt(mult)
            se_mu = float(np.sqrt((m["tau2"] + se_k ** 2) / k))
            half = TQ(k - 2) * float(np.sqrt(m["tau2"] + se_mu ** 2))
            proj[f"{k} wordings, {mult}x runs"] = {"pred_interval": [m["mu"] - half, m["mu"] + half], "half_width": half}
    res["projection"][name] = proj

Path(out / "s_heterogeneity.json").write_text(json.dumps(res, indent=1))

rows = []
for label, m in tab:
    pi = m["pred_interval"]
    rows.append(f"{label} & {m['mu']:+.2f} [{m['ci'][0]:+.2f}, {m['ci'][1]:+.2f}] & {m['tau']:.2f} & {100 * m['I2']:.0f}\\% & {m['Q']:.1f} ({m['Q_df']} df) & [{pi[0]:+.2f}, {pi[1]:+.2f}] \\\\")
tex = ("\\begin{tabular}{lccccc}\n\\toprule\n set & pooled effect [95\\% CI] & $\\tau$ & $I^2$ & Q & 95\\% prediction interval \\\\\n\\midrule\n"
       + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table_heterogeneity.tex").write_text(tex)
print(json.dumps({k: (v if k != "projection" else "see file") for k, v in res.items()}, indent=1)[:6000])
