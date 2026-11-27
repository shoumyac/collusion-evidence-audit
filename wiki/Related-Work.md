# Related Work

A working list for positioning the next version of the paper. Entries marked **abstract only** were checked from the abstract page, not the full text. Read the full paper before citing it for anything beyond what its abstract says.

## Closest papers found in November 2026

| Paper | What it does (from the abstract) | How it relates to this project | Status |
| --- | --- | --- | --- |
| *Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems*, Nakamura et al., arXiv 2602.15198 (Feb 2026, revised May 2026) | A framework for auditing collusion among LLM agents; measures action-based collusion as regret against the cooperative optimum, compares it with communication-based collusion, and reports "collusion on paper", where agents plan to collude in text but often act non-collusively | Overlaps our say-versus-do finding. We must cite it and say what we add: blind auditors, label-validity controls, and the unit-of-calibration audit of a detector | abstract only |
| *Faithful yet Collusive: Why Chain-of-Thought Monitoring Cannot Detect Collusion in LLM Pricing Agents under Oligopolistic Competition*, arXiv 2609.18346 | Tests nine LLMs in duopoly and triopoly Bertrand competition and finds that collusive behaviour and chain-of-thought faithfulness come apart | Same setting (pricing agents) and a related conclusion about monitors. We study text auditors and calibration instead of chain-of-thought faithfulness | abstract only |
| *Collusion with Competitive Marginals: Price-Level Audits Are Blind by Construction*, Xu et al., arXiv 2607.26385 (Jul 2026) | Argues that tests using a single agent's price history have power equal to their false-positive rate against coordination through the joint distribution of unexplained components. Reports that residual correlation is higher between two deployments of the same model than across models | Complements our result that an outcome (price) detector cannot separate communication from parallel obedience. Their same-model correlation also bears on how independent repeated runs of one model are | abstract only |
| *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations*, Miller, arXiv 2411.00640 (Nov 2024) | Argues evaluations are experiments and should be analysed with standard experimental statistics, including error bars, model comparison and evaluation planning | The standard reference for treating eval results statistically. We extend the spirit to detector calibration and label validity. I did not confirm whether it covers clustered standard errors in detail | abstract only |
| *Flaw or Artifact? Rethinking Prompt Sensitivity in Evaluating LLMs*, arXiv 2509.01790 | Found by title only | May bear on our wording-heterogeneity result | not read |

## Already cited in the report

Mathew et al. and Motwani et al. (secret and steganographic collusion), Fish et al. (LLM pricing agents), Agrawal et al. (communication in double auctions), Cho et al. (collusion without explicit collusion), Tailor (the detector stack we audited, arXiv 2510.04303), Kirchenbauer et al. (watermarks), Hurlbert (pseudoreplication), Ramdas and Vovk (e-values).

## What to do with this

1. Read the three closest papers in full before the next draft.
2. Rewrite the contribution statement so it does not claim novelty over "collusion on paper" or pricing-agent monitors, and states clearly what is new: the calibration unit audit, the label-validity controls with swap and wording, and the evidence ladder.
3. Look for more work on same-model correlation between runs, because it affects how many independent units a batch of runs really contains.
