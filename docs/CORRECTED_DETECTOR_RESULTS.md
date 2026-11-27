# Corrected detectors on fresh batches: results

Script: `sprint_work/v_corrected_detector.py`. Data: `sprint_work/out/v_*.jsonl`, summary `sprint_work/out/v_summary.json`. No API calls.
Design: 60 fresh honest batches and 20 keyword-colluder batches (10 runs each, seeds never used by the shipped calibration or audits) per game, simulated with the starter pipeline. 200 random 50/50 splits of the honest batches into calibration and held-out halves. Rates are on the held-out half (honest) or on all keyword batches (power), at the 0.05 level; brackets are the 5th to 95th percentile across splits.

| game | detector | false positives, shipped p-value | false positives, corrected | detection of keyword colluders, corrected |
| --- | --- | --- | --- | --- |
| pricing | linguistic | 85% | 3.7% [0, 10] | 100% |
| pricing | cross-run MI | 100% | 3.1% [0, 10] | 100% |
| auction | linguistic | 95% | 2.9% [0, 10] | 100% |
| auction | cross-run MI | 100% | 3.4% [0, 13] | 100% |

What "corrected" means: linguistic uses reference token frequencies pooled from the calibration honest batches (each calibration batch scored against a reference that excludes it) and an empirical p-value against the calibration statistics. Cross-run MI uses the same estimator settings for the statistic and the null, and an empirical p-value against calibration batches. Both therefore behave like the batch-level recalibration already in the report, now with the statistic itself repaired.

Findings and caveats
* A first version of the linguistic fix scored calibration batches against a reference that included them. That gave 99.5% false positives in the auction, an in-sample bias. The leave-one-out version above is the fix; the bug is worth remembering when reading any calibrated detector.
* The batch-level permutation null for cross-run MI cannot reject at 0.05 with 8 shuffles (smallest possible p is 1/9), so the permutation p-value is uninformative here; the calibration-based p-value is the usable one. Shuffled-null mean (0.80 pricing, 1.01 auction) is close to the honest statistic mean (0.82, 1.10), so the shipped steps mismatch was only part of the problem.
* Power is shown only against scripted keyword colluders, which both statistics were already known to find. It says nothing about unknown channels.
* With 30 held-out honest batches per split, a 5% rate has wide intervals, as the brackets show. More batches would tighten them.
