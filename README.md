# collusion-evidence-audit

Apart Research AI Collusion Research Sprint (October 2026), Track 2 (Detection and Audit).
Authors: Shoumya Chowdhury, Anmita Das (University of Melbourne).

Report: `report/report.pdf` (source `report/report.tex`).

## What is pre-existing and what is new

**Pre-existing (not ours, not modified):** the starter repository
https://github.com/poseidon-research/collusion_hackathon at commit `e6fb1308dae9cf97ae42aec1c5f7889d9e2291e8`,
in particular `steganographic-collusion/` (ColludeBench-v0, the detector stack, calibration thresholds and the shipped
transcripts in `results/`) and `util/` (poseidon_compute). We import it from a sibling clone and write nothing into it.

**New this sprint:** everything in `sprint_work/` and `report/`.

| File | What it does |
| --- | --- |
| `a_pseudoreplication.py` | Counts raw vs distinct runs in the shipped transcripts and the calibration sample size behind each threshold |
| `b_controls.py`, `b_analyze.py`, `b2_recalibrate.py` | Held-out honest / keyword / sparse audit batches scored by the repo detectors, per-batch FPR/TPR, batch-level recalibration |
| `modal_host.py`, `c_llm_agents.py` | LLM firms (Qwen2.5-7B on Modal via vLLM; Claude Haiku/Sonnet 5.5 via the Anthropic API) in the repo's pricing game |
| `d_score_llm.py`, `e_llm_auditor.py` | Repo detectors on LLM transcripts, say-vs-do baselines, blind Claude auditor in three views |
| `f_report_assets.py`, `g_make_tables.py` | Build every number, figure and table in the report from saved outputs |
| `out/` | Raw per-batch results (JSONL), summaries (JSON/CSV), figures. Raw transcripts of the control runs are not committed |

## Reproduce

```
git clone https://github.com/poseidon-research/collusion_hackathon starter
git -C starter checkout e6fb1308dae9cf97ae42aec1c5f7889d9e2291e8
git clone https://github.com/shoumyac/collusion-evidence-audit work
cd starter/steganographic-collusion && uv sync --python 3.11     # Python 3.13 cannot build numpy 1.26 on Windows
export PYTHONPATH=$(pwd)                                          # PowerShell: $env:PYTHONPATH=(Get-Location).Path
uv run python ../../work/sprint_work/a_pseudoreplication.py .
uv run python ../../work/sprint_work/b_controls.py --scenario pricing --label honest --batches 30 --runs 10   # also keyword, sparse; auction, review
uv run python ../../work/sprint_work/b_analyze.py .
uv run python ../../work/sprint_work/b2_recalibrate.py
# LLM agents: put your own key in work/.anthropic_key (gitignored); Modal needs `modal token new`
uv run python ../../work/sprint_work/c_llm_agents.py --backend anthropic --model claude-haiku-5-5 --tag claude-haiku-5-5 --runs 40
uv run python ../../work/sprint_work/d_score_llm.py claude-haiku-5-5 10
uv run python ../../work/sprint_work/e_llm_auditor.py claude-haiku-5-5 claude-sonnet-5-5
uv run python ../../work/sprint_work/f_report_assets.py && python ../../work/sprint_work/g_make_tables.py
```

No credentials are stored in this repository. LLM outputs are not deterministic, so a re-run will differ in detail.
