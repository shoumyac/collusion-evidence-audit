"""Summarise a games run directory: per-condition mean of the headline metric (run means), effect with bootstrap 95% CI, swap difference."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from .envs import make_game


def run_means(d: Path, game: str):
    out = []
    for f in sorted(d.glob("*.jsonl")):
        rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        if game == "cournot":  # metric is total quantity: sum agents per round, then mean over rounds
            by: dict = {}
            for r in rows:
                by.setdefault(r["round_id"], 0.0)
                by[r["round_id"]] += r["action"]
            out.append(float(np.mean(list(by.values()))))
        elif game == "auction":
            out.append(float(np.mean([r["info"]["metric"] for r in rows if r["agent_id"] == "bidder_a"])))
        else:
            out.append(float(np.mean([r["action"] for r in rows])))
    return np.array(out)


def boot(x, y, B=4000, seed=0):
    g = np.random.default_rng(seed)
    d = g.choice(x, (B, len(x))).mean(1) - g.choice(y, (B, len(y))).mean(1)
    return float(x.mean() - y.mean()), [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def summarize(root: Path) -> dict:
    meta = json.loads((root / "meta.json").read_text())
    game = meta["game"]
    cells = {c.name: run_means(c, game) for c in sorted(root.iterdir()) if c.is_dir()}
    res = {"game": game, "benchmarks": make_game(game).benchmarks(), "cells": {k: {"n": len(v), "mean": float(v.mean())} for k, v in cells.items() if len(v)}}
    if "honest" in cells and "collude" in cells:
        e, ci = boot(cells["collude"], cells["honest"])
        res["effect"] = {"d": e, "ci95": ci}
    if all(k in cells for k in ("honest", "collude", "honest_swap", "collude_swap")):
        e1, _ = boot(cells["collude"], cells["honest"])
        e2, _ = boot(cells["collude_swap"], cells["honest_swap"])
        res["swap_effect"] = e2
        res["intact_minus_swapped"] = e1 - e2
    return res


if __name__ == "__main__":
    print(json.dumps(summarize(Path(sys.argv[1])), indent=1))
