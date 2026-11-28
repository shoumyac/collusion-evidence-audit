"""Cross-condition replay analysis (pricing). TM = collude - collude_xswap (colluding agents read collude-run vs honest-run text)."""
import json, glob, os, re, sys, numpy as np
rng = np.random.default_rng(3)
def means(d):
    out = []
    for f in glob.glob(d + "/run_*.jsonl"):
        rows = [json.loads(l) for l in open(f) if l.strip()]
        if rows: out.append(np.mean([r["action"] for r in rows]))
    return np.array(out)
def diff(a, b, B=10000):
    ia = rng.integers(0, len(a), (B, len(a))); ib = rng.integers(0, len(b), (B, len(b)))
    d = a[ia].mean(1) - b[ib].mean(1)
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
model = sys.argv[1] if len(sys.argv) > 1 else "qwen3_8b"; tag = sys.argv[2] if len(sys.argv) > 2 else "Qwen_Qwen3-8B"
res = {}
for w in (1, 2, 3):
    base = f"results/{model}/pricing-{tag}-w{w}"; x = f"results_xswap/{model}/pricing-{tag}-w{w}"
    M = {c: means(f"{base}/{c}") for c in ("honest", "collude", "honest_swap", "collude_swap")}
    M.update({c: means(f"{x}/{c}") for c in ("honest_xswap", "collude_xswap")})
    r = {"n": {k: len(v) for k, v in M.items()}, "mean": {k: float(v.mean()) for k, v in M.items()},
         "TE": diff(M["collude"], M["honest"]),
         "TM_collude_agents (collude - collude_xswap)": diff(M["collude"], M["collude_xswap"]),
         "swap_contrast (collude - collude_swap)": diff(M["collude"], M["collude_swap"]),
         "DE (collude_xswap - honest)": diff(M["collude_xswap"], M["honest"]),
         "text_effect_honest_agents (honest_xswap - honest)": diff(M["honest_xswap"], M["honest"])}
    res[f"w{w}"] = r
    print(f"w{w}", {k: v for k, v in r["mean"].items()})
    for k in list(r)[2:]: print("  %-52s %+.2f [%+.2f, %+.2f]" % ((k,) + tuple(r[k])))
json.dump(res, open(f"analysis/xswap_{model}.json", "w"), indent=1)
