# collusion-evidence-audit

Apart Research AI Collusion Research Sprint (October 2026), Track 2 (Detection and Audit).
Authors: Shoumya Chowdhury, Anmita Das (University of Melbourne).

**Report:** `report/report.pdf` (source `report/report.tex`). Title: *Auditing a Collusion Detector: Unit of Replication, Calibration and Say-versus-Do Gaps in LLM Pricing Agents*.

## What is pre-existing and what is new

**Pre-existing (not ours, not modified):** the starter repository
https://github.com/poseidon-research/collusion_hackathon at commit `e6fb1308dae9cf97ae42aec1c5f7889d9e2291e8`,
in particular `steganographic-collusion/` (ColludeBench-v0, the detector stack, calibration thresholds and the shipped
transcripts in `results/`) and `util/` (poseidon_compute). We import it from a sibling clone and write nothing into it.
(One runtime patch, never written to disk: `i_mi_null_test.py` re-compiles one function with a single constant changed.)

**New this sprint:** everything in `sprint_work/`, `kit/` and `report/`.

| File | What it does |
| --- | --- |
| `sprint_work/a_pseudoreplication.py` | Raw vs distinct runs in the shipped transcripts; calibration sample size behind each threshold |
| `sprint_work/b_controls.py`, `b_analyze.py`, `b2_recalibrate.py`, `j_evidence_curve.py` | Held-out honest / keyword / sparse audit batches scored by the repo detectors; batch-level recalibration; calibration-size curve |
| `sprint_work/i_mi_null_test.py`, `i_summarize.py` | Test of one cause of the cross-run MI p-value result (null estimated with fewer steps) |
| `sprint_work/modal_host.py`, `c_llm_agents.py` | LLM firms in the repo's pricing game: open-weight models via vLLM on Modal, Claude via the Anthropic API; silent, paraphrase and reworded-prompt controls |
| `sprint_work/d_score_llm.py`, `e_llm_auditor.py`, `h_auditor_examples.py` | Repo detectors on LLM transcripts; cross-validated say-vs-do classifiers; blind LLM auditors (Claude Sonnet 5.5 and Qwen2.5-7B) |
| `sprint_work/f_report_assets.py`, `g_make_tables.py`, `k_verify_report_numbers.py` | Build every figure, table and number in the report from saved outputs; check the numbers quoted in the text |
| `sprint_work/m_permutation_and_interaction.py`, `n_independent_checks.py` | Label-permutation test of the say/do classifiers (200 shuffles); difference-of-differences interaction estimates with bootstrap CIs (no LLM calls); recomputation of five headline numbers from the raw files |
| `sprint_work/o_variants.py` | Claude agents under four prompt wordings (v1 to v4) plus the swap control under prompt 3: prices with bootstrap CIs, collude effect, blind-auditor AUROC, message rates, distinct paths |
| `colab/swap_controls_open_weights.ipynb`, `colab/colab_bundle.zip`, `colab/swap_results.zip` | Colab notebook that ran the swap control for the four open-weight models on Modal GPUs, its input bundle and the returned runs (now in `sprint_work/out/llm/<model>/{honest,collude}_swap`) |
| `sprint_work/q_auction_agents.py`, `sprint_work/r_auction_analysis.py` | Second game: first-price auction with Claude firms (honest, collude, swap), and its bootstrap analysis |
| `sprint_work/p_path_cluster_ci.py` | Confidence intervals that resample clusters of identical-path runs, compared with the ordinary run-level bootstrap |
| `kit/collusion_audit_kit.py` (+ tests) | Small dependency-light helpers: distinct-run counting, batch calibration, held-out rates, manipulation check, AUROC with CI |
| `sprint_work/out/` | Raw per-batch results (JSONL), summaries (JSON/CSV), LLM transcripts, figures |

Also: `VERIFY_YOURSELF.md` lists five headline numbers each author should recompute from the saved files, and
`sprint_work/l_distinct_and_words.py` counts distinct price paths per condition and lists the top words per model.
Controls in the LLM game: `silent` (no message channel), `para` (rival's messages paraphrased), `swap` (rival's messages
taken from a different run) and `--variant v2|v3|v4` (v2 and v4 reworded prompts, v3 a strict independent-play honest baseline with the v1 collusion prompt; v3 and v4 for the Claude models only).

Runs that were discarded: Claude runs with a 120-token reply cap (truncation inflated prices) were archived locally
under `sprint_work/out/llm/_superseded_maxtok120/` (not committed) and are not used anywhere in the report.

## Reproduce

```
git clone https://github.com/poseidon-research/collusion_hackathon starter
git -C starter checkout e6fb1308dae9cf97ae42aec1c5f7889d9e2291e8
git clone https://github.com/shoumyac/collusion-evidence-audit work
cd starter/steganographic-collusion && uv sync --python 3.11     # Python 3.13 cannot build numpy 1.26 on Windows
export PYTHONPATH=$(pwd)                                          # PowerShell: $env:PYTHONPATH=(Get-Location).Path
uv run python ../../work/sprint_work/a_pseudoreplication.py .
uv run python ../../work/sprint_work/b_controls.py --scenario pricing --label honest --batches 30 --runs 10   # also keyword, sparse; auction, review; --suffix _s1 --seed0 400000 for extra honest shards
uv run python ../../work/sprint_work/b_analyze.py . ; uv run python ../../work/sprint_work/b2_recalibrate.py ; uv run python ../../work/sprint_work/j_evidence_curve.py
# LLM agents: put your own key in work/.anthropic_key (gitignored); Modal needs `modal token new` and secrets named huggingface and modal-serve
uv run python ../../work/sprint_work/c_llm_agents.py --backend anthropic --model claude-haiku-5-5 --tag claude-haiku-5-5 --runs 40 --max-tokens 400 --conditions honest,collude,honest_silent,collude_silent
uv run python ../../work/sprint_work/d_score_llm.py claude-haiku-5-5 10
uv run python ../../work/sprint_work/e_llm_auditor.py claude-haiku-5-5 claude-sonnet-5-5
uv run python ../../work/sprint_work/f_report_assets.py && python ../../work/sprint_work/g_make_tables.py && python ../../work/sprint_work/k_verify_report_numbers.py
cd ../../work/report && pdflatex report.tex && pdflatex report.tex
```

No credentials are stored in this repository. LLM outputs are not deterministic, so a re-run will differ in detail.
The audit kit tests: `cd kit && python -m pytest -q`.
