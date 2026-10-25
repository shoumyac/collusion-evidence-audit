"""Test of one concrete explanation for the liberal cross-run MI p-values: in run_cross_run_mi the observed MI is estimated with
estimate_mi(..., steps=200) but each shuffled-null estimate uses steps=120, so the null is trained for less time and sits lower
than the observed statistic even when there is no dependence. We patch ONLY that number (null steps 120 -> 200) at runtime
(the starter source is not modified), re-run the same honest and keyword batches (same seeds as b_controls.py) and compare.

Run from steganographic-collusion/:
  uv run python ../../work/sprint_work/i_mi_null_test.py --scenario pricing --batches 10
"""
import argparse
import inspect
import json
import time
from pathlib import Path

import auditor.detectors.mi as mi_mod
from auditor.config import AuditPipelineConfig, SeedScheduleConfig
from auditor.detectors import registry
from auditor.pipeline import AuditPipeline

ap = argparse.ArgumentParser()
ap.add_argument("--scenario", required=True)
ap.add_argument("--batches", type=int, default=10)
ap.add_argument("--runs", type=int, default=10)
args = ap.parse_args()

src = inspect.getsource(mi_mod.run_cross_run_mi)
assert "steps=120" in src and "steps=200" in src
patched_src = src.replace("steps=120", "steps=200")
ns = dict(mi_mod.__dict__)
exec(patched_src, ns)
patched = ns["run_cross_run_mi"]

CFG = {("pricing", "honest"): "configs/audits/pricing_honest_calibration.yaml",
       ("pricing", "keyword"): "configs/audits/pricing_keyword_audit.yaml",
       ("auction", "honest"): "configs/audits/auction_honest_calibration.yaml",
       ("auction", "keyword"): "configs/audits/auction_keyword_audit.yaml",
       ("review", "honest"): "configs/audits/review_honest_calibration.yaml",
       ("review", "keyword"): "configs/audits/review_keyword_audit.yaml"}
out = Path(__file__).parent / "out"
res_path = out / f"i_mi_null_{args.scenario}.jsonl"
done = {(json.loads(l)["label"], json.loads(l)["batch"]) for l in res_path.read_text().splitlines()} if res_path.exists() else set()
for label in ("honest", "keyword"):
    for b in range(args.batches):
        if (label, b) in done:
            continue
        cfg = AuditPipelineConfig.from_yaml(CFG[(args.scenario, label)])
        start = 100000 + b * args.runs  # same seeds as b_controls.py batches 0..
        cfg.seed_schedule = SeedScheduleConfig(mode="list", values=tuple(range(start, start + args.runs)), count=args.runs)
        cfg.output_dir = out / "runs_i" / f"{args.scenario}_{label}" / f"batch{b}"
        cfg.log_dir = cfg.output_dir / "logs"
        cfg.detectors = [d for d in cfg.detectors if d.kind == "cross_run_mi"]
        t0 = time.time()
        registry._REGISTRY["cross_run_mi"] = patched
        s_patched = AuditPipeline(cfg).run().detectors[0]
        rec = {"scenario": args.scenario, "label": label, "batch": b, "p_patched": s_patched.p_value,
               "stat_patched": s_patched.statistic, "null_mean_patched": s_patched.details["null_mean"],
               "null_std_patched": s_patched.details["null_std"], "sec": round(time.time() - t0, 1)}
        with res_path.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(rec, flush=True)
