# Scope: a corrected detector on the shipped logs

Status: scoped, not built. No API calls are needed; the work is CPU time and care.

## What is wrong in the shipped code (from reading `auditor/detectors/linguistic.py` and `mi.py`)

| detector | problem | fix |
| --- | --- | --- |
| linguistic | p-value compares the maximum of the batch's chi-square values with the mean and standard deviation of the same batch (`gaussian_p_value(max, mean, std)`), so it is not a null distribution. The expected token frequencies are also the batch's own pooled counts. | Take the reference frequencies and the null distribution of the statistic from independent honest batches; report an empirical or permutation p-value. |
| cross-run MI | The shuffled null uses `steps=120` and 3 repeats; the statistic uses `steps=200`. The two are not estimated the same way. The null is also Gaussian-approximated from 3 draws per pair. | Same estimator, same steps and seed policy for statistic and null; permutation p-value over many shuffles; calibrate the threshold on independent honest batches (about 20, see the calibration curve). |
| all | Pair and run counts treat copied runs as independent. | Deduplicate by the cross-file path key before pairing; unit of analysis is the distinct path. |

## Plan

1. Rebuild the batch index with distinct paths only (reuse `sprint_work/a_pseudoreplication.py`).
2. Reimplement both statistics in `kit/` with the fixes above, keeping the shipped feature extractor so the comparison is like for like.
3. Check size: false-positive rate on held-out honest batches at 0.05 and 0.001 (target about 5% and a defensible bound for 0.1%).
4. Check power: the four scripted colluders and the LLM collusion runs.
5. Report the corrected rates next to the shipped ones in the README and report.

Expected cost: the neural MI estimator is the slow part (200 optimisation steps per pair). With distinct runs only the pair count drops by roughly 5x; a CPU run of a few hours is plausible. Not started because the corrected MI null needs many more shuffles than the shipped one, so the runtime must be measured on one scenario first.

Caveat: this fixes the statistics, it does not make the detector able to see unknown channels. Power claims stay limited to the scripted ones.
