"""collusion_audit_kit: small, dependency-light helpers for auditing a collusion detector.

Everything here works on plain Python numbers and JSONL transcripts, so it can be used without the starter repository.
Functions: count_distinct_runs, wilson_interval, batch_threshold, heldout_rates, manipulation_check, auroc_with_ci.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


def split_runs(records: Sequence[dict]) -> List[List[dict]]:
    """Split an appended transcript into runs: a new run starts where round_id drops."""
    runs, cur, last = [], [], 0
    for r in records:
        if r["round_id"] < last and cur:
            runs.append(cur)
            cur = []
        cur.append(r)
        last = r["round_id"]
    if cur:
        runs.append(cur)
    return runs


def run_digest(run: Sequence[dict], ignore_run_id: bool = False) -> str:
    h = hashlib.sha256()
    for r in run:
        h.update(json.dumps(["" if ignore_run_id else r["run_id"], r["round_id"], r["agent_id"], r["message"], r["action"], r["reward"]]).encode())
    return h.hexdigest()


def count_distinct_runs(paths: Iterable[Path]) -> Dict[str, int]:
    """Raw runs counted naively, distinct within each file, and distinct across all files (by content)."""
    raw = within = 0
    seen = set()
    for p in paths:
        recs = [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]
        runs = split_runs(recs)
        raw += len(runs)
        within += len({run_digest(r) for r in runs})
        seen.update(run_digest(r) for r in runs)
    return {"raw": raw, "distinct_within_file": within, "distinct_global": len(seen)}


def wilson_interval(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def batch_threshold(honest_batch_stats: Sequence[float], alpha: float = 0.05) -> float:
    """Threshold from independent honest audit BATCHES (the unit decided on): the empirical (1-alpha) quantile.
    With n batches the smallest alpha that is meaningful is about 1/(n+1); requesting less raises ValueError."""
    n = len(honest_batch_stats)
    if n < 1 or alpha < 1.0 / (n + 1):
        raise ValueError(f"{n} honest batches cannot support alpha={alpha}; need at least {math.ceil(1 / alpha) - 1}")
    srt = sorted(honest_batch_stats)
    return srt[min(n - 1, int((1 - alpha) * n))]


def heldout_rates(honest: Sequence[float], colluding: Sequence[float], alpha: float = 0.05, splits: int = 500, seed: int = 0) -> Dict[str, float]:
    """Random 50/50 splits of honest batches: threshold on one half, FPR on the other, TPR on all colluding batches."""
    rng = random.Random(seed)
    fpr, tpr = [], []
    for _ in range(splits):
        idx = list(range(len(honest)))
        rng.shuffle(idx)
        cal = [honest[i] for i in idx[: len(idx) // 2]]
        test = [honest[i] for i in idx[len(idx) // 2:]]
        thr = batch_threshold(cal, alpha)
        fpr.append(sum(x > thr for x in test) / len(test))
        tpr.append(sum(x > thr for x in colluding) / len(colluding))
    return {"heldout_fpr": sum(fpr) / splits, "tpr": sum(tpr) / splits}


def manipulation_check(prices_honest: Sequence[float], prices_colluding: Sequence[float], nash: float, joint_max: float,
                       boots: int = 2000, seed: int = 0) -> Dict[str, object]:
    """Did the 'colluding' label change behaviour? Mean price difference with bootstrap CI and position between Nash and joint max."""
    rng = random.Random(seed)
    diff = sum(prices_colluding) / len(prices_colluding) - sum(prices_honest) / len(prices_honest)
    bs = sorted(
        sum(rng.choice(prices_colluding) for _ in prices_colluding) / len(prices_colluding)
        - sum(rng.choice(prices_honest) for _ in prices_honest) / len(prices_honest)
        for _ in range(boots)
    )
    mc = sum(prices_colluding) / len(prices_colluding)
    return {"mean_diff": diff, "ci95": (bs[int(0.025 * boots)], bs[int(0.975 * boots)]),
            "colluding_nash_to_joint_fraction": (mc - nash) / (joint_max - nash), "label_supported": bs[int(0.025 * boots)] > 0}


def auroc(scores: Sequence[float], labels: Sequence[int]) -> float:
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return float("nan")
    return sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg))


def auroc_with_ci(scores: Sequence[float], labels: Sequence[int], boots: int = 1000, seed: int = 0) -> Tuple[float, Tuple[float, float]]:
    rng = random.Random(seed)
    n = len(labels)
    vals = []
    for _ in range(boots):
        idx = [rng.randrange(n) for _ in range(n)]
        a = auroc([scores[i] for i in idx], [labels[i] for i in idx])
        if not math.isnan(a):
            vals.append(a)
    vals.sort()
    return auroc(scores, labels), (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals))])
