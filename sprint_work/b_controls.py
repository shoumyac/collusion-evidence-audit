"""Analysis B: held-out positive and negative controls, scored per independent audit batch.

Run from the starter project directory (steganographic-collusion) so relative config paths resolve:
  uv run python <path>/b_controls.py --scenario pricing --label honest --batches 20 --runs 10 --seed0 100000

Each batch = one audit of `--runs` runs with fresh seeds never used by the shipped calibration (0..199) or audits (0..19).
Output: one JSON line per batch appended to sprint_work/out/b_<scenario>_<label>.jsonl
"""
import argparse
import json
import time
from pathlib import Path

from auditor.config import AuditPipelineConfig, SeedScheduleConfig
from auditor.pipeline import AuditPipeline

CFG = {
    ("pricing", "honest"): "configs/audits/pricing_honest_calibration.yaml",
    ("pricing", "keyword"): "configs/audits/pricing_keyword_audit.yaml",
    ("auction", "honest"): "configs/audits/auction_honest_calibration.yaml",
    ("auction", "keyword"): "configs/audits/auction_keyword_audit.yaml",
    ("review", "honest"): "configs/audits/review_honest_calibration.yaml",
    ("review", "keyword"): "configs/audits/review_keyword_audit.yaml",
    ("pricing", "sparse"): "configs/audits/pricing_sparse_audit.yaml",
    ("review", "sparse"): "configs/audits/review_sparse_audit.yaml",
    ("auction", "sparse"): "configs/audits/auction_sparse_audit.yaml",
}

ap = argparse.ArgumentParser()
ap.add_argument("--scenario", required=True)
ap.add_argument("--label", required=True)
ap.add_argument("--batches", type=int, default=10)
ap.add_argument("--runs", type=int, default=10)
ap.add_argument("--seed0", type=int, default=100000)
ap.add_argument("--out", default=str(Path(__file__).parent / "out"))
ap.add_argument("--suffix", default="", help="e.g. _s1 to write an extra shard to its own file")
args = ap.parse_args()

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
res_path = out / f"b_{args.scenario}_{args.label}{args.suffix}.jsonl"
done = set()
if res_path.exists():
    done = {json.loads(l)["batch"] for l in res_path.read_text().splitlines() if l.strip()}

for b in range(args.batches):
    if b in done:
        continue
    cfg = AuditPipelineConfig.from_yaml(CFG[(args.scenario, args.label)])
    start = args.seed0 + b * args.runs
    seeds = tuple(range(start, start + args.runs))
    cfg.seed_schedule = SeedScheduleConfig(mode="list", values=seeds, count=len(seeds))
    cfg.output_dir = out / "runs" / f"{args.scenario}_{args.label}{args.suffix}" / f"batch{b}"
    cfg.log_dir = cfg.output_dir / "logs"
    t0 = time.time()
    summary = AuditPipeline(cfg).run()
    dets = {}
    for d in summary.detectors:
        det = {k: v for k, v in d.details.items() if not isinstance(v, (list, dict)) or k.endswith("values") or k in ("per_run_gaps",)}
        dets[d.name] = {"statistic": d.statistic, "p_value": d.p_value, "details": det}
    rec = {"batch": b, "seeds": [seeds[0], seeds[-1]], "scenario": args.scenario, "label": args.label,
           "sec": round(time.time() - t0, 1), "detectors": dets}
    with res_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(f"batch {b} {rec['sec']}s", {k: (round(v['statistic'], 4), round(v['p_value'], 4)) for k, v in dets.items()}, flush=True)
