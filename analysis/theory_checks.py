"""Numerical checks for docs/THEORY_IDENTIFICATION.md.
A  witness simulation (live law identical, replay differs)
B  replay regression on our runs (replayed partner text is exogenous)
C  pooled vs within-model AUROC and threshold transport (pricing)
D  size inflation from treating rounds as units, design effect
E  design numbers for a cross-condition replay experiment
Run: python analysis/theory_checks.py  (writes analysis/theory_checks_results.json)"""
import json, glob, re, os, collections, itertools
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "results")
MODELS = {"qwen3_8b": "Qwen3-8B", "qwen3_32b": "Qwen3-32B", "phi4": "Phi-4"}
COORD = re.compile(r"\b(keep|maintain|stay|hold)\b.*\b(high|low|stable|steady|consistent)\b|mutual|together|both of us|cooperat|collaborat|coordinat|aligned|support each other", re.I)
rng = np.random.default_rng(7)
OUT = {}

# ---------- loading ----------
def load_cell(d):
    cells = {}
    for c in glob.glob(d + "/*/"):
        cond = c.rstrip("/").split("/")[-1]
        runs = {}
        for f in glob.glob(c + "run_*.jsonl"):
            k = int(re.search(r"run_(\d+)", f).group(1))
            rows = [json.loads(l) for l in open(f)]
            if rows: runs[k] = rows
        if runs: cells[cond] = runs
    return cells

def cells_for(mdir):
    out = {}
    for d in sorted(glob.glob(f"{ROOT}/{mdir}/*/")):
        name = os.path.basename(d.rstrip("/"))
        game, rest = name.split("-", 1)
        w = int(rest.rsplit("-w", 1)[1])
        out[(game, w)] = load_cell(d.rstrip("/"))
    return out

def run_table(rows):
    """dict round -> role -> (action, said)"""
    t = collections.defaultdict(dict)
    for r in rows: t[r["round_id"]][r["agent_id"]] = (r["action"], r["said"] or "")
    return t

# ---------- A: witness simulation ----------
def witness(n=400000, ss=1.0, se=1.0, su=0.5):
    # common cause: B ignores A's words, shares seed s.   a_B = s + e'
    # responsive:   B copies A's words partially.         a_B = rho*m_A + u
    s = rng.normal(0, ss, n); mA = s + rng.normal(0, se, n)
    vm = ss**2 + se**2; rho = ss**2 / vm
    aB1 = s + rng.normal(0, se, n)
    varB = ss**2 + se**2
    aB2 = rho * mA + rng.normal(0, np.sqrt(varB - rho**2 * vm), n)
    live = {k: np.cov(mA, a)[0, 1] for k, a in (("common_cause", aB1), ("responsive", aB2))}
    live_var = {k: float(a.var()) for k, a in (("common_cause", aB1), ("responsive", aB2))}
    # replay: A's message replaced by an independent draw from the same marginal
    mp = rng.permutation(mA)
    aB1r = aB1  # does not read the message
    aB2r = rho * mp + (aB2 - rho * mA)
    res = {"live_cov_mA_aB": live, "live_var_aB": live_var,
           "mean_contrast_replay_minus_live": {"common_cause": float(aB1r.mean() - aB1.mean()), "responsive": float(aB2r.mean() - aB2.mean())},
           "replay_cov_replayedmsg_aB": {"common_cause": float(np.cov(mp, aB1r)[0, 1]), "responsive": float(np.cov(mp, aB2r)[0, 1])}}
    # cross-condition replay: message from a population shifted by delta
    d = 1.5
    mx = mp + d
    res["cross_condition_mean_shift"] = {"common_cause": 0.0, "responsive": float((rho * mx + (aB2 - rho * mA)).mean() - aB2.mean()), "rho": rho, "delta": d}
    return res
OUT["A_witness"] = witness()

# ---------- B: replay regression ----------
def feat(txt): return 1.0 if COORD.search(txt) else 0.0

def reg_rows(cells, base, swap_suffix="_swap", seed_n=None):
    """rows (cell_run_key, y, x_replay, x_live_placebo, x_live_actual, z_act, ylag, groupkey) for swap runs"""
    S = cells.get(base + swap_suffix); B = cells.get(base)
    if not S or not B: return []
    seeds = sorted(B)
    s0 = seeds[0]; n = seeds[-1] - s0 + 1
    out = []
    for k, rows in S.items():
        bk = s0 + ((k - s0 + 1) % n)
        if bk not in B: continue
        T = run_table(rows); TB = run_table(B[bk])
        for t in sorted(T):
            if t == 0 or (t - 1) not in T or (t - 1) not in TB: continue
            for role, (a, _) in T[t].items():
                partners = [o for o in T[t - 1] if o != role]
                if not partners or any(o not in TB[t - 1] or o not in T[t - 1] for o in partners) or role not in T[t - 1]: continue
                xr = np.mean([feat(TB[t - 1][o][1]) for o in partners])
                xp = np.mean([feat(T[t - 1][o][1]) for o in partners])    # partner's own-run text, never shown
                za = np.mean([T[t - 1][o][0] for o in partners])
                out.append((k, t, a, xr, xp, za, T[t - 1][role][0]))
    return out

