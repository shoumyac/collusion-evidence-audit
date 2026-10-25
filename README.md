# collusion-evidence-audit

Apart Research AI Collusion Research Sprint (Oct 2026), Track 2 (Detection and Audit).
Authors: Shoumya Chowdhury, Anmita Das (University of Melbourne).

## What is pre-existing vs new

PRE-EXISTING (not ours): everything in the starter repo https://github.com/poseidon-research/collusion_hackathon
(pinned commit e6fb1308dae9cf97ae42aec1c5f7889d9e2291e8), in particular `steganographic-collusion/`
(ColludeBench-v0, the detector stack, calibration thresholds, shipped transcripts) and `util/` (poseidon_compute).
We do not copy or modify it; our scripts import it from a sibling clone.

NEW this sprint: everything in `sprint_work/` (analysis scripts, outputs, report sources).

## Reproduce

```
git clone https://github.com/poseidon-research/collusion_hackathon starter
git -C starter checkout e6fb1308dae9cf97ae42aec1c5f7889d9e2291e8
cd starter/steganographic-collusion && uv sync --python 3.11
uv run python ../../work/sprint_work/a_pseudoreplication.py .
```
(Status: work in progress.)
