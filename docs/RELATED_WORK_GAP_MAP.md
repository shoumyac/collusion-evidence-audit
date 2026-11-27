# Related work and gap map (read 27 Nov 2026)

Method: searched alphaXiv for 2025 to 2026 papers on LLM collusion, steganographic collusion, detection and evaluation statistics, then read the relevant pages of ten papers (method, results and limitations). Papers marked "abstract only" were not read in full. Numbers below are as reported by each paper.

## 1. What each paper does and where it is limited

| Paper | What it does | Limits (stated by authors, or visible in the design) |
| --- | --- | --- |
| What Do Collusion Probes Read? (Mohsin and Rahman, arXiv 2611.10620) | Shows white-box collusion probes mostly detect that an agent was told to collude. Adds agents that receive the instruction and refuse it, and a no-instruction control. Without the instruction, agent AUROC falls from 1.00 to 0.61. Proposes a control checklist. | Collusion is instructed or fine-tuned from instructed replies. Probes need white-box access. Qwen3 and Mistral-Small only, 4-bit. Two task formats written by one author. Labels come from the generator. Emergent collusion untested (a bag-of-words classifier reaches 0.89 where the probe is at chance). A 1% false-alarm threshold became 2.5% and 4.0% on a new task. |
| Is Anyone Enforcing the Cartel? (Tran and Yu, 2610.28787) | Audits whether a cartel-like outcome is enforced by forcing a deviation in cloned markets. Finds prompted LLMs rarely punish and most reach cartel-like prices through rules that ignore the market. | One main prompt plus up to three wordings on three models, and levels are wording-sensitive, so conclusions are drawn only from contrasts within a prompt. Events within a session are not independent. Stylised markets. Small models for the RL part. |
| Faithful yet Collusive (Lee and Park, 2609.18346) | Shows chain-of-thought faithfulness and collusiveness dissociate across nine LLMs in Bertrand duopoly and triopoly. | Two prompts, 3 to 10 runs per cell, Welch tests; frontier-model prompt effects are not significant at n = 3 per cell. Pricing only. An LLM parser extracts the stated graph. No calibration of any detector. |
| Colosseum (Nakamura et al., 2602.15198) | Regret-based and judge-based collusion audit in cooperative multi-agent systems; "collusion on paper"; secret-channel probe on 19 models. | 5 to 10 seeds per cell. Advantage effect across models is not significant (mean +0.31, CI [-0.52, +1.19]); only judge scores rise. DCOP tasks with known coalition membership, homogeneous teams, cannot separate secrecy from extra communication capacity. |
| Collusion with Competitive Marginals (Xu et al., 2607.26385) | Proves single-agent price tests have power equal to their size against a coupling that leaves marginals unchanged. Same-model deployments correlate (+0.053) and different models do not. | Block builders are not LLMs, so the two halves are joined by argument. Thresholds come from sweeps. Rent size depends on the auditor. |
| Partner-Outsider Positive Listening (Denamganai, 2610.37849) | Behavioural test: compare how the intended partner and an uninvolved outsider react to a paraphrased message. | One environment, one model, 10 markets per condition, instructed code, scripted speaker, blind to codes carried by meaning. Message-only monitors failed (flagged 9 of 10 honest markets). |
| Steganalysis of Adaptive Covert Collusion (Ghanem, 2608.02698) | Proposes a black-box detector fusing cross-run MI, permutation tests and timing, calibrated to a fixed false-positive budget, against an adaptive adversary. | The results are labelled placeholders pending measurement. Calibration is described but not measured. |
| Emergent Collusion in Long-Horizon Interaction (Shi et al., 2609.24967) | 94% of trajectories across 10 models drift into joint protocol violation. | 50 trajectories per model, one designed environment, collusion defined as joint violation driven by peer influence. I did not see wording variation across the main runs. |
| Sticky Collusion (Cahyono, 2610.39660) | Collusion persists after incentive removal and partner replacement. | Three models, 15 saved histories each, one game, histories selected for fast collusion, near-100% ceilings, no fixed seeds. Its own market pilots failed because fresh agents had no competitive default. |
| Prompt Optimization Enables Stable Collusion (Tian, 2604.17774) | Optimising a shared meta-prompt yields stable tacit collusion. | Workshop paper. One model, 4 training and 4 test markets, 3 optimisation rounds, one significant round contrast (p = 0.03). |
| Evaluation-statistics papers (Miller 2411.00640; 2610.00651; 2609.30074; 2609.35815; 2511.21140) | Error bars, judge reliability and prompt-set reliability for LLM evaluation. | Abstract only. None addresses detector calibration or collusion. |

