"""Analysis M (numpy only, no LLM calls, no cost).
(1) Label-permutation test of the cross-validated naive-Bayes say / say-masked / do classifiers from d_score_llm.py:
    same data order, same 5 folds, labels shuffled; the AUROC should be about 0.5.
(2) Interaction estimates: for each model, difference of differences
    (collude - honest, with messages) - (collude - honest, silent), with a bootstrap CI over runs.
    Same for the paraphrase and swap controls (Claude only): (collude - honest, control) - (collude - honest, main).
Reads only saved transcripts in out/llm/. Writes out/m_permutation.json, out/m_interaction.json, out/table_interaction.tex.
Run:  python3 m_permutation_and_interaction.py      (from anywhere; numpy only)
"""
import json
import math
import random
import re
from collections import Counter
from pathlib import Path

import numpy as np

here = Path(__file__).parent
out = here / "out"
MODELS = {"Qwen2.5-7B-Instruct": "Qwen2.5-7B", "Qwen2.5-32B-Instruct": "Qwen2.5-32B", "phi-4": "Phi-4",
          "Mistral-Nemo-12B": "Mistral-Nemo-12B", "claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5"}
src = (here / "c_llm_agents.py").read_text(encoding="utf-8")
PROMPT_VOCAB = set(re.findall(r"[a-z']+", src[src.index("BASE ="):src.index("PRICE_RE")].lower()))


def load(tag, cond):
    runs = []
    for tp in sorted((out / "llm" / tag / cond).glob("*.jsonl")):
        if tp.name.endswith(".metrics.json"):
            continue
        recs = [json.loads(l) for l in tp.read_text().splitlines() if l.strip()]
        if recs:
            runs.append(recs)
    return runs


def mean_price(recs):
    return float(np.mean([float(r["action"]) for r in recs]))


def feats(recs):
    return mean_price(recs), " ".join(x["message"].lower().replace("price:", " ") for x in recs)


def toks(t, mask=False):
    o = [w.strip(".,;:!?\"'()") for w in t.split() if not any(c.isdigit() for c in w)]
    return [w for w in o if not (mask and w in PROMPT_VOCAB)]


def auroc(scores, ys):
    pos = [s for s, y in zip(scores, ys) if y == 1]
    neg = [s for s, y in zip(scores, ys) if y == 0]
    return sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg))


def cv_aurocs(data, ys, K=5):
    """data: list of (price, text); ys: labels aligned with data. Same fold rule as d_score_llm.py (i::K on the shuffled order)."""
    tk = [(set(toks(t, False)), set(toks(t, True))) for _, t in data]
    idx = list(range(len(data)))
    folds = [idx[i::K] for i in range(K)]
    oof = {"say": {}, "say_masked": {}, "do": {}}
    for k in range(K):
        test = folds[k]
        train = [i for j, f in enumerate(folds) if j != k for i in f]
        n = {y: sum(1 for i in train if ys[i] == y) for y in (0, 1)}
        mu = {y: np.mean([data[i][0] for i in train if ys[i] == y]) for y in (0, 1)}
        sd = {y: max(np.std([data[i][0] for i in train if ys[i] == y]), 0.05) for y in (0, 1)}
        for mi, name in ((0, "say"), (1, "say_masked")):
            cnt = {0: Counter(), 1: Counter()}
            for i in train:
                cnt[ys[i]].update(tk[i][mi])
            vocab = set(cnt[0]) | set(cnt[1])
            for i in test:
                oof[name][i] = sum(math.log(((cnt[1][w] + 1) / (n[1] + 2)) / ((cnt[0][w] + 1) / (n[0] + 2))) for w in tk[i][mi] & vocab)
        ll = lambda p, y: -0.5 * ((p - mu[y]) / sd[y]) ** 2 - math.log(sd[y])
        for i in test:
            oof["do"][i] = ll(data[i][0], 1) - ll(data[i][0], 0)
    return {k: auroc([v[i] for i in idx], [ys[i] for i in idx]) for k, v in oof.items()}


# ---------------------------------------------------------------- (1) permutation test
import os
NPERM = int(os.environ.get("NPERM", 200))
perm = {}
REUSE = os.environ.get("REUSE_PERM") and (out / "m_permutation.json").exists()
if REUSE:
    perm = json.loads((out / "m_permutation.json").read_text())
