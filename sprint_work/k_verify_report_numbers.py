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

# ---- additions after the second review round ----
chk("haiku swap c", P("claude-haiku-5-5", "collude_swap"), 2.52, .01)
chk("haiku swap h", P("claude-haiku-5-5", "honest_swap"), 1.71, .01)
chk("sonnet swap c", P("claude-sonnet-5-5", "collude_swap"), 4.39, .01)
chk("sonnet swap h", P("claude-sonnet-5-5", "honest_swap"), 2.49, .01)
chk("haiku v2 auditor say", L["claude-haiku-5-5-v2"]["auditor"]["say"]["auroc"], 0.0, .006)
chk("sonnet v2 auditor say", L["claude-sonnet-5-5-v2"]["auditor"]["say"]["auroc"], .33, .006)
D = json.loads((out / "l_distinct.json").read_text())
chk("haiku honest_silent distinct paths", D["claude-haiku-5-5|honest_silent"]["distinct_price_paths"], 3, 0)
chk("haiku collude_silent distinct paths", D["claude-haiku-5-5|collude_silent"]["distinct_price_paths"], 4, 0)
chk("MI test pricing honest shipped 9/10", mi["pricing|honest"]["shipped_frac_le_0.05"] * mi["pricing|honest"]["n"], 9, 0)
chk("MI test auction honest shipped 10/10", mi["auction|honest"]["shipped_frac_le_0.05"] * mi["auction|honest"]["n"], 10, 0)
print("\nMISMATCHES (after additions):", bad if bad else "none")

for r in N["B2_recalibrated"]:
    if r["detector"] == "cross_run_mi":
        chk(f"recal TPR smart {r['scenario']}", float(r["tpr_smart_q95"]), 1.0, 0.0)
        chk(f"recal TPR adaptive {r['scenario']}", float(r["tpr_adaptive_q95"]), 1.0, 0.0)
        chk(f"n adaptive {r['scenario']}", float(r["n_adaptive"]), 4 if r["scenario"] == "review" else 20, 0)
print("\nMISMATCHES (final):", bad if bad else "none")

# ---- additions: interaction estimates and permutation test (m_permutation_and_interaction.py) ----
IN = json.loads((out / "m_interaction.json").read_text())
PM = json.loads((out / "m_permutation.json").read_text())
for tag, want in (("claude-haiku-5-5", .62), ("claude-sonnet-5-5", 1.69), ("Qwen2.5-7B-Instruct", .86), ("Qwen2.5-32B-Instruct", .38),
                  ("Mistral-Nemo-12B", .55), ("phi-4", -.09)):
    chk(f"interaction {tag}", IN[tag]["interaction_msg_minus_silent"][0], want, .006)
chk("perm mean AUROC min >= .47", min(v[f"perm_mean_{k}"] for v in PM.values() for k in ("say", "say_masked", "do")), .47, .006)
chk("perm mean AUROC max <= .51", max(v[f"perm_mean_{k}"] for v in PM.values() for k in ("say", "say_masked", "do")), .51, .006)
chk("perm max AUROC min .63", min(v[f"perm_max_{k}"] for v in PM.values() for k in ("say", "say_masked", "do")), .63, .006)
chk("perm max AUROC max .71", max(v[f"perm_max_{k}"] for v in PM.values() for k in ("say", "say_masked", "do")), .71, .006)
chk("observed above every shuffle", min(v[f"observed_{k}"] - v[f"perm_max_{k}"] for v in PM.values() for k in ("say", "say_masked", "do")), 0.08, 1)
print("\nMISMATCHES (with interaction/permutation):", bad if bad else "none")

# ---- additions: four prompt wordings and the strict-independent baseline (o_variants.py) ----
OV = json.loads((out / "o_variants.json").read_text())
for tag, want in (("claude-haiku-5-5", .62), ("claude-haiku-5-5-v2", 0.0), ("claude-haiku-5-5-v3", .44), ("claude-haiku-5-5-v4", .01),
                  ("claude-sonnet-5-5", 2.03), ("claude-sonnet-5-5-v2", .19), ("claude-sonnet-5-5-v3", 2.01), ("claude-sonnet-5-5-v4", -.35)):
    chk(f"effect {tag}", OV[tag]["effect"][0], want, .006)
chk("sonnet v4 effect CI upper < 0", min(0, -OV["claude-sonnet-5-5-v4"]["effect"][1][1]), 0.0, 0.0)
chk("sonnet v3 auditor AUROC 1.00", OV["claude-sonnet-5-5-v3"]["auditor_say_auroc"][0], 1.0, .006)
chk("haiku v3 auditor AUROC .06", OV["claude-haiku-5-5-v3"]["auditor_say_auroc"][0], .06, .006)
chk("sonnet v3 honest price-talk 3%", OV["claude-sonnet-5-5-v3"]["msg_rates"]["honest"]["price_stability"], .03, .006)
chk("haiku v3 collude refusal 95%", OV["claude-haiku-5-5-v3"]["msg_rates"]["collude"]["refusal"], .95, .006)
SW = OV["swap_prompt3"]["claude-sonnet-5-5-v3"]
chk("sonnet v3 swap effect 1.99", SW["effect_swap"][0], 1.99, .006)
chk("sonnet v3 main minus swap .02", SW["main_minus_swap"][0], .02, .006)
for tag, n in (("claude-haiku-5-5", 40), ("claude-sonnet-5-5-v4", 40), ("claude-haiku-5-5-v3", 40)):
    chk(f"n runs {tag}", OV[tag]["n"][0] + OV[tag]["n"][1], 2 * n, 0)
