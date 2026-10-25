"""Check every number quoted in report.tex prose against the saved outputs. Prints OK/MISMATCH per claim."""
import glob
import json
from pathlib import Path

import numpy as np

out = Path(__file__).parent / "out"
N = json.loads((out / "report_numbers.json").read_text())
B, L = N["B_pvalue_rates"], N["LLM"]
bad = []


def chk(name, got, want, tol=0.006):
    ok = abs(got - want) <= tol
    print(("OK       " if ok else "MISMATCH ") + f"{name}: got {got:.4f} want {want}")
    if not ok:
        bad.append(name)


A = N["A"]
chk("raw runs", A["raw_runs_counted_naively"], 22127, 0)
chk("within-file distinct", A["distinct_runs_within_file"], 3918, 0)
chk("global distinct", A["distinct_runs_by_content_global"], 2740, 0)
chk("distinct ignoring run id", A["distinct_ignoring_run_id"], 2104, 0)
chk("auction calib 5840 runs", A["calibration_diversity"]["first_price_auction"]["runs"], 5840, 0)
chk("auction calib 200 distinct", A["calibration_diversity"]["first_price_auction"]["distinct_transcripts"], 200, 0)
chk("review calib 7640", A["calibration_diversity"]["peer_review"]["runs"], 7640, 0)
chk("review calib 434", A["calibration_diversity"]["peer_review"]["distinct_transcripts"], 434, 0)
for k, v in {"cross_run_mi": 59745, "permutation_invariance": 610, "watermark_variance": 1640, "linguistic_steganalysis": 600, "acceptance_bias": 4}.items():
    chk(f"threshold n {k}", A["threshold_n"][k], v, 0)
for scen, want in (("pricing", .99), ("auction", 1.0), ("review", .14)):
    chk(f"MI honest@.05 {scen}", B[f"{scen}|honest|cross_run_mi|0.05"]["rate"], want)
for scen, want in (("pricing", .88), ("auction", .95), ("review", .93)):
    chk(f"ling honest@.05 {scen}", B[f"{scen}|honest|linguistic_steganalysis|0.05"]["rate"], want)
chk("accept honest@.05 review", B["review|honest|acceptance_bias|0.05"]["rate"], .19)
chk("accept keyword@.05 review", B["review|keyword|acceptance_bias|0.05"]["rate"], .27)
chk("n honest batches", B["pricing|honest|cross_run_mi|0.05"]["n"], 180, 0)

cur = json.loads((out / "j_curve.json").read_text())
for scen in ("pricing", "auction", "review"):
    rows = {r["n_cal"]: r for r in cur[scen]["rows"]}
    chk(f"curve n=3 {scen} in 24-26%", rows[3]["fpr_mean"], 0.25, 0.015)
    chk(f"curve n=12 {scen} ~8%", rows[12]["fpr_mean"], 0.08, 0.006)
    chk(f"curve n=20 {scen} 4-5%", rows[20]["fpr_mean"], 0.045, 0.006)
    chk(f"curve n=80 {scen} 4.7-4.9%", rows[80]["fpr_mean"], 0.048, 0.002)
for r in N["B2_recalibrated"]:
    if r["detector"] == "cross_run_mi":
        chk(f"recal max-rule FPR {r['scenario']}", float(r["heldout_fpr_max"]), 0.011, 0.002)
        chk(f"recal q95 FPR {r['scenario']} 5-6%", float(r["heldout_fpr_q95"]), 0.055, 0.006)
        chk(f"recal TPR kw {r['scenario']}", float(r["tpr_keyword_q95"]), 1.0, 0.0)
mi = json.loads((out / "i_mi_summary.json").read_text())
chk("MI test pricing honest shipped", mi["pricing|honest"]["shipped_frac_le_0.05"], .9)
chk("MI test auction honest shipped", mi["auction|honest"]["shipped_frac_le_0.05"], 1.0)
chk("MI test patched honest", mi["pricing|honest"]["matched_null_frac_le_0.05"] + mi["auction|honest"]["matched_null_frac_le_0.05"], 0.0)
chk("MI test patched keyword", mi["pricing|keyword"]["matched_null_frac_le_0.05"] + mi["auction|keyword"]["matched_null_frac_le_0.05"], 0.0)