## 2. Limitations the field shares

| Code | Shared limitation | Seen in |
| --- | --- | --- |
| L1 | Collusion is instructed or labelled by the instruction, so detectors learn the instruction | Probes paper, Colosseum prompted arm, PoPLi, Ghanem, this project |
| L2 | Few independent units per cell, runs or events treated as independent | Faithful (n = 3 to 10), Colosseum (5 to 10 seeds), PoPLi (10 markets), Sticky (15 histories), Tran and Yu (events) |
| L3 | Wording sensitivity noticed but not estimated | Tran and Yu, Faithful (two prompts), Sakana, this project |
| L4 | Detector thresholds not validated on independent honest data, or validated only as placeholders | Ghanem, probes paper (threshold drift on new task), shipped starter detectors |
| L5 | One game, one model family, or one author's scenarios | Almost all |
| L6 | Outcome or price evidence cannot separate communication, parallel obedience and enforcement | Xu et al., Tran and Yu, this project (swap) |
| L7 | Emergent collusion untested by detectors built on instructed cases | Probes paper, Colosseum, PoPLi |
| L8 | White-box access required | Probes paper, NARCBench |

## 3. Candidate contributions, ranked

| Rank | Contribution | Addresses | Cost | What it adds beyond what exists |
| --- | --- | --- | --- | --- |
| 1 | Re-audit published collusion evaluations with cluster-aware and wording-aware inference. Use released code and trajectories (Shi et al., Sticky, Colosseum, Tran and Yu where released) and report which headline claims survive. | L2, L3 | Free, CPU | Nobody has applied a replication-unit audit to the collusion literature itself. Strong, checkable, and builds on our pseudoreplication method. |
| 2 | Decliner and instruction-removal controls in economic games with black-box detectors. Add a condition where the agent receives the collusion instruction and may decline, plus a no-instruction condition, to pricing and auction. | L1, L6, L8 | Cheap (Haiku), runner exists | The probes paper does this for white-box probes in committee and code-review tasks; nobody has done it for text and outcome detectors in price games. |
| 3 | Measured calibration of black-box detectors on real LLM transcripts: our corrected linguistic and MI detectors, plus a PoPLi-style replay, with false-positive rates on independent honest batches. | L4, L7 | Cheap to moderate | Ghanem proposes this and reports placeholders. We have measured results for scripted agents already. |
| 4 | Wording as a random effect: estimate between-wording variance, give a prediction interval for a new wording, and a rule for how many wordings are needed. Test it on at least 10 systematically generated wordings. | L3 | Moderate | Tran and Yu and Faithful note wording sensitivity but use 2 to 4 prompts and report no variance component. |
| 5 | Same-model dependence: use Xu et al.'s finding (same-model deployments correlate) to test whether runs of one model are exchangeable in our data, and how that changes effective sample size. | L2 | Free | Links the pseudoreplication argument to measured dependence. |
| 6 | Counterfactual deviation test on our own agents (Tran and Yu's audit) to separate parallel obedience from enforcement. | L6 | Moderate | We could say not only that swapping messages does not matter, but that the agents are not enforcing anything. |
| 7 | A short, tested protocol that merges the controls from this project, the probes paper (refusers, instruction removal, before-outcome scoring), PoPLi (partner versus outsider) and Tran and Yu (forced deviations), shipped as the audit kit. | L1 to L6 | Mostly writing | A single usable checklist with code. Must credit the originals clearly. |

## 4. What this means for the paper

* Do not claim novelty for the instruction confound, "collusion on paper", or monitor blindness. Mohsin and Rahman, Colosseum, Lee and Park and Xu et al. already cover versions of these.
* The defensible claim is about evidence standards for black-box and outcome detection in repeated economic games: replication unit, calibration unit, wording variance, and instruction-versus-decision controls, shown to change conclusions in real data.
* The strongest paper is contributions 1, 2, 3 and 4 together, with 7 as the practical output. Contribution 1 is free and should come first because it shows the problem exists beyond our own data.
* Risk: the field is moving quickly. All of these papers appeared between February and November 2026. Check arXiv again before submission.
