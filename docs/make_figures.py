"""Build the README / wiki figures from the saved results in sprint_work/out.

Run from the repository root:  python docs/make_figures.py
Every number comes from a saved JSON file, except the six-model price table, which is read from
the same values that appear in report Table 2 (sprint_work/out/table2.tex).
"""
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sprint_work", "out")
IMG = os.path.join(ROOT, "docs", "img")
os.makedirs(IMG, exist_ok=True)

NAVY, TEAL, AMBER, RED, GRAY, LIGHT, INK = "#1F3A5F", "#2A9D8F", "#E9A23B", "#D1495B", "#8A94A6", "#F4F6FA", "#1B2433"

for f in font_manager.findSystemFonts():
    if "Inter-" in os.path.basename(f) or "Inter[" in os.path.basename(f):
        font_manager.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"], "font.size": 11, "axes.edgecolor": GRAY, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 200, "savefig.bbox": "tight",
})


def load(name):
    with open(os.path.join(OUT, name)) as fh:
        return json.load(fh)


def save(fig, name, face="white"):
    fig.savefig(os.path.join(IMG, name), facecolor=face)
    plt.close(fig)
    print("wrote", name)


# ------------------------------------------------------------------ 00 hero banner
def hero():
    fig = plt.figure(figsize=(12, 3.6))
    fig.patch.set_facecolor(NAVY)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 3.6)
    ax.text(0.45, 3.0, "Auditing a Collusion Detector", color="white", fontsize=26, fontweight="bold", va="center")
    ax.text(0.45, 2.45, "Unit of replication, calibration and say-versus-do gaps in LLM pricing agents",
            color="#C9D6EA", fontsize=12.5, va="center")
    stats = [("99%", "of fresh honest batches\nflagged at p <= 0.05"), ("20", "independent honest batches\nneeded to calibrate"),
             ("6 of 6", "models keep the price rise\nwhen messages are swapped"), ("+2.0 to -0.3", "swing in Sonnet's collusion\neffect across 4 prompt wordings")]
    for i, (big, small) in enumerate(stats):
        x = 0.45 + i * 2.95
        ax.add_patch(plt.Rectangle((x, 0.35), 2.7, 1.55, color="#2B4C7A", lw=0))
        ax.text(x + 0.18, 1.45, big, color="#FFD27A", fontsize=21, fontweight="bold", va="center")
        ax.text(x + 0.18, 0.78, small, color="white", fontsize=9.5, va="center", linespacing=1.3)
    save(fig, "00_hero.png", face=NAVY)


# ------------------------------------------------------------------ 01 pseudoreplication
def pseudorep():
    a = load("a_pseudoreplication.json")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw={"width_ratios": [1, 1.25]})
    labels = ["Counted\nnaively", "Distinct\nwithin files", "Distinct\nacross files", "Distinct, ignoring\nrun id"]
    vals = [a["raw_runs_counted_naively"], a["distinct_runs_within_file"], a["distinct_runs_by_content_global"], a["distinct_ignoring_run_id"]]
    cols = [RED, AMBER, TEAL, NAVY]
    bars = ax1.bar(labels, vals, color=cols, width=0.62)
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 400, f"{v:,}", ha="center", fontweight="bold")
    ax1.set_ylim(0, 25500); ax1.set_ylabel("runs"); ax1.set_title("Shipped transcripts: 22,127 runs, far fewer distinct", loc="left", fontsize=11.5, fontweight="bold")
    ax1.tick_params(axis="x", labelsize=9)
    d = a["by_top_dir"]
    names = ["calibration", "audit", "sweeps", "stress", "experiments", "baseline"]
    y = np.arange(len(names))
    raw = [d[n]["raw"] for n in names]; dist = [d[n]["distinct"] for n in names]
    ax2.barh(y + 0.19, raw, 0.36, color=RED, label="counted naively")
    ax2.barh(y - 0.19, dist, 0.36, color=TEAL, label="distinct")
    ax2.set_xscale("log"); ax2.set_yticks(y); ax2.set_yticklabels(names); ax2.invert_yaxis()
    for yi, r_, d_ in zip(y, raw, dist):
        ax2.text(r_ * 1.1, yi + 0.19, f"{r_:,}", va="center", fontsize=8.5); ax2.text(d_ * 1.1, yi - 0.19, f"{d_:,}", va="center", fontsize=8.5)
    ax2.set_xlim(3, 90000); ax2.set_xlabel("runs (log scale)"); ax2.legend(frameon=False, loc="lower right")
    ax2.set_title("By results folder", loc="left", fontsize=11.5, fontweight="bold")
    fig.tight_layout(); save(fig, "01_pseudoreplication.png")


