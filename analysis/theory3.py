"""(c) Does a one-feature replay regression predict the cross-condition TM? Dynamic multiplier version, Qwen3-8B pricing."""
import json, glob, re, os, numpy as np
rng = np.random.default_rng(5)
ROOT = os.path.join(os.path.dirname(__file__), "..", "results")
COORD = re.compile(r"\b(keep|maintain|stay|hold)\b.*\b(high|low|stable|steady|consistent)\b|mutual|together|both of us|cooperat|collaborat|coordinat|aligned|support each other", re.I)
feat = lambda t: 1.0 if COORD.search(t or "") else 0.0
def tab(rows):
    t = {}
    for r in rows: t.setdefault(r["round_id"], {})[r["agent_id"]] = (r["action"], r["said"] or "")
    return t
def load(d):
    return {int(re.search(r"run_(\d+)", f).group(1)): tab([json.loads(l) for l in open(f)]) for f in glob.glob(d + "/run_*.jsonl")}
out = {}
for w in (1, 2, 3):
    d = f"{ROOT}/qwen3_8b/pricing-Qwen_Qwen3-8B-w{w}"
    B, S = load(d + "/collude"), load(d + "/collude_swap")
    s0 = min(B); n = max(B) - s0 + 1
    rows = []
    for k, T in S.items():
        bk = s0 + ((k - s0 + 1) % n)
        if bk not in B: continue
        TB = B[bk]
        for t in range(1, 10):
            for role, (a, _) in T[t].items():
                o = [x for x in T[t - 1] if x != role][0]
                rows.append((k, t, a, feat(TB[t - 1][o][1]), T[t - 1][o][0], T[t - 1][role][0]))
    D = np.array(rows, float)
    def fit(D):
        key = D[:, 1]; Y = D[:, 2].copy(); X = D[:, 3:6].copy()
        for t in np.unique(key):
            m = key == t; Y[m] -= Y[m].mean(); X[m] -= X[m].mean(0)
        return np.linalg.lstsq(X, Y, rcond=None)[0]
    b = fit(D)
    runs = np.unique(D[:, 0]); idx = {r: np.where(D[:, 0] == r)[0] for r in runs}
    shift = {}
    sc = np.mean([feat(T[t][r][1]) for T in load(d + "/collude").values() for t in T for r in T[t]])
    sh = np.mean([feat(T[t][r][1]) for T in load(d + "/honest").values() for t in T for r in T[t]])
    bs = []
    for _ in range(300):
        pick = rng.choice(runs, len(runs)); sel = np.concatenate([idx[p] for p in pick])
        bb = fit(D[sel]); rho = bb[2] + bb[1] * 0.0
        bs.append(bb[0] * (sc - sh) / max(1 - bb[2], 0.05))
    pred = b[0] * (sc - sh) / max(1 - b[2], 0.05)
    out[f"w{w}"] = dict(beta_text=float(b[0]), beta_rival_action=float(b[1]), rho_own_lag=float(b[2]), feature_shift=float(sc - sh),
                       predicted_TM=float(pred), predicted_TM_ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
    print(w, out[f"w{w}"], flush=True)
x = json.load(open(os.path.join(os.path.dirname(__file__), "xswap_qwen3_8b.json")))
for w in (1, 2, 3): out[f"w{w}"]["observed_TM"] = x[f"w{w}"]["TM_collude_agents (collude - collude_xswap)"]
json.dump(out, open(os.path.join(os.path.dirname(__file__), "theory3_results.json"), "w"), indent=1)