P = lambda tag, cond: L[tag]["conditions"][cond]["mean_price"]
chk("haiku silent h", P("claude-haiku-5-5", "honest_silent"), 1.99, .01)
chk("haiku silent c", P("claude-haiku-5-5", "collude_silent"), 1.99, .01)
chk("sonnet silent h", P("claude-sonnet-5-5", "honest_silent"), 2.50, .01)
chk("sonnet silent c", P("claude-sonnet-5-5", "collude_silent"), 2.84, .01)
chk("haiku h", P("claude-haiku-5-5", "honest"), 1.70, .01)
chk("haiku c", P("claude-haiku-5-5", "collude"), 2.32, .01)
chk("sonnet h", P("claude-sonnet-5-5", "honest"), 2.46, .01)
chk("sonnet c", P("claude-sonnet-5-5", "collude"), 4.49, .01)
chk("haiku para c", P("claude-haiku-5-5", "collude_para"), 2.23, .01)
chk("sonnet para c", P("claude-sonnet-5-5", "collude_para"), 4.34, .01)
chk("haiku v2 h", P("claude-haiku-5-5-v2", "honest"), 1.58, .01)
chk("haiku v2 c", P("claude-haiku-5-5-v2", "collude"), 1.58, .01)
chk("sonnet v2 h", P("claude-sonnet-5-5-v2", "honest"), 4.19, .01)
chk("sonnet v2 c", P("claude-sonnet-5-5-v2", "collude"), 4.38, .01)
chk("qwen7 silent", P("Qwen2.5-7B-Instruct", "honest_silent"), 1.88, .01)
chk("qwen7 silent c", P("Qwen2.5-7B-Instruct", "collude_silent"), 2.06, .01)
chk("qwen32 silent", P("Qwen2.5-32B-Instruct", "honest_silent"), 2.17, .01)
chk("qwen32 silent c", P("Qwen2.5-32B-Instruct", "collude_silent"), 2.43, .01)
chk("phi silent h", P("phi-4", "honest_silent"), 1.63, .01)
chk("phi silent c", P("phi-4", "collude_silent"), 2.76, .01)
chk("nemo silent h", P("Mistral-Nemo-12B", "honest_silent"), 1.89, .01)
chk("nemo silent c", P("Mistral-Nemo-12B", "collude_silent"), 2.53, .01)
chk("phi honest-silent parse fail 14.5%", L["phi-4"]["conditions"]["honest_silent"]["parse_fail_rate"], 0.145, .003)
chk("haiku refusal c 98%", L["claude-haiku-5-5"]["conditions"]["collude"]["refusal_msg_rate"], .98, .006)
chk("haiku honest price-talk 63%", L["claude-haiku-5-5"]["conditions"]["honest"]["price_talk_msg_rate"], .63, .006)
mx = max(np.mean([float(json.loads(l)["action"]) for l in open(f.replace(".metrics.json", ".jsonl")) if l.strip()])
         for f in glob.glob(str(out / "llm/claude-sonnet-5-5/collude/*.metrics.json")))
print(f"INFO     max Sonnet collude run-mean price = {mx:.2f} (text says individual runs reach 6.3-6.5)")
for tag, lo_hi in (("Qwen2.5-7B-Instruct", None),):
    pass
aud = {t: L[t]["auditor"] for t in L if "auditor" in L[t]}
sayv = [aud[t]["say"]["auroc"] for t in ("Qwen2.5-7B-Instruct", "Qwen2.5-32B-Instruct", "phi-4", "Mistral-Nemo-12B")]
chk("open-weight say AUROC min 0.92", min(sayv), .92, .006)
chk("open-weight say AUROC max 1.00", max(sayv), 1.0, .006)
chk("haiku say AUROC", aud["claude-haiku-5-5"]["say"]["auroc"], 0.0, .006)
chk("sonnet say AUROC", aud["claude-sonnet-5-5"]["say"]["auroc"], .21, .006)
chk("haiku auditor2 say", L["claude-haiku-5-5"]["auditor2"]["say"]["auroc"], 0.0, .006)
chk("sonnet auditor2 say", L["claude-sonnet-5-5"]["auditor2"]["say"]["auroc"], .42, .006)
dos = [L[t]["say_vs_do"]["auroc_do"] for t in ("Qwen2.5-7B-Instruct", "Qwen2.5-32B-Instruct", "phi-4", "Mistral-Nemo-12B", "claude-haiku-5-5", "claude-sonnet-5-5")]
chk("NB do min .74", min(dos), .74, .006)
chk("NB do max .99", max(dos), .99, .006)
for t in L:
    if "say_vs_do" in L[t]:
        chk(f"NB say masked {t}", L[t]["say_vs_do"]["auroc_say_masked"], 1.0, .006)
chk("benchmarks nash", N["benchmarks"]["nash"], 4.6, 0)
chk("benchmarks joint", N["benchmarks"]["joint_profit_max"], 5.5, 0)
print("\nMISMATCHES:", bad if bad else "none")