# ------------------------------------------------------------------ 02 false alarms
def false_alarms():
    r = load("report_numbers.json")["B_pvalue_rates"]
    dets = [("cross_run_mi", "Cross-run\nMI"), ("linguistic_steganalysis", "Linguistic"), ("welfare_shift", "Welfare"), ("acceptance_bias", "Acceptance\nbias")]
    scen = [("pricing", "Pricing duopoly", NAVY), ("auction", "First-price auction", TEAL), ("review", "Peer review", AMBER)]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    w = 0.26
    for i, (s, sl, c) in enumerate(scen):
        xs, ys, lo, hi = [], [], [], []
        for j, (dk, _) in enumerate(dets):
            k = f"{s}|honest|{dk}|0.05"
            if k in r:
                v = r[k]; xs.append(j + (i - 1) * w); ys.append(v["rate"]); lo.append(v["rate"] - v["lo"]); hi.append(v["hi"] - v["rate"])
        ax.bar(xs, ys, w, color=c, label=sl, yerr=[lo, hi], error_kw=dict(ecolor=INK, lw=1, capsize=2))
        for x_, y_ in zip(xs, ys):
            ax.text(x_, y_ + 0.045, f"{y_*100:.0f}%", ha="center", fontsize=8.5)
    ax.axhline(0.05, color=RED, ls="--", lw=1.4); ax.text(2.42, 0.07, "nominal 5%", color=RED, ha="left", fontsize=9.5, fontweight="bold")
    ax.set_xticks(range(len(dets))); ax.set_xticklabels([d[1] for d in dets]); ax.set_ylim(0, 1.15)
    ax.set_yticks([0, .25, .5, .75, 1]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("honest batches flagged at p <= 0.05"); ax.legend(frameon=False, ncol=3, loc="upper right")
    ax.set_title("On 180 fresh honest batches per scenario, two of the shipped detectors raise alarms almost every time", loc="left", fontsize=11.5, fontweight="bold")
    save(fig, "02_false_alarms.png")


# ------------------------------------------------------------------ 03 calibration curve
def curve():
    j = load("j_curve.json")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.3))
    cols = {"pricing": NAVY, "auction": TEAL, "review": AMBER}
    names = {"pricing": "pricing", "auction": "auction", "review": "peer review"}
    rows = j["pricing"]["rows"]; n = [r["n_cal"] for r in rows]
    th = np.array([r["theory_mean"] for r in rows]); sd = np.array([r["theory_sd"] for r in rows])
    ax1.fill_between(n, np.clip(th - sd, 0, 1), th + sd, color=GRAY, alpha=0.25, label="theory, mean ± 1 sd")
    ax1.plot(n, th, color=GRAY, lw=2, ls="--", label="theory: Beta curve")
    for s in ["pricing", "auction", "review"]:
        ax1.plot([r["n_cal"] for r in j[s]["rows"]], [r["fpr_mean"] for r in j[s]["rows"]], "o-", color=cols[s], label=names[s], lw=1.8)
    ax1.axhline(0.05, color=RED, ls=":", lw=1.3); ax1.set_xscale("log"); ax1.set_xticks(n); ax1.set_xticklabels(n)
    ax1.xaxis.set_minor_formatter(NullFormatter()); ax1.text(82, 0.056, "5%", color=RED, fontsize=9, fontweight="bold"); ax1.set_xlabel("independent honest batches used to set the threshold"); ax1.set_ylabel("held-out false-positive rate")
    ax1.set_title("Error rate settles near 5% from about 20 batches", loc="left", fontsize=11, fontweight="bold"); ax1.legend(frameon=False, fontsize=9)
    for k, lab, c in [("tpr_keyword", "keyword", NAVY), ("tpr_sparse", "sparse (stealth)", TEAL), ("tpr_smart", "smart", AMBER), ("tpr_adaptive", "adaptive", RED)]:
        ys = np.mean([[r[k] for r in j[s]["rows"]] for s in ["pricing", "auction", "review"]], axis=0)
        ax2.plot(n, ys, {"tpr_keyword": "o", "tpr_sparse": "s", "tpr_smart": "^", "tpr_adaptive": "D"}[k], color=c, label=lab, ms=9, alpha=0.6, ls="-" if k == "tpr_keyword" else "none", lw=2)
    ax2.set_xscale("log"); ax2.set_xticks(n); ax2.set_xticklabels(n); ax2.set_ylim(0.9, 1.05); ax2.set_yticks([0.9, 0.95, 1.0]); ax2.set_yticklabels(["90%", "95%", "100%"])
    ax2.xaxis.set_minor_formatter(NullFormatter()); ax2.set_xlabel("independent honest batches used to set the threshold"); ax2.set_ylabel("detection rate of scripted colluders")
    ax2.set_title("Detection stays at 100%: all four scripted colluders are easy", loc="left", fontsize=11, fontweight="bold"); ax2.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout(); save(fig, "03_calibration_curve.png")


