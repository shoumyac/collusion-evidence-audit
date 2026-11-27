# Re-audit of two published LLM collusion evaluations (27 Nov 2026)

We applied the replication-unit and calibration checks from our report to the two recent papers that released enough raw data to do it. The question was whether their headline claims survive cluster-aware, multiplicity-aware inference. Short answer: mostly yes. This is a robustness result with a few specific corrections, not a refutation.

Scope. Re-analysed: Shi et al. (2609.24967, Emergent Collusion in Long-Horizon LLM Agent Interaction) and Cahyono (2610.39660, Sticky Collusion). Not re-analysed: Tran and Yu (their repo ships code and an anonymised software zip, no transcripts that I found), Colosseum (the repo has code only, no logs), and Lee and Park, PoPLi, Xu et al. (no released data that I checked). Scripts are in `reaudit/`.

## 1. Reproduction

| Paper | Check | Result |
| --- | --- | --- |
| Sticky Collusion | Authors' `make_figures.py` run on the released slim runs | `numbers.json` is identical to the shipped file (1,325 runs, 6,041 episodes) |
| Shi et al. | EC, TC and CC for all 10 models recomputed from the released episode files | All 30 values match Table 1 exactly. CC matches when the "at least half remaining" count includes the onset episode, which the paper does not spell out in the main text |

## 2. Sticky Collusion

1. **Selection of histories does not drive the results.** The paper analyses the first 15 histories per model that formed collusion. Re-running every main arm on all available histories (17 for GPT-6-Luna, 16 for DeepSeek, 24 for Gemini) moves no estimate by more than 4.6 points and flips no conclusion (for example Gemini told: 97.3% to 92.7%; GPT-6-Luna silent stop: 78.1% to 79.5%).
2. **Conditioning on formation cannot be quantified from the release.** The exported builds contain almost only runs that formed collusion (Gemini onset builds: 9 of 10 and 6 of 10). DeepSeek's second build was stopped once six repeats had formed collusion. The formation rate is therefore unknown, and every claim is conditional on formation. The paper says this, but the denominator should be released.
3. **Zero-width intervals.** The percentile bootstrap over histories returns [0, 0] or [100, 100] in 8 of 18 cells I recomputed (all the 0% wipe cells and the 100% DeepSeek and Gemini cells). Exact history-level intervals are wider: 15 of 15 histories colluding gives a 95% lower bound of about 78%, and 0 of 15 gives an upper bound of about 22%. "100%" and "0%" are best read as "at least about 78%" and "at most about 22%" of histories.
4. **Episode-level intervals are too narrow, cluster intervals are right.** Design effects (cluster variance over binomial variance) are 1.0 to 3.9 where defined, for example 3.8 for Gemini with the chat removed (cluster interval 29 to 64%, naive episode interval 38 to 56%). The authors already use history-level resampling, so their intervals are fine.
5. **No multiplicity correction.** `numbers.json` records 79 tests. 33 have raw p below 0.05. 12 survive Holm and 29 survive Benjamini-Hochberg at 5%. The wipe-versus-keep results (p about 6e-5) survive everything. Several mid-strength claims do not survive Holm, for example the Gemini re-formation result (p = 0.0034, Holm-adjusted 0.22, BH 0.014) and the GPT-6-Luna re-formation of collusion (p = 0.039, BH 0.09). Holm is conservative here because several tests share outcomes, so treat BH as the more reasonable bar. Recommendation: label the tiers as confirmatory (wipe, silent stop) and exploratory (the rest).

## 3. Shi et al.

1. **Task sequences are close to exchangeable across models.** Per-sequence collusion correlates weakly across models (mean pairwise r = 0.11, ICC = 0.06). Treating trajectories as independent is reasonable here, so the pseudoreplication concern does not apply to the main table.
2. **"More capable models in the same family collude earlier" holds in 3 of 4 families.** Paired by task sequence, difference in episode-level collusion (cluster bootstrap 95% CI): Gemini 3.7 Flash minus 3.1 Flash-Lite +43.4 points [37.2, 49.4]; Claude Opus minus Sonnet +10.2 [6.6, 13.6]; Qwen 3.8 minus 3.6 +10.8 [5.6, 15.2]. All three survive Holm across the four contrasts. GPT-5.6 Terra minus Luna is +3.8 [-6.6, +13.6] with onset at episode 4.9 versus 4.6, so there is no effect. The paper does not define the capability ordering, and for the GPT pair there is nothing to order.
3. **Mutual ACCEPT is close to a rubber stamp.** Across all 10,000 agent verdicts, agents accept correct peer work 75.1% of the time and wrong peer work 66.8%. The pooled difference is 8.3 points [5.4, 11.4] with trajectory clustering. Only 1,068 of the 10,000 peer tasks were wrong, so per-model estimates are noisy. This supports reading the behaviour as skipping verification rather than as honest judgment on summaries, which our own say-versus-do argument needs and which the paper does not report.
4. **Ceiling on the trajectory-level rate.** Eight of ten models have TC of at least 92%, so TC barely separates models. EC and CC carry the signal.

## 4. What this means for our paper

* The "published claims break under replication-unit audits" story is not supported for these two papers. Both already resample at the trajectory or history level. Say so plainly and credit them.
* What we can add that is true and checkable: degenerate-interval handling for boundary rates, a multiplicity tier table, an unreported discrimination analysis (accept versus peer correctness), and the formation-rate denominator problem.
* The pseudoreplication hook is stronger for papers with 3 to 10 runs per cell and no released logs (Lee and Park, PoPLi, parts of Colosseum). Those need the authors' data or a rerun.
* The discrimination analysis in section 3.3 is a good fit for our instruction-versus-decision framing and could become a short section in the report.