print("\nMISMATCHES (with variants):", bad if bad else "none")

# ---- additions: swap control for the open-weight models (Colab run) ----
for tag, want_sw, want_int in (("Qwen2.5-7B-Instruct", 1.00, 1.04), ("Qwen2.5-32B-Instruct", .78, .65), ("phi-4", 1.07, 1.04), ("Mistral-Nemo-12B", 1.20, 1.19)):
    chk(f"swap effect {tag}", IN[tag]["effect_swap"][0], want_sw, .006)
    chk(f"intact effect {tag}", IN[tag]["effect_with_messages"][0], want_int, .006)
for tag in IN:
    if "interaction_main_minus_swap" in IN[tag]:
        lo, hi = IN[tag]["interaction_main_minus_swap"][1]
        chk(f"swap difference CI contains 0: {tag}", float(lo <= 0 <= hi), 1.0, 0.0)
print("\nMISMATCHES (with open-weight swap):", bad if bad else "none")

# ---- additions: path-cluster intervals (p_path_cluster_ci.py) ----
PC = json.loads((out / "p_path_cluster.json").read_text())
chk("sonnet messages effect (cluster file)", PC["claude-sonnet-5-5"]["messages"]["effect"], 2.03, .006)
chk("sonnet cluster CI lower 1.56", PC["claude-sonnet-5-5"]["messages"]["ci_clusters"][0], 1.56, .006)
chk("sonnet cluster CI upper 2.53", PC["claude-sonnet-5-5"]["messages"]["ci_clusters"][1], 2.53, .006)
chk("haiku silent cluster CI lower -0.05", PC["claude-haiku-5-5"]["silent"]["ci_clusters"][0], -.05, .006)
chk("haiku silent cluster CI upper 0.11", PC["claude-haiku-5-5"]["silent"]["ci_clusters"][1], .11, .006)
for tag in PC:
    chk(f"message effect cluster CI excludes 0: {tag}", float(PC[tag]["messages"]["ci_clusters"][0] > 0), 1.0, 0.0)
print("\nMISMATCHES (with cluster CIs):", bad if bad else "none")

# ---- additions: second game, first-price auction (r_auction_analysis.py) ----
AU = json.loads((out / "r_auction.json").read_text())
Hh, Ss = AU["claude-haiku-5-5"], AU["claude-sonnet-5-5"]
chk("auction haiku honest 10.05", Hh["mean_price"]["honest"], 10.05, .006)
chk("auction haiku collude 9.99", Hh["mean_price"]["collude"], 9.99, .006)
chk("auction sonnet honest 9.85", Ss["mean_price"]["honest"], 9.85, .006)
chk("auction sonnet collude 4.51", Ss["mean_price"]["collude"], 4.51, .006)
chk("auction sonnet swapped 4.73", Ss["mean_price"]["collude_swap"], 4.73, .006)
chk("auction sonnet effect -5.34", Ss["effect"][0], -5.34, .006)
chk("auction sonnet effect CI", Ss["effect"][1], -5.55, .006); chk("auction sonnet effect CI hi", Ss["effect"][2], -5.13, .006)
chk("auction sonnet intact minus swapped -0.21", Ss["intact_minus_swapped"][0], -.21, .006)
chk("auction sonnet intact minus swapped CI lo", Ss["intact_minus_swapped"][1], -.42, .006)
chk("auction sonnet intact minus swapped CI hi", Ss["intact_minus_swapped"][2], .005, .006)
chk("auction share of effect ~4%", abs(Ss["intact_minus_swapped"][0] / Ss["effect"][0]), .04, .005)
chk("auction flag intact 100%", Ss["flag_intact"], 1.0, 0); chk("auction flag swapped 100%", Ss["flag_swapped"], 1.0, 0)
chk("auction flag honest swapped 2.5%", Ss["flag_honest_swap"], .025, 1e-9)
chk("auction swapped collude effect -5.16", Ss["swap_effect"][0], -5.16, .006)
chk("auction sonnet profit 0.55 -> 2.05", Ss["bidder_profit"]["honest"], .55, .006); chk("auction sonnet profit collude", Ss["bidder_profit"]["collude"], 2.05, .006)
chk("auction haiku effect -0.07", Hh["effect"][0], -.07, .006)
chk("auction haiku swapped effect +0.06", Hh["swap_effect"][0], .06, .006)
chk("auction n per cell", min(Ss["n"].values()) + min(Hh["n"].values()), 80, 0)
print("\nMISMATCHES (with auction):", bad if bad else "none")
AU = json.loads((out / "r_auction.json").read_text())
chk("auction haiku refusal share 39%", AU["claude-haiku-5-5"]["refusal_share_collude"], .39, .005)
print("\nMISMATCHES (final):", bad if bad else "none")