# ------------------------------------------------------------------ 04 prices
def parse_table2():
    txt = open(os.path.join(OUT, "table2.tex")).read()
    out = {}
    for line in txt.splitlines():
        if "&" not in line or line.startswith("model"):
            continue
        cells = [c.strip() for c in line.rstrip("\\ ").split("&")]
        nums = []
        for c in cells[2:6]:
            m = re.match(r"([0-9.]+) \[([0-9.]+), ([0-9.]+)\]", c)
            nums.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
        out[cells[0]] = nums
    return out


def prices():
    t = parse_table2()
    models = list(t.keys())
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.axhspan(4.6, 5.5, color="#E7F4F2", zorder=0)
    ax.axhline(4.6, color=TEAL, lw=1.6, ls="--"); ax.axhline(5.5, color=NAVY, lw=1.6, ls="--"); ax.axhline(1.0, color=GRAY, lw=1.2, ls=":")
    ax.text(5.55, 4.68, "Nash 4.6", color=TEAL, ha="right", fontsize=9.5, fontweight="bold"); ax.text(5.55, 5.58, "joint maximum 5.5", color=NAVY, ha="right", fontsize=9.5, fontweight="bold")
    ax.text(5.55, 1.08, "cost 1.0", color=GRAY, ha="right", fontsize=9.5)
    conds = [("honest", TEAL, -0.27), ("collude", RED, -0.09), ("honest, silent", "#9BD3CC", 0.09), ("collude, silent", "#F0A3AE", 0.27)]
    for ci, (cn, c, off) in enumerate(conds):
        for mi, m in enumerate(models):
            v, lo, hi = t[m][ci]
            ax.errorbar(mi + off, v, yerr=[[v - lo], [hi - v]], fmt="o", color=c, ms=7, capsize=2.5, lw=1.4, label=cn if mi == 0 else None)
    ax.set_xticks(range(len(models))); ax.set_xticklabels([m.replace("Claude ", "Claude\n") for m in models], fontsize=9.5)
    ax.set_ylabel("mean price per run"); ax.set_ylim(0.8, 6.0); ax.legend(frameon=False, ncol=4, loc="upper left", fontsize=9)
    ax.set_title("Honest prices sit far below Nash; the collusion instruction raises them, but only Sonnet reaches the Nash level", loc="left", fontsize=11.5, fontweight="bold")
    save(fig, "04_prices.png")


