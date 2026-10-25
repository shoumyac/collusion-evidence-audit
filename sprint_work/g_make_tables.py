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
            f"{f(s5['rate']) if s5 else '--'} & {f(r['heldout_fpr']) if r else '--'} & "
            f"{f(r['tpr_keyword']) if r else '--'} & {f(r['tpr_sparse']) if r and r['tpr_sparse'] else '--'} \\\\")
tab1 = ("\\begin{tabular}{llrrrrrrr}\n\\toprule\n"
        " & & \\multicolumn{4}{c}{shipped p-values} & \\multicolumn{3}{c}{recalibrated on batches (held out)}\\\\\n"
        "\\cmidrule(lr){3-6}\\cmidrule(lr){7-9}\n"
        "scenario & detector & honest@.05 & honest@.01 & keyword@.05 & sparse@.05 & FPR & TPR kw & TPR sp \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table1.tex").write_text(tab1)

L = N["LLM"]
lrows = []
for tag, label in (("Qwen2.5-7B-Instruct", "Qwen2.5-7B"), ("claude-haiku-5-5", "Claude Haiku 5.5"),
                   ("claude-sonnet-5-5", "Claude Sonnet 5.5")):
    d = L[tag]
    h, c = d["conditions"]["honest"], d["conditions"]["collude"]
    rp = d["repo_detectors"]
    a = d["auditor"]
    lrows.append(
        f"{label} & {h['runs']}/{c['runs']} & {h['mean_price']:.2f} & {c['mean_price']:.2f} & {c['refusal_msg_rate']:.2f} & "
        f"{rp['honest|cross_run_mi']['frac_p_le_0.01']:.2f}/{rp['honest|welfare_shift']['frac_p_le_0.01']:.2f} & "
        f"{d['say_vs_do']['auroc_say_only']:.2f}/{d['say_vs_do']['auroc_do_only']:.2f}/{d['say_vs_do']['auroc_combined']:.2f} & "
        f"{a['say']['auroc']:.2f}/{a['do']['auroc']:.2f}/{a['both']['auroc']:.2f} \\\\")
tab2 = ("\\begin{tabular}{lrrrrrcc}\n\\toprule\n"
        "agent model & runs h/c & price h & price c & refusal c & repo flags h (MI/welf.) & NB AUROC s/d/b & Claude auditor AUROC s/d/b \\\\\n\\midrule\n"
        + "\n".join(lrows) + "\n\\bottomrule\n\\end{tabular}\n")
(out / "table2.tex").write_text(tab2)
print(tab1)
print(tab2)
