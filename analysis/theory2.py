"""Extra checks: (a) exact randomisation test, (b) rounds cannot buy power (between-run floor), (c) sufficiency of a text feature."""
import json, glob, os, re, sys
import numpy as np
from scipy import stats
rng = np.random.default_rng(11)
OUT = {}
# (a) randomisation test over run-level text assignment, sharp null of no text effect, clustered data
def sim(n=20, m=20, icc=0.5, reps=3000, effect=0.0):
    sb, sw = np.sqrt(icc), np.sqrt(1 - icc)
    rej_perm = rej_round = rej_run = 0
    for _ in range(reps):
        u = rng.normal(0, sb, 2 * n)
        y = u[:, None] + rng.normal(0, sw, (2 * n, m))
        lab = np.r_[np.ones(n), np.zeros(n)].astype(bool); rng.shuffle(lab)   # random assignment of text source to runs
        y[lab] += effect
        rm = y.mean(1); obs = rm[lab].mean() - rm[~lab].mean()
        # exact-in-expectation Monte Carlo randomisation test over assignments
        cnt = 0; P = 199
        for _ in range(P):
            p = rng.permutation(lab); cnt += abs(rm[p].mean() - rm[~p].mean()) >= abs(obs) - 1e-12
        rej_perm += (cnt + 1) / (P + 1) <= 0.05
        rej_round += stats.ttest_ind(y[lab].ravel(), y[~lab].ravel(), equal_var=False).pvalue < 0.05
        rej_run += stats.ttest_ind(rm[lab], rm[~lab], equal_var=False).pvalue < 0.05
    return dict(n=n, m=m, icc=icc, effect=effect, randomisation=rej_perm / reps, run_level_t=rej_run / reps, round_level_t=rej_round / reps)
OUT["a_randomisation"] = [sim(effect=0.0, reps=1500), sim(n=10, effect=0.0, reps=1500), sim(effect=0.6, reps=1500)]
for r in OUT["a_randomisation"]: print("a", r, flush=True)
# (b) rounds floor
def floor(sb2, sw2, n=50):
    ms = np.array([1, 2, 5, 10, 20, 50, 1000])
    sd = np.sqrt(sb2 + sw2 / ms)
    return {int(m): float(2.8 * s * np.sqrt(2 / n)) for m, s in zip(ms, sd)}
ROOT = os.path.join(os.path.dirname(__file__), "..", "results")
res = {}
for sub, tag in (("qwen3_8b", "Qwen_Qwen3-8B"), ("phi4", "microsoft_phi-4")):
    for w in (1, 2, 3):
        runs = []
        for f in glob.glob(f"{ROOT}/{sub}/pricing-{tag}-w{w}/collude/run_*.jsonl"):
            rows = [json.loads(l) for l in open(f)]
            M = {}
            for r in rows: M.setdefault(r["round_id"], []).append(r["action"])
            runs.append([np.mean(M[t]) for t in sorted(M)])   # firm-average price per round
        R = np.array(runs); m = R.shape[1]
        sw2 = R.var(1, ddof=1).mean(); sb2 = max(R.mean(1).var(ddof=1) - sw2 / m, 0)
        res[f"{sub}-w{w}"] = dict(sigma_between_sq=float(sb2), sigma_within_sq=float(sw2), m=m, mde_at_50_runs_by_rounds=floor(sb2, sw2))
        print("b", sub, w, "sb2=%.3f sw2=%.3f" % (sb2, sw2), {k: round(v, 2) for k, v in res[f"{sub}-w{w}"]["mde_at_50_runs_by_rounds"].items()}, flush=True)
OUT["b_rounds_floor"] = res
# (c) sufficiency of the coordination-language feature: predicted vs observed TM (Qwen3-8B pricing)
COORD = re.compile(r"\b(keep|maintain|stay|hold)\b.*\b(high|low|stable|steady|consistent)\b|mutual|together|both of us|cooperat|collaborat|coordinat|aligned|support each other", re.I)
def share(cond, w):
    d = f"{ROOT}/qwen3_8b/pricing-Qwen_Qwen3-8B-w{w}/{cond}"
    v = [bool(COORD.search(json.loads(l)["said"] or "")) for f in glob.glob(d + "/run_*.jsonl") for l in open(f)]
    return float(np.mean(v))
xs = json.load(open(os.path.join(os.path.dirname(__file__), "xswap_qwen3_8b.json"))) if os.path.exists(os.path.join(os.path.dirname(__file__), "xswap_qwen3_8b.json")) else {}
c_res = {}
for w in (1, 2, 3):
    sc, sh = share("collude", w), share("honest", w)
    c_res[f"w{w}"] = dict(coord_share_collude_text=sc, coord_share_honest_text=sh, shift=sc - sh,
                         observed_TM=xs.get(f"w{w}", {}).get("TM_collude_agents (collude - collude_xswap)"))
    print("c", w, c_res[f"w{w}"], flush=True)
OUT["c_feature_shift"] = c_res
json.dump(OUT, open(os.path.join(os.path.dirname(__file__), "theory2_results.json"), "w"), indent=1)
