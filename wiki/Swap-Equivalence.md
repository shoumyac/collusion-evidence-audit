# Swap Equivalence

*Post-sprint analysis, not in the submitted report. Script: `sprint_work/u_equivalence_mediation.py`. Output: `sprint_work/out/u_equivalence_mediation.json` and `table_equivalence.tex`. No API calls.*

## Why this check

The report says that for all six models the interval of (intact effect minus swapped effect) contains zero, and concludes that the price rise is parallel obedience rather than communication. An interval that contains zero shows no detectable difference. It does not show that the difference is small. This analysis asks the stronger question: can we rule out a communication effect of a meaningful size?

## Method

* **Intact effect** = mean(collude) minus mean(honest). **Swapped effect** = mean(collude_swap) minus mean(honest_swap). Both on run-mean prices.
* **D** = intact minus swapped. A positive D means part of the effect runs through reading the real rival's messages.
* **Share through messages** = D divided by the intact effect, with a bootstrap 95% CI (10,000 resamples).
* **Equivalence test (TOST).** Equivalent if the 90% bootstrap interval of D lies inside plus or minus a margin. The margins, 25% and 50% of the intact effect, were written into the script before it was run. They are judgement calls, so read the 50% column as lenient and the 25% column as strict.

## Results

| Set | Intact | Swapped | D [95% CI] | Share through messages [95% CI] | Equivalent at 50% | Equivalent at 25% |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen2.5-7B | +1.04 | +1.00 | +0.05 [-0.09, +0.19] | +4% [-10, +17] | yes | yes |
| Qwen2.5-32B | +0.65 | +0.78 | -0.13 [-0.27, +0.01] | -20% [-48, +2] | yes | no |
| Phi-4 | +1.04 | +1.07 | -0.03 [-0.23, +0.17] | -3% [-24, +15] | yes | yes |
| Mistral-Nemo-12B | +1.19 | +1.20 | -0.01 [-0.71, +0.70] | -0% [-93, +46] | no | no |
| Claude Haiku 5.5 | +0.62 | +0.81 | -0.19 [-0.51, +0.13] | -31% [-110, +17] | no | no |
| Claude Sonnet 5.5 | +2.03 | +1.91 | +0.12 [-0.48, +0.73] | +6% [-28, +31] | yes | no |
| Claude Haiku 5.5, prompt 3 | +0.44 | +0.51 | -0.07 [-0.40, +0.27] | -15% [-159, +46] | no | no |
| Claude Sonnet 5.5, prompt 3 | +2.01 | +1.99 | +0.02 [-0.59, +0.64] | +1% [-33, +29] | yes | no |

## What this says

* **Supported:** Qwen2.5-7B and Phi-4 are equivalent even at the strict 25% margin, so for them messages carry little or none of the effect.
* **Supported at the lenient margin only:** Qwen2.5-32B, Claude Sonnet 5.5 (both prompts). A communication effect up to half the instruction effect cannot be ruled out for Sonnet.
* **Not supported either way:** Mistral-Nemo-12B and Claude Haiku 5.5 (both prompts). Their intervals are too wide, so we cannot say the swap changes nothing. For Haiku the swapped effect is, if anything, larger than the intact one (D is negative).
* **No model** shows a positive share of messages whose interval excludes zero, so there is no evidence for message-mediated coordination in any of them.

So the safe wording for the paper is: *we find no evidence that reading the rival's messages drives the rise, and for four of six models we can rule out a communication share above half of the effect.* "Equivalent for all six models" is not supported.

## Caveats

* Run-mean prices with run-level bootstrap. Repeated price paths would widen the intervals further.
* The margins are our own choice, and the test is one-sided in each direction with a 90% interval by convention.
* 40 to 50 runs per cell, so Haiku and Nemo are underpowered for this question. More runs per cell would help here, unlike in the wording analysis.