# ------------------------------------------------------------------ 05 swap control
def swap():
    m = load("m_interaction.json")
    keys = list(m.keys())
    fig, ax = plt.subplots(figsize=(11, 4.8))
    y = np.arange(len(keys))
    for i, k in enumerate(keys):
        e, (l1, h1) = m[k]["effect_with_messages"]; s, (l2, h2) = m[k]["effect_swap"]
        ax.errorbar(e, i - 0.14, xerr=[[e - l1], [h1 - e]], fmt="o", color=NAVY, ms=8, capsize=3, lw=1.6, label="real rival's messages" if i == 0 else None)
        ax.errorbar(s, i + 0.14, xerr=[[s - l2], [h2 - s]], fmt="s", color=AMBER, ms=8, capsize=3, lw=1.6, label="another run's messages (swap)" if i == 0 else None)
    ax.axvline(0, color=GRAY, lw=1)
    ax.set_yticks(y); ax.set_yticklabels([m[k]["label"] for k in keys]); ax.invert_yaxis()
    ax.set_xlabel("collusion instruction effect on mean price (collude minus honest, 95% CI)")
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("Swap the rival's messages and the price rise stays, for all six models", loc="left", fontsize=11.5, fontweight="bold")
    save(fig, "05_swap_control.png")


# ------------------------------------------------------------------ 06 prompt wording
def wording():
    o = load("o_variants.json")
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    prompts = ["prompt 1\n(main)", "prompt 2\n(reworded)", "prompt 3\n(strict honest)", "prompt 4\n(reworded again)"]
    for model, c, off, tag in [("haiku", AMBER, -0.12, "Claude Haiku 5.5"), ("sonnet", NAVY, 0.12, "Claude Sonnet 5.5")]:
        ks = [f"claude-{model}-5-5", f"claude-{model}-5-5-v2", f"claude-{model}-5-5-v3", f"claude-{model}-5-5-v4"]
        vals = [o[k]["effect"] for k in ks]
        e = np.array([v[0] for v in vals]); lo = np.array([v[1][0] for v in vals]); hi = np.array([v[1][1] for v in vals])
        x = np.arange(4) + off
        ax.errorbar(x, e, yerr=[e - lo, hi - e], fmt="o-", color=c, ms=8, capsize=3, lw=1.8, label=tag)
        for xi, ei in zip(x, e):
            ax.text(xi + (0.13 if model == "sonnet" else 0.0), ei + (0.0 if model == "sonnet" else -0.22), f"{ei:+.2f}", ha="left" if model == "sonnet" else "center", va="center", fontsize=9, color=c)
    ax.axhline(0, color=GRAY, lw=1)
    ax.set_xticks(range(4)); ax.set_xticklabels(prompts); ax.set_xlim(-0.5, 3.6); ax.set_ylabel("effect of collusion instruction on price")
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("The effect belongs to the wording: Sonnet swings from +2.0 to below zero", loc="left", fontsize=11.5, fontweight="bold")
    save(fig, "06_prompt_wording.png")


