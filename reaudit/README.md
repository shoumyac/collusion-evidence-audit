# Re-audit scripts for published collusion evaluations

Both scripts have hard coded paths (`/home/claude/reaudit/...`). Edit the `BASE` and glob paths at the top before running elsewhere.

Data used (not copied here):
- Sticky Collusion (Cahyono 2026): `git clone https://github.com/JvThunder/sticky-collusion` (the slim run records are in `data/sticky-collusion/runs`).
- Shi et al. 2026: `data/episodes/main/*.parquet` from the Hugging Face dataset `SALT-NLP/agent-collusion` (needs `pip install pyarrow pandas scipy`).

`audit_sticky.py` reproduces the paper's `numbers.json` first (run the authors' `make_figures.py` with `STICKY_RESULTS` pointing at the slim runs), then adds the checks in `docs/REAUDIT_PUBLISHED.md`.
