"""Summarise the MI null-steps test: shipped p-values vs p-values with the null trained for the same number of steps,
on the SAME batches (b_controls batches 0..9, same seeds)."""
import json
from pathlib import Path

out = Path(__file__).parent / "out"
res = {}
for scen in ("pricing", "auction"):
    rows = [json.loads(l) for l in (out / f"i_mi_null_{scen}.jsonl").read_text().splitlines() if l.strip()]
    for label in ("honest", "keyword"):
        shipped = {json.loads(l)["batch"]: json.loads(l)["detectors"]["cross_run_mi"]["p_value"]
                   for l in (out / f"b_{scen}_{label}.jsonl").read_text().splitlines() if l.strip()}
        pr = [r for r in rows if r["label"] == label]
        pairs = [(shipped[r["batch"]], r["p_patched"]) for r in pr if r["batch"] in shipped]
        n = len(pairs)
        res[f"{scen}|{label}"] = {
            "n": n,
            "shipped_frac_le_0.05": sum(a <= 0.05 for a, _ in pairs) / n,
            "matched_null_frac_le_0.05": sum(b <= 0.05 for _, b in pairs) / n,
            "shipped_median_p": sorted(a for a, _ in pairs)[n // 2],
            "matched_null_median_p": sorted(b for _, b in pairs)[n // 2],
        }
(out / "i_mi_summary.json").write_text(json.dumps(res, indent=1))
for k, v in res.items():
    print(k, v)
