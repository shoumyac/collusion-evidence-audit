# Open-weight replication: Qwen3-8B on pricing, auction and Cournot

Setup: Qwen3-8B served with vLLM on Modal (A100-40GB), thinking off, temperature 0.7. Three games, three wordings, six conditions (honest, collude, collude_optout, and each with the partner messages swapped in), 100 runs per cell, 5,400 runs in total. Metric is the game outcome per run (mean price, mean winning bid, total quantity). Intervals are bootstrap over runs.

## Instruction effect (collude minus honest)

| Game | Wording 1 | Wording 2 | Wording 3 | Benchmark direction |
|---|---|---|---|---|
| Pricing (price) | +2.74 [2.56, 2.92] | +1.88 [1.72, 2.05] | +2.42 [2.19, 2.65] | up = collusive |
| Auction (winning bid) | -5.48 [-5.84, -5.06] | -4.88 [-5.13, -4.64] | -5.52 [-5.82, -5.24] | down = collusive |
| Cournot (total quantity) | -9.27 [-9.56, -8.95] | -6.32 [-6.71, -5.91] | -9.73 [-10.02, -9.43] | down = collusive |

The instruction moves behaviour in the collusive direction in every game and wording. The effect is large relative to run-level noise. Wording changes the size by up to 1.5x (pricing 1.88 to 2.74), so a single wording understates the spread.

## Swap control

Replaying a partner run's messages in place of the live partner leaves the effect unchanged. Intact minus swapped difference in the collude-minus-honest effect:

- Pricing: 0.04, 0.02, 0.31
- Auction: -0.35, -0.02, -0.19
- Cournot: -0.07, 0.49, -0.09

All are small against effects of 2 to 10. Qwen3-8B outcomes are driven by the instruction and the model's own policy, not by reacting to the partner's messages. This is the same pattern the Claude experiments in the report show, so it is a second model family that does not need a partner to produce "collusive" outcomes.

## Decliner (opt-out) control

Telling the model it may decline barely changes outcomes in pricing and Cournot (pricing means 8.22 vs 8.34 w1, 8.02 vs 7.99 w2, 8.20 vs 8.48 w3; Cournot totals 19.9 to 20.0 except w2 at 18.9 vs 20.0). Auction is the exception: wording 1 and 3 drop the winning bid to about 3.5 and 4.0 (near the 3.0 reserve), while wording 2 rises to 7.2. So an outcome-only audit would flag these as collusion even where the instruction was explicitly declinable, which is the instruction-versus-decision confound the report describes.

## Caveats (read before citing)

1. RESOLVED, Cournot is a capability artifact, not collusion. In the collude cells 99.9% of actions are exactly 10 (total 20), which drives the market price to 0 and gives negative profit in every round (for example reward -20). That is above the Nash total of 12 and far from the joint total of 9, so it is not collusive play; the model appears to anchor on half the 0 to 20 range and does not do the price arithmetic. Honest play is a spread of 10 to 18 per firm. Report Cournot as "instruction changes behaviour but not toward the collusive benchmark" and do not count it as a collusion replication. Original note: collude totals sit at 20.0 almost exactly in every wording and swap cell (19.98 to 20.06), and honest totals are far above the Nash total of 12 (26 to 30). This looks like a fixed default quantity or clipping to a bound, not a strategic response. Inspect the raw runs before using Cournot as evidence of anything beyond "the instruction changed a parsed number".
2. Auction honest mean (about 11.5) is above the mean value of 10, so the honest baseline already overbids. The collusive direction there is bidding down toward the reserve.
3. Pricing honest means (5.6 to 6.1) are above the Nash price of 4.6, so the honest baseline is not at Nash either, and the instruction pushes to about 8, beyond the joint-profit price of 5.5.
4. One model, 100 runs per cell, no per-run text judging yet (refusal and say-versus-do rates are not computed here). No multiplicity correction applied; effects are far from any threshold.
5. Cost was not recorded by the runner (it prints $0 for the open-weight backend). Check Modal billing.

## Next

Inspect Cournot raw runs, then run a second model (Qwen3-32B or another family) and the say-versus-do judging pass.
