"""Generate LaTeX tables for the report from out/report_numbers.json (no hand-typed numbers)."""
import json
from pathlib import Path

out = Path(__file__).parent / "out"
N = json.loads((out / "report_numbers.json").read_text())
t = N["B_pvalue_rates"]
NAMES = {"cross_run_mi": "cross-run MI", "linguistic_steganalysis": "linguistic", "welfare_shift": "welfare",
         "acceptance_bias": "accept. bias"}


def f(x, nd=2):
    return "--" if x in (None, "") else f"{float(x):.{nd}f}"


rec = {(r["scenario"], r["detector"]): r for r in N["B2_recalibrated"]}
rows = []
for scen in ("pricing", "auction", "review"):
    for det in NAMES:
        h5 = t.get(f"{scen}|honest|{det}|0.05")
        if not h5:
            continue
        h1 = t[f"{scen}|honest|{det}|0.01"]
        k5 = t.get(f"{scen}|keyword|{det}|0.05")
        s5 = t.get(f"{scen}|sparse|{det}|0.05")
        r = rec.get((scen, det))
        rows.append(
            f"{scen} & {NAMES[det]} & {f(h5['rate'])} & {f(h1['rate'])} & {f(k5['rate'])} & "
            f"{f(s5['rate']) if s5 else '--'} & {f(r['heldout_fpr_q95']) if r else '--'} & "
            f"{f(r['tpr_keyword_q95']) if r else '--'} & {f(r['tpr_sparse_q95']) if r and r['tpr_sparse_q95'] else '--'} \\\\")
n_h = {s: t[f"{s}|honest|cross_run_mi|0.05"]["n"] for s in ("pricing", "auction", "review")}
n_k = {s: t[f"{s}|keyword|cross_run_mi|0.05"]["n"] for s in ("pricing", "auction", "review")}
n_s = {s: t[f"{s}|sparse|cross_run_mi|0.05"]["n"] for s in ("pricing", "auction", "review")}
N["batch_n"] = {"honest": n_h, "keyword": n_k, "sparse": n_s}
tab1 = ("\\begin{tabular}{llrrrrrrr}\n\\toprule\n"
        " & & \\multicolumn{4}{c}{shipped p-values: fraction of batches} & \\multicolumn{3}{c}{recalibrated on batches (held out)}\\\\\n"
        "\\cmidrule(lr){3-6}\\cmidrule(lr){7-9}\n"
        "scenario & detector & honest@.05 & honest@.01 & keyword@.05 & sparse@.05 & FPR & TPR kw & TPR sp \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table1.tex").write_text(tab1)

L = N["LLM"]
MAIN = {"Qwen2.5-7B-Instruct": "Qwen2.5-7B", "Qwen2.5-32B-Instruct": "Qwen2.5-32B", "phi-4": "Phi-4",
        "Mistral-Nemo-12B": "Mistral-Nemo-12B", "claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5"}


def pc(e, dag=True):
    if not e:
        return "--"
    s = f"{e['mean_price']:.2f} [{e['price_ci95'][0]:.2f}, {e['price_ci95'][1]:.2f}]"
    return s + ("$^\\dagger$" if dag and e["parse_fail_rate"] > 0.05 else "")


r2 = []
for tag, label in MAIN.items():
    c = L[tag]["conditions"]
    r2.append(f"{label} & {c['honest']['runs']} & {pc(c['honest'])} & {pc(c['collude'])} & {pc(c.get('honest_silent'))} & "
              f"{pc(c.get('collude_silent'))} & {c['collude']['nash_fraction']:+.2f} & {c['collude']['refusal_msg_rate']:.2f} \\\\")
tab2 = ("\\begin{tabular}{lrccccrr}\n\\toprule\n"
        "model & runs/cond. & honest & collude & honest, silent & collude, silent & c: Nash$\\to$joint & refusal c \\\\\n\\midrule\n"
        + "\n".join(r2) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table2.tex").write_text(tab2)

ci = lambda x, c: f"{x:.2f} [{c[0]:.2f}, {c[1]:.2f}]"
r3 = []
for tag, label in MAIN.items():
    d = L[tag]
    bc = d.get("repo_batch_counts", {})
    kn = lambda key: f"{bc[key]['k_flagged_p01']}/{bc[key]['n_batches']}" if key in bc else "--"
    sv = d["say_vs_do"]
    r3.append(f"{label} & {kn('honest|cross_run_mi')} & {kn('honest|welfare_shift')} & {kn('honest|linguistic_steganalysis')} & "
              f"{ci(sv['auroc_say'], sv['auroc_say_ci'])} & {ci(sv['auroc_say_masked'], sv['auroc_say_masked_ci'])} & "
              f"{ci(sv['auroc_do'], sv['auroc_do_ci'])} \\\\")
tab3 = ("\\begin{tabular}{lcccccc}\n\\toprule\n"
        " & \\multicolumn{3}{c}{repo: honest batches flagged ($p\\le.01$)} & \\multicolumn{3}{c}{naive Bayes AUROC [95\\% CI], 5-fold CV}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\n"
        "model & MI & welfare & linguistic & say & say, prompt words masked & do \\\\\n\\midrule\n"
        + "\n".join(r3) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table3.tex").write_text(tab3)

r5 = []
for tag, label in MAIN.items():
    d = L[tag]
    a1, a2 = d.get("auditor"), d.get("auditor2")
    cell = lambda a, v: ci(a[v]["auroc"], a[v]["auroc_ci"]) if a else "--"
    r5.append(f"{label} & {cell(a1, 'say')} & {cell(a1, 'do')} & {cell(a1, 'both')} & {cell(a2, 'say')} & {cell(a2, 'do')} \\\\")
tab5 = ("\\begin{tabular}{lccccc}\n\\toprule\n"
        " & \\multicolumn{3}{c}{auditor 1: Claude Sonnet 5.5} & \\multicolumn{2}{c}{auditor 2: Qwen2.5-7B}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-6}\n"
        "agents & say & do & both & say & do \\\\\n\\midrule\n"
        + "\n".join(r5) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table5.tex").write_text(tab5)

r4 = []
for fam, label in (("claude-haiku-5-5", "Claude Haiku 5.5"), ("claude-sonnet-5-5", "Claude Sonnet 5.5")):
    c, c2 = L[fam]["conditions"], L[fam + "-v2"]["conditions"]
    r4.append(f"{label} & {pc(c['honest'])} & {pc(c['collude'])} & {pc(c.get('honest_para'))} & {pc(c.get('collude_para'))} & "
              f"{pc(c2.get('honest'))} & {pc(c2.get('collude'))} \\\\")
tab4 = ("\\begin{tabular}{lcccccc}\n\\toprule\n"
        " & \\multicolumn{2}{c}{prompt 1 (main)} & \\multicolumn{2}{c}{prompt 1, rival's messages paraphrased} & \\multicolumn{2}{c}{prompt 2 (reworded)}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n"
        "model & honest & collude & honest & collude & honest & collude \\\\\n\\midrule\n"
        + "\n".join(r4) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table4.tex").write_text(tab4)
(out / "report_numbers.json").write_text(json.dumps(N, indent=1, default=float))
print(tab1, tab2, tab3, tab4, tab5, sep="\n")