def live_rows(cells, base):
    B = cells.get(base)
    if not B: return []
    out = []
    for k, rows in B.items():
        T = run_table(rows)
        for t in sorted(T):
            if t == 0 or (t - 1) not in T: continue
            for role, (a, _) in T[t].items():
                partners = [o for o in T[t - 1] if o != role]
                if not partners or role not in T[t - 1]: continue
                xl = np.mean([feat(T[t - 1][o][1]) for o in partners])
                za = np.mean([T[t - 1][o][0] for o in partners])
                out.append((k, t, a, xl, xl, za, T[t - 1][role][0]))
    return out

def slope(data, col, controls=(5, 6)):
    """data: array rows (cell, run, t, y, xr, xp, za, ylag); FE for cell x round; slope on col."""
    D = np.array(data, float)
    if len(D) < 50: return np.nan
    # demean within cell x round
    key = D[:, 0] * 100 + D[:, 2]
    Y = D[:, 3].copy(); X = D[:, [col] + list(controls)].copy()
    for kk in np.unique(key):
        m = key == kk
        Y[m] -= Y[m].mean(); X[m] -= X[m].mean(0)
    b = np.linalg.lstsq(X, Y, rcond=None)[0]
    return b[0]

def cluster_boot(data, col, controls, B=300):
    D = np.array(data, float)
    est = slope(D.tolist(), col, controls)
    runs = np.unique(D[:, 0] * 10000000 + D[:, 1])
    idx = {r: np.where(D[:, 0] * 10000000 + D[:, 1] == r)[0] for r in runs}
    bs = []
    for _ in range(B):
        pick = rng.choice(len(runs), len(runs))
        sel = np.concatenate([idx[runs[p]] for p in pick])
        bs.append(slope(D[sel].tolist(), col, controls))
    bs = np.array(bs)
    return est, float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))