for tag, label in ([] if REUSE else MODELS.items()):
    data = []
    for cond, y in (("honest", 0), ("collude", 1)):
        for recs in load(tag, cond):
            p, t = feats(recs)
            data.append((p, t, y))
    rng = random.Random(7)
    rng.shuffle(data)
    X = [(d[0], d[1]) for d in data]
    y0 = [d[2] for d in data]
    obs = cv_aurocs(X, y0)
    gen = np.random.default_rng(11)
    nulls = {"say": [], "say_masked": [], "do": []}
    for _ in range(NPERM):
        ys = list(gen.permutation(y0))
        a = cv_aurocs(X, ys)
        for k in nulls:
            nulls[k].append(a[k])
    perm[tag] = {"label": label, "n_runs": len(data), "n_perm": NPERM,
                 **{f"observed_{k}": obs[k] for k in obs},
                 **{f"perm_mean_{k}": float(np.mean(v)) for k, v in nulls.items()},
                 **{f"perm_q025_{k}": float(np.percentile(v, 2.5)) for k, v in nulls.items()},
                 **{f"perm_q975_{k}": float(np.percentile(v, 97.5)) for k, v in nulls.items()},
                 **{f"perm_max_{k}": float(np.max(v)) for k, v in nulls.items()}}
    print(label, {k: round(v, 3) for k, v in perm[tag].items() if k.startswith(("observed", "perm_mean", "perm_max"))}, flush=True)
if not REUSE:
    (out / "m_permutation.json").write_text(json.dumps(perm, indent=1))

# ---------------------------------------------------------------- (2) interaction (difference of differences)
B = 10000


def cell(tag, cond):
    return np.array([mean_price(r) for r in load(tag, cond)])


def boot_did(c1, h1, c0, h0, seed):
    g = np.random.default_rng(seed)
    r = lambda a: g.choice(a, (B, len(a))).mean(axis=1)
    d = (r(c1) - r(h1)) - (r(c0) - r(h0))
    est = (c1.mean() - h1.mean()) - (c0.mean() - h0.mean())
    return float(est), [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def boot_diff(c, h, seed):
    g = np.random.default_rng(seed)
    d = g.choice(c, (B, len(c))).mean(axis=1) - g.choice(h, (B, len(h))).mean(axis=1)
    return float(c.mean() - h.mean()), [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


inter = {}
for i, (tag, label) in enumerate(MODELS.items()):
    ch, cc, sh, sc = cell(tag, "honest"), cell(tag, "collude"), cell(tag, "honest_silent"), cell(tag, "collude_silent")
    e = {"label": label, "effect_with_messages": boot_diff(cc, ch, 100 + i), "effect_silent": boot_diff(sc, sh, 200 + i),
         "interaction_msg_minus_silent": boot_did(cc, ch, sc, sh, 300 + i)}
    for ctl in ("para", "swap"):
        if (out / "llm" / tag / f"collude_{ctl}").exists():
            ph, pc = cell(tag, f"honest_{ctl}"), cell(tag, f"collude_{ctl}")
            e[f"effect_{ctl}"] = boot_diff(pc, ph, 400 + i)
            e[f"interaction_main_minus_{ctl}"] = boot_did(cc, ch, pc, ph, 500 + i)
    inter[tag] = e
    print(label, {k: v for k, v in e.items() if k != "label"}, flush=True)
(out / "m_interaction.json").write_text(json.dumps(inter, indent=1))

f = lambda v: f"{v[0]:+.2f} [{v[1][0]:+.2f}, {v[1][1]:+.2f}]"
rows = []
for tag, e in inter.items():
    sw = f(e["effect_swap"]) if "effect_swap" in e else "--"
    rows.append(f"{e['label']} & {f(e['effect_with_messages'])} & {f(e['effect_silent'])} & {f(e['interaction_msg_minus_silent'])} & {sw} \\\\")
tab = ("\\begin{tabular}{lcccc}\n\\toprule\nmodel & collude $-$ honest, messages & collude $-$ honest, silent & difference of the two & collude $-$ honest, swap \\\\\n\\midrule\n"
       + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table_interaction.tex").write_text(tab)
rows = []
for tag, e in perm.items():
    rows.append(f"{e['label']} & {e['observed_say']:.2f} & {e['perm_mean_say']:.2f} ({e['perm_max_say']:.2f}) & {e['observed_say_masked']:.2f} & {e['perm_mean_say_masked']:.2f} ({e['perm_max_say_masked']:.2f}) & {e['observed_do']:.2f} & {e['perm_mean_do']:.2f} ({e['perm_max_do']:.2f}) \\\\")
tab = ("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{say} & \\multicolumn{2}{c}{say, prompt words masked} & \\multicolumn{2}{c}{do} \\\\\n"
       "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\nmodel & observed & shuffled mean (max) & observed & shuffled mean (max) & observed & shuffled mean (max) \\\\\n\\midrule\n"
       + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table_permutation.tex").write_text(tab)
print("done")
