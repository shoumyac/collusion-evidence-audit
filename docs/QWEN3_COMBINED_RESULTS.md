# Qwen3-8B vs Qwen3-32B: does the audit pattern replicate?

Same design for both models (vLLM on Modal, thinking off, temperature 0.7, three games, three wordings, six conditions). 8B: 100 runs per cell, complete. 32B: 50 runs per cell, 2,401 of 2,700 runs; Cournot wording 3 is missing because the background job hit its time limit. Effects are collude minus honest on the game outcome, with run-level bootstrap intervals. Details for the 8B are in QWEN3_8B_RESULTS.md. Raw runs are in results/qwen3_8b and results/qwen3_32b.

## Instruction effect

| Game | Qwen3-8B | Qwen3-32B |
|---|---|---|
| Pricing (price, collusive = up) | +1.88 to +2.74 | +0.57 to +0.65 |
| Auction (winning bid, collusive = down) | -4.88 to -5.52 | -1.23, -0.37 (interval touches 0), -1.69 |
| Cournot (total quantity, collusive = down) | -6.3 to -9.7 | +1.19 [0.36, 1.99], +2.04 [1.26, 2.83] (wrong direction) |

Levels matter as much as effects. In pricing the instructed 8B prices at about 8.0 to 8.5, far above the joint-profit price of 5.5, while the 32B prices at 5.6 to 6.0, close to it. Uninstructed prices are 5.6 to 6.1 (8B) and 5.0 to 5.4 (32B).

## Controls

- Swap control: replaying partner messages does not change the effect for either model. Intact minus swapped differences are within -0.35 to 0.49 (8B) and -0.10 to 0.21 in pricing and auction (32B, differences up to 1.2 in Cournot wording 2 where the effect itself is small and noisy).
- Opt-out control: no material change for either model in pricing. In the 8B auction the opt-out lowers the bid to near the reserve in two of three wordings.

## What this supports

1. Instruction-versus-decision confound is real in a second model family size: instructed outcomes shift with no partner involvement, so an outcome-only detector cannot separate following an instruction from collusive coordination.
2. The partner-independence result (swap) replicates at both sizes.
3. Effect size is not stable across capability. The smaller model overshoots; the larger model hits the benchmark more closely with a much smaller shift. A fixed detection threshold calibrated on one model would misfire on the other.
4. Cournot is not a valid test here. The 8B plays 10 each (total 20, price 0). The 32B instructed play moves up toward 10 per firm (total about 18), the wrong direction, apparently reading "coordinate" as a salient number rather than computing the cooperative quantity.

## Limits

One model family, two sizes, thinking off, no judge-based say-versus-do analysis, 50 runs per 32B cell, and Cournot wording 3 missing for the 32B. No multiplicity correction (the auction wording 2 32B result is the only one near zero). Cost was not logged by the runner; check Modal billing.


## Addendum: third model (Microsoft Phi-4, 14B) and Cournot wording 5

Phi-4 was run at 50 runs per cell on pricing, auction and Cournot wordings 1 to 3 and Cournot wording 5 (3,000 planned runs, 2,929 saved; Cournot wording 3 is partial, with 29 to 50 runs per cell). Raw runs are in results/phi4.

| Game | Instruction effect, Phi-4 (collude minus honest) |
|---|---|
| Pricing | +2.41 [2.16, 2.66], +2.12 [1.89, 2.34], +2.28 [2.10, 2.48]; instructed price about 7.1 |
| Auction | -0.68 [-1.21, -0.15], +0.14 [-0.32, 0.59], -1.05 [-1.85, -0.35] |
| Cournot | -2.60, -3.48, -4.14 (wording 3 partial); wording 5 -2.18 [-2.87, -1.48] |

- Swap control: intact minus swapped differences are between -0.58 and 0.24 in every cell. The partner-independence result now holds for three models.
- Opt-out: no material change in pricing or Cournot. Explicit decline statements appear in at most 3% of opt-out messages (Phi-4), and in none for the Qwen models.
- Cournot is a valid test for Phi-4. It moves total quantity toward the collusive total in all wordings, so the Qwen failure is a model capability issue, not a flaw in the game. The worked-example wording 5 was not needed for Phi-4 and was not run on the Qwen models (that would need redeploying them).
- Effect size again depends on the model. Pricing effects are 1.9 to 2.7 (Qwen3-8B), 0.6 (Qwen3-32B) and 2.1 to 2.4 (Phi-4), so effect size does not track parameter count; it varies by model.
- Say-versus-do (keyword screen, see SAY_DO_KEYWORD_PASS.md): Phi-4 shows no gap in pricing (say 0.70 to 0.84, do 0.98 to 1.00), but a modest one in the auction, where under instruction 16 to 23% of rounds contain coordination language without a collusive bid, with the caveat that the screen is crude.
