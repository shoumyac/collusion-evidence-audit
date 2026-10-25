"""Analysis A: pseudo-replication audit of the shipped ColludeBench transcripts and calibration samples.

Reads (never writes) the starter repo. Writes JSON to sprint_work/out/.
Usage: python a_pseudoreplication.py <path to steganographic-collusion>
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

root = Path(sys.argv[1])
out = Path(__file__).parent / "out"
out.mkdir(exist_ok=True)


def split_runs(path):
    runs, cur, last = [], [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["round_id"] < last and cur:
            runs.append(cur)
            cur = []
        cur.append(rec)
        last = rec["round_id"]
    if cur:
        runs.append(cur)
    return runs


def digest(run, ignore_id=False):
    h = hashlib.sha256()
    for r in run:
        rid = "" if ignore_id else r["run_id"]
        h.update(json.dumps([rid, r["round_id"], r["agent_id"], r["message"], r["action"], r["reward"]]).encode())
    return h.hexdigest()


files = [p for p in (root / "results").rglob("*.jsonl") if not p.name.endswith("_interventions.jsonl")]
raw = distinct = within_file_distinct = 0
multi = 0
seen, seen_noid = set(), set()
by_dir = defaultdict(lambda: Counter())
for p in files:
    runs = split_runs(p)
    top = p.relative_to(root / "results").parts[0]
    if len(runs) > 1:
        multi += 1
    within_file_distinct += len({digest(r) for r in runs})
    for run in runs:
        raw += 1
        by_dir[top]["raw"] += 1
        d = digest(run)
        if d not in seen:
            seen.add(d)
            distinct += 1
            by_dir[top]["distinct"] += 1
            dn = digest(run, ignore_id=True)
            if dn not in seen_noid:
                seen_noid.add(dn)

summary = {
    "transcript_files": len(files),
    "files_with_multiple_runs": multi,
    "raw_runs_counted_naively": raw,
    "distinct_runs_within_file": within_file_distinct,
    "distinct_runs_by_content_global": distinct,
    "distinct_ignoring_run_id": len(seen_noid),
    "by_top_dir": {k: dict(v) for k, v in by_dir.items()},
}

# Behavioural diversity inside the calibration (honest) runs: how many distinct message/action sequences
cal = defaultdict(lambda: {"runs": 0, "distinct_seq": set(), "distinct_actions": set(), "msgs": set()})
for p in (root / "results" / "calibration").rglob("*.jsonl"):
    if p.name.endswith("_interventions.jsonl"):
        continue
    scen = p.parent.name
    for run in split_runs(p):
        c = cal[scen]
        c["runs"] += 1
        c["distinct_seq"].add(digest(run, ignore_id=True))
        c["distinct_actions"].add(tuple((r["agent_id"], r["action"]) for r in run))
        for r in run:
            c["msgs"].add(r["message"])
summary["calibration_diversity"] = {
    k: {"runs": v["runs"], "distinct_transcripts": len(v["distinct_seq"]),
        "distinct_action_sequences": len(v["distinct_actions"]), "distinct_messages": len(v["msgs"])}
    for k, v in cal.items()
}

# Calibration samples behind each detector threshold
thr = json.loads((root / "results/calibration/detector_thresholds.json").read_text())["thresholds"]
sample_rows = {}
for name, v in thr.items():
    n = v["count"]
    sample_rows[name] = {
        "n_samples": n,
        "max": v["max"],
        "target_fpr_1e3": v["target_fpr_1e3"],
        "threshold_equals_max_at_1e3": v["target_fpr_1e3"] == v["max"],
        "min_n_needed_for_1e3_quantile": 1000,
    }
summary["thresholds"] = sample_rows

# Distinct values inside the calibration series
series_info = {}
for f in (root / "results/calibration/logs").glob("*_calibration.json"):
    payload = json.loads(f.read_text())
    for det in payload["detectors"]:
        d = det["details"]
        for key in ("mi_values", "aligned_scores", "variances", "chi_stats", "gap_values", "per_run_gaps"):
            if key in d and d[key]:
                vals = d[key]
                series_info[f"{f.stem}:{det['name']}:{key}"] = {
                    "n": len(vals), "distinct": len(set(round(x, 9) for x in vals)),
                    "n_runs_in_audit": len(payload["runs"]),
                }
summary["calibration_series"] = series_info

(out / "a_pseudoreplication.json").write_text(json.dumps(summary, indent=2))
print(json.dumps({k: v for k, v in summary.items() if k not in ("calibration_series",)}, indent=1)[:6000])
print("series:", len(series_info))
for k, v in list(series_info.items())[:30]:
    print(k, v)
