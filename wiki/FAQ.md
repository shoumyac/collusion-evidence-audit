# FAQ

Plain answers to the questions people ask first.

## What is collusion here?

Two or more AI agents coordinating to get a better outcome for themselves than competition would give, for example two pricing firms keeping prices high. The sprint's own survey of 139 definitions splits into an economics view (prices above the competitive level) and an AI-safety view (covert, unwanted coordination). See [Methods](Methods#what-we-mean-by-collusion).

## What is a "collusion detector"?

A program that reads logs of agent behaviour and reports a score or a p-value saying how likely it is that the agents colluded. The project we audited combines several signals: mutual information between agents, permutation tests, watermark variance, linguistic traces, acceptance bias and welfare shifts.

## Why does "99% of honest batches flagged" matter?

The detector claims a false-positive rate of 1 in 1,000. If it flags almost every honest batch at the 5% level, its p-values do not mean what they say. A verdict of "collusion" from it is then weak evidence, even if the underlying statistic is informative.

## Does this mean the original detectors are bad?

No. The underlying statistics are informative: after recalibrating on independent honest batches, cross-run MI detects all four scripted colluders every time. The problem is the calibration and what counts as an independent unit. This is a critique of reporting practice, not of the original authors, whose open release made the audit possible.

## What is pseudoreplication?

Treating copies or dependent samples as independent ones. A log that appends the same run many times looks like thousands of runs but holds only a few distinct ones. A statistic calibrated on those copies sounds more certain than it is.

## What is the swap control?

Each firm reads the messages of a different run instead of its real rival's. If the price rise came from the two firms talking to each other, it would disappear. It stays for all six models, so the firms are each following the same prompt rather than coordinating through messages.

## So did the agents collude?

Not in the sense of an agreement. The "collude" instruction raised prices, but the swap control, the silent control and the prompt-wording results all point to parallel obedience to a shared instruction. We do not claim a meeting of minds in any run.

## Why did the auditor mark the honest Claude runs as more suspicious?

Because in those runs the firms read each other's statements and often proposed holding prices, for example "I'll hold 1.75 as long as you do". Meanwhile Haiku's collusion-labelled runs mostly refused ("I won't coordinate"). The auditor reads the transcripts correctly. It is the labels that are unreliable.

## Why do results change so much with the prompt wording?

That is one of the findings. For Sonnet the collusion effect is +2.03, +0.19, +2.01 and -0.35 across four wordings. A single prompt cannot support a claim about what a model "does" under a collusion instruction.

## How big is the study?

Six LLM agents in a pricing game (40 to 50 runs per condition), two Claude models in a first-price auction (40 runs per cell), and 180 honest, 30 keyword and 20 stealth batches per scenario for the detector tests. It is a focused audit, not a large benchmark. See [Limitations and Roadmap](Limitations-and-Roadmap).

## Can I trust the numbers?

Every number in the report is built from saved outputs by scripts in `sprint_work/`, and `k_verify_report_numbers.py` checks the text against them. Better still, recompute five of them yourself with [VERIFY_YOURSELF.md](https://github.com/shoumyac/collusion-evidence-audit/blob/main/VERIFY_YOURSELF.md). The report's LLM Usage Statement discloses that Claude helped write the code and text.

## Can I reuse the code?

Yes, with care. The helper library is described in [Audit Kit](Audit-Kit). The starter repository that we audited has its own licence terms, so check them before reusing that part.

## How do I cite this?

See the BibTeX entry at the bottom of the [README](https://github.com/shoumyac/collusion-evidence-audit#citation).