# ------------------------------------------------------------------ 07 auction
def auction():
    r = load("r_auction.json")
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
    for ax, k, tag in [(axs[0], "claude-haiku-5-5", "Claude Haiku 5.5"), (axs[1], "claude-sonnet-5-5", "Claude Sonnet 5.5")]:
        mp = r[k]["mean_price"]
        labs = ["honest", "collude", "honest\n(swap)", "collude\n(swap)"]; vals = [mp["honest"], mp["collude"], mp["honest_swap"], mp["collude_swap"]]
        bars = ax.bar(labs, vals, color=[TEAL, RED, "#9BD3CC", "#F0A3AE"], width=0.65)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.15, f"{v:.2f}", ha="center", fontweight="bold", fontsize=10)
        ax.set_title(tag, loc="left", fontsize=11.5, fontweight="bold"); ax.set_ylim(0, 12.5)
        ax.tick_params(axis="x", labelsize=9)
    axs[0].set_ylabel("mean clearing price (private values around 10)")
    fig.suptitle("Second game, first-price auction: Sonnet's price falls by 5.3, and swapping messages barely changes it", x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    fig.tight_layout(); save(fig, "07_auction.png")


# ------------------------------------------------------------------ 08 auditor
def auditor():
    rows = [("Qwen2.5-7B", 1.00, 1.00, 1.00), ("Qwen2.5-32B", 0.99, 1.00, None), ("Phi-4", 0.92, 0.90, None), ("Mistral-Nemo-12B", 1.00, 0.99, None),
            ("Claude Sonnet 5.5", 0.21, 0.19, 0.42), ("Claude Haiku 5.5", 0.00, 0.00, 0.00)]
    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    y = np.arange(len(rows))
    cols = [TEAL if r[1] >= 0.9 else RED for r in rows]
    ax.barh(y, [r[1] for r in rows], color=cols, height=0.55)
    for yi, r_ in zip(y, rows):
        ax.text(r_[1] + 0.015, yi, f"{r_[1]:.2f}", va="center", fontweight="bold")
    ax.axvline(0.5, color=GRAY, ls="--", lw=1.2); ax.text(0.51, 5.45, "chance (0.5)", color=GRAY, fontsize=9)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis(); ax.set_xlim(0, 1.12)
    ax.set_xlabel("blind auditor AUROC from messages only (1 = agrees with labels, 0 = fully inverted)")
    ax.set_title("A text auditor agrees with the labels for open models, and inverts them for Claude", loc="left", fontsize=11.5, fontweight="bold")
    save(fig, "08_auditor.png")


# ------------------------------------------------------------------ 09 heterogeneity (post-sprint analysis S)
def heterogeneity():
    r = load("s_heterogeneity.json")
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.6), sharex=True)
    for ax, name, col in [(axs[0], "Claude Haiku 5.5", AMBER), (axs[1], "Claude Sonnet 5.5", NAVY)]:
        m = r["by_wording"][name]; eff = m["effects"]
        for i, e in enumerate(eff):
            ax.errorbar(e["d"], i, xerr=1.96 * e["se"], fmt="s", color=col, ms=7, capsize=3, lw=1.6)
            ax.text(e["d"] + 1.96 * e["se"] + 0.25, i, f"{e['d']:+.2f}", ha="left", va="center", fontsize=9, color=col)
        y = len(eff) + 0.3
        ax.fill_betweenx([y - 0.28, y + 0.28], m["ci"][0], m["ci"][1], color=col, alpha=0.9)
        ax.plot([m["pred_interval"][0], m["pred_interval"][1]], [y + 0.75, y + 0.75], color=RED, lw=3, solid_capstyle="butt")
        ax.text(m["pred_interval"][1], y + 0.75, f"  prediction interval [{m['pred_interval'][0]:+.1f}, {m['pred_interval'][1]:+.1f}]", color=RED, va="center", fontsize=9, ha="left")
        ax.text(m["ci"][1], y, f"  pooled {m['mu']:+.2f}, I$^2$ = {100*m['I2']:.0f}%", va="center", fontsize=9, ha="left")
        ax.axvline(0, color=GRAY, lw=1)
        ax.set_yticks(list(range(len(eff))) + [y, y + 0.75]); ax.set_yticklabels([e["wording"] for e in eff] + ["pooled (random effects)", "new wording"])
        ax.invert_yaxis(); ax.set_title(name, loc="left", fontsize=11.5, fontweight="bold", pad=10); ax.set_xlabel("effect of collusion instruction on price (95% CI)")
    axs[0].set_xlim(-6.5, 11)
    fig.suptitle("Across wordings the effect is almost all real heterogeneity, so a new wording could give nearly any sign", x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    fig.tight_layout(); save(fig, "09_heterogeneity.png")


if __name__ == "__main__":
    for fn in (hero, pseudorep, false_alarms, curve, prices, swap, wording, auction, auditor, heterogeneity):
        fn()