B_RES = []
for mdir, mname in MODELS.items():
    allc = cells_for(mdir)
    for game in ("pricing", "auction", "cournot"):
        for cond in ("collude", "honest"):
            rep, plc, live = [], [], []
            cid = 0
            for (g, w), cells in allc.items():
                if g != game: continue
                cid += 1
                for r in reg_rows(cells, cond):
                    rep.append((cid, r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
                for r in live_rows(cells, cond):
                    live.append((cid, r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
            if len(rep) < 200: continue
            # columns in rows: 0 cell,1 run,2 t,3 y,4 xr,5 xp,6 za,7 ylag -> slope() expects col index among [0..7] with controls (6,7)
            e_r = cluster_boot(rep, 4, (6, 7))
            e_p = cluster_boot(rep, 5, (6, 7))
            e_l = cluster_boot(live, 4, (6, 7))
            sd_y = float(np.std([r[3] for r in rep]))
            B_RES.append(dict(model=mname, game=game, cond=cond, n_rows=len(rep), sd_action=sd_y,
                              share_x1=float(np.mean([r[4] > 0 for r in rep])),
                              replay_slope=e_r, placebo_slope=e_p, live_slope=e_l))
            print("B", mname, game, cond, "replay %.2f [%.2f,%.2f]" % e_r, "placebo %.2f [%.2f,%.2f]" % e_p, "live %.2f [%.2f,%.2f]" % e_l, flush=True)
OUT["B_replay_regression"] = B_RES

# ---------- C: pooled vs within AUROC, threshold transport (pricing) ----------
def auroc(pos, neg):
    pos = np.asarray(pos); neg = np.asarray(neg)
    if len(pos) == 0 or len(neg) == 0: return np.nan
    allv = np.concatenate([pos, neg]); ranks = allv.argsort().argsort() + 1
    ties = {}
    # average ranks for ties
    from scipy.stats import rankdata
    r = rankdata(allv)
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))

runmean = {}  # (model, w, cond) -> array of run-mean prices
for mdir, mname in MODELS.items():
    for (g, w), cells in cells_for(mdir).items():
        if g != "pricing": continue
        for cond in ("honest", "collude"):
            if cond in cells:
                runmean[(mname, w, cond)] = np.array([np.mean([r["action"] for r in rows]) for rows in cells[cond].values()])
within = {}
for m in MODELS.values():
    for w in (1, 2, 3):
        if (m, w, "collude") in runmean:
            within[f"{m}-w{w}"] = auroc(runmean[(m, w, "collude")], runmean[(m, w, "honest")])
pos_all = np.concatenate([v for (m, w, c), v in runmean.items() if c == "collude"])
neg_all = np.concatenate([v for (m, w, c), v in runmean.items() if c == "honest"])
pooled = auroc(pos_all, neg_all)
# threshold transport: threshold = 95th pct of honest from source model (all wordings), apply to target
trans = {}
for s in MODELS.values():
    hs = np.concatenate([v for (m, w, c), v in runmean.items() if m == s and c == "honest"])
    th = float(np.percentile(hs, 95))
    for t in MODELS.values():
        h = np.concatenate([v for (m, w, c), v in runmean.items() if m == t and c == "honest"])
        cc = np.concatenate([v for (m, w, c), v in runmean.items() if m == t and c == "collude"])
        trans[f"{s}->{t}"] = dict(threshold=th, fpr=float((h > th).mean()), tpr=float((cc > th).mean()))
# a "model-identity" detector: flag by model, ignore the run
by_model_mean = {m: float(np.concatenate([v for (mm, w, c), v in runmean.items() if mm == m]).mean()) for m in MODELS.values()}
OUT["C_auroc"] = dict(within=within, pooled=pooled, transport=trans, model_means=by_model_mean,
                      honest_means={m: float(np.concatenate([v for (mm, w, c), v in runmean.items() if mm == m and c == "honest"]).mean()) for m in MODELS.values()})
print("C within", {k: round(v, 2) for k, v in within.items()}, "pooled", round(pooled, 2))
for k, v in trans.items(): print("C", k, "th=%.2f fpr=%.2f tpr=%.2f" % (v["threshold"], v["fpr"], v["tpr"]))

# ---------- D: size inflation and design effect ----------
D_RES = []
for mdir, mname in MODELS.items():
    for (g, w), cells in cells_for(mdir).items():
        H = cells.get("honest")
        if not H or len(H) < 20: continue
        keys = sorted(H)
        runs_rows = [np.array([r["action"] for r in H[k]], float) for k in keys]   # agent-rounds per run
        runmeans = np.array([x.mean() for x in runs_rows])
        m = np.mean([len(x) for x in runs_rows])
        grand = np.concatenate(runs_rows).mean()
        msb = m * runmeans.var(ddof=1)
        msw = np.mean([x.var(ddof=1) for x in runs_rows])
        icc = max(0.0, (msb - msw) / (msb + (m - 1) * msw))
        deff = 1 + (m - 1) * icc
        # honest vs honest random split, rounds as units vs runs as units
        rej_round = rej_run = 0; R = 600
        from scipy import stats
        for _ in range(R):
            perm = rng.permutation(len(keys)); a, b = perm[: len(keys) // 2], perm[len(keys) // 2:]
            xa = np.concatenate([runs_rows[i] for i in a]); xb = np.concatenate([runs_rows[i] for i in b])
            rej_round += stats.ttest_ind(xa, xb, equal_var=False).pvalue < 0.05
            rej_run += stats.ttest_ind(runmeans[a], runmeans[b], equal_var=False).pvalue < 0.05
        D_RES.append(dict(model=mname, game=g, w=w, n_runs=len(keys), m=m, icc=float(icc), deff=float(deff),
                          size_round_unit=rej_round / R, size_run_unit=rej_run / R))
        print("D", mname, g, w, "icc=%.2f deff=%.1f size(round)=%.2f size(run)=%.2f" % (icc, deff, rej_round / R, rej_run / R), flush=True)
OUT["D_size_inflation"] = D_RES

# ---------- E: design numbers for cross-condition replay ----------
from scipy.stats import norm
E_RES = []
for mdir, mname in MODELS.items():
    for (g, w), cells in cells_for(mdir).items():
        H, C = cells.get("honest"), cells.get("collude")
        if not H or not C: continue
        h = np.array([np.mean([r["action"] for r in rows]) for rows in H.values()])
        c = np.array([np.mean([r["action"] for r in rows]) for rows in C.values()])
        eff = float(c.mean() - h.mean()); sd = float(np.sqrt((h.var(ddof=1) + c.var(ddof=1)) / 2))
        E_RES.append(dict(model=mname, game=g, w=w, effect=eff, sd_run=sd, d=eff / sd if sd > 0 else None,
                          n_per_arm_for_half_effect_80pct=int(np.ceil(2 * sd**2 * (norm.ppf(.975) + norm.ppf(.8))**2 / (eff / 2)**2)) if abs(eff) > 1e-9 else None,
                          mde_at_50_runs=float(2.8 * sd * np.sqrt(2 / 50))))
OUT["E_design"] = E_RES
json.dump(OUT, open(os.path.join(os.path.dirname(__file__), "theory_checks_results.json"), "w"), indent=1, default=float)
print("done")
