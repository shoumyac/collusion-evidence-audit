"""Puppet factorial analysis. usage: python analysis/factorial_analysis.py <results_subdir> <model_tag> [games]"""
import json, glob, sys, numpy as np
rng = np.random.default_rng(9)
sub, tag = sys.argv[1], sys.argv[2]; games = sys.argv[3].split(",") if len(sys.argv) > 3 else ["pricing", "auction"]
def rm(d, live_only=True):
    v = []
    for f in glob.glob(d + "/run_*.jsonl"):
        rows = [json.loads(l) for l in open(f) if l.strip()]
        if rows: v.append(np.mean([r["action"] for r in rows]))
    return np.array(v)
def ci(fn, cells, B=4000):
    est = fn(cells)
    bs = []
    for _ in range(B):
        c = {k: v[rng.integers(0, len(v), len(v))] for k, v in cells.items()}
        bs.append(fn(c))
    return [float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
res = {}
for g in games:
    for w in (1, 2, 3):
        bd = f"results/{sub}/{g}-{tag}-w{w}"; fd = f"results_factorial/{sub}/{g}-{tag}-w{w}"
        C = {"live_collude": rm(bd + "/collude"), "live_honest": rm(bd + "/honest")}
        for z, zn in (("collude", "1"), ("honest", "0")):
            for ta in ("cc", "ch", "hc", "hh", "cc-coh", "hh-coh"):
                C[f"{zn}_{ta}"] = rm(f"{fd}/pup-{z}-{ta}")
        if any(len(v) == 0 for v in C.values()): print("missing", g, w, [k for k, v in C.items() if len(v) == 0]); continue
        m = lambda c, k: c[k].mean()
        est = {
         "TE_live (collude-honest, both live)": lambda c: m(c, "live_collude") - m(c, "live_honest"),
         "OL_total (1,cc) - (0,hh)": lambda c: m(c, "1_cc") - m(c, "0_hh"),
         "FB feedback = TE_live - OL_total": lambda c: (m(c, "live_collude") - m(c, "live_honest")) - (m(c, "1_cc") - m(c, "0_hh")),
         "DE instruction vs honest script (1,hh)-(0,hh)": lambda c: m(c, "1_hh") - m(c, "0_hh"),
         "instruction vs collude script (1,cc)-(0,cc)": lambda c: m(c, "1_cc") - m(c, "0_cc"),
         "text main, colluding agent": lambda c: .5 * ((m(c, "1_ch") - m(c, "1_hh")) + (m(c, "1_cc") - m(c, "1_hc"))),
         "action main, colluding agent": lambda c: .5 * ((m(c, "1_hc") - m(c, "1_hh")) + (m(c, "1_cc") - m(c, "1_ch"))),
         "text x action interaction, colluding agent": lambda c: m(c, "1_cc") - m(c, "1_ch") - m(c, "1_hc") + m(c, "1_hh"),
         "text main, honest agent": lambda c: .5 * ((m(c, "0_ch") - m(c, "0_hh")) + (m(c, "0_cc") - m(c, "0_hc"))),
         "action main, honest agent": lambda c: .5 * ((m(c, "0_hc") - m(c, "0_hh")) + (m(c, "0_cc") - m(c, "0_ch"))),
         "coherence (1,cc-coh)-(1,cc)": lambda c: m(c, "1_cc-coh") - m(c, "1_cc"),
        }
        out = {k: ci(f, C) for k, f in est.items()}
        out["means"] = {k: float(v.mean()) for k, v in C.items()}; out["n"] = {k: len(v) for k, v in C.items()}
        res[f"{g}-w{w}"] = out
        print(f"{g} w{w}  n={min(out['n'].values())}-{max(out['n'].values())}")
        for k in est: print("   %-52s %+.2f [%+.2f, %+.2f]" % ((k,) + tuple(out[k])))
json.dump(res, open(f"analysis/factorial_{sub}.json", "w"), indent=1)
