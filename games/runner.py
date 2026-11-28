"""Run repeated-game experiments against any backend.

Example (free, no API):  python -m games.runner --game pricing --backend stub --runs 6 --out /tmp/stubrun
Conditions: honest, collude, honest_swap, collude_swap. A swap run replays the rival's messages from a different run of the
base condition, so the agent cannot be reacting to its actual rival's words. Swap needs the base runs on disk first.
Output per run: <out>/<tag>/<cond>/run_<seed>.jsonl (one row per agent per round) plus cost.json. Existing run files are skipped (resume).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .backends import make_backend
from .cost import BudgetExceeded, CostTracker, estimate_usd
from .envs import make_game
from .prompts import system_prompt, user_prompt

ROOT = Path(__file__).resolve().parent.parent
NUM = r"(-?\d+(?:\.\d+)?)"


def parse_action(text: str, label: str, game) -> tuple[float, str]:
    """Return (action, message). Takes the last 'Label:<number>' and falls back to the midpoint of the range if missing."""
    ms = re.findall(rf"{label}\s*[:=]\s*\$?{NUM}", text, flags=re.I)
    act = game.clip(float(ms[-1])) if ms else (game.lo + game.hi) / 2
    said = re.sub(rf"{label}\s*[:=]\s*\$?{NUM}", "", text, flags=re.I).strip()
    return act, said[:400]


def load_msgs(path: Path) -> dict:
    out: dict = {}
    for l in path.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            out[(r["round_id"], r["agent_id"])] = r["said"]
    return out


def run_one(game_name, backend, cost, cond, wording, rounds, seed, partner_msgs=None, max_tokens=250):
    g = make_game(game_name, rounds)
    g.reset(seed)
    base = cond.replace("_xswap", "").replace("_swap", "")
    hist, rows = [], []
    for rd in range(rounds):
        said, acts, tin_out = {}, {}, {}
        for role in g.roles:
            sys_p = system_prompt(g, role, base, wording, rounds)
            usr = user_prompt(g, role, hist, rd + 1, rounds)
            text, ti, to = backend.ask(sys_p, usr, max_tokens)
            cost.add(ti, to)
            acts[role], said[role] = parse_action(text, g.action, g)
        obs = {r: dict(g.observe(r)) for r in g.roles}
        rew, info = g.step(acts)
        seen = {}
        for role in g.roles:
            seen[role] = {o: (partner_msgs.get((rd, o), said[o]) if partner_msgs else said[o]) for o in g.roles if o != role}
        hist.append({"r": rd + 1, "said": said, "act": acts, "rew": rew, "seen": seen})
        for role in g.roles:
            rows.append({"run_id": f"{cond}_{seed}", "round_id": rd, "agent_id": role, "action": acts[role], "said": said[role], "reward": rew[role],
                         "info": {k: v for k, v in info.items() if k != "values"}, "obs": obs[role]})
    return rows


def load_rows(path: Path) -> dict:
    out: dict = {}
    for l in path.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            out[(r["round_id"], r["agent_id"])] = (r["action"], r["said"])
    return out


DEV_ROUND, DEV_PRICE = 4, 3.0   # forced one-round undercut by the puppet (pricing only), below the Nash price 4.6


def run_puppet(game_name, backend, cost, cond, wording, rounds, seed, live_role, text_src, act_src, max_tokens=250, dev=False):
    """One live agent against open-loop puppet rivals. cond = 'pup-<collude|honest>-<T><A>[-coh]'.
    The puppets' texts come from text_src and their actions from act_src (dicts (round, role) -> (action, said)); the live
    agent's profit is computed by the game against the puppets' actions, so the history it sees is consistent."""
    g = make_game(game_name, rounds)
    g.reset(seed)
    base = cond.split("-")[1]
    puppets = [r for r in g.roles if r != live_role]
    hist, rows = [], []
    for rd in range(rounds):
        sys_p = system_prompt(g, live_role, base, wording, rounds)
        usr = user_prompt(g, live_role, hist, rd + 1, rounds)
        text, ti, to = backend.ask(sys_p, usr, max_tokens)
        cost.add(ti, to)
        act, said_live = parse_action(text, g.action, g)
        acts = {live_role: act}
        said = {live_role: said_live}
        for o in puppets:
            acts[o] = DEV_PRICE if (dev and rd == DEV_ROUND) else act_src[(rd, o)][0]
            said[o] = text_src[(rd, o)][1]
        obs = {r: dict(g.observe(r)) for r in g.roles}
        rew, info = g.step(acts)
        hist.append({"r": rd + 1, "said": said, "act": acts, "rew": rew, "seen": {live_role: {o: said[o] for o in puppets}}})
        rows.append({"run_id": f"{cond}_{seed}", "round_id": rd, "agent_id": live_role, "action": act, "said": said_live, "reward": rew[live_role],
                     "info": {k: v for k, v in info.items() if k != "values"}, "obs": obs[live_role], "live_role": live_role})
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--game", default="pricing", choices=["pricing", "auction", "cournot"])
    p.add_argument("--backend", default="stub", choices=["stub", "anthropic", "openai"])
    p.add_argument("--model", default="stub")
    p.add_argument("--runs", type=int, default=6)
    p.add_argument("--conditions", default="honest,collude")
    p.add_argument("--wording", type=int, default=1, choices=[1, 2, 3, 4, 5])
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--seed0", type=int, default=0)
    p.add_argument("--out", default=str(ROOT / "games_out"))
    p.add_argument("--budget-usd", type=float, default=None, help="hard cap; the run stops when exceeded")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=250)
    p.add_argument("--dry-run", action="store_true", help="print the cost estimate and exit")
    a = p.parse_args(argv)

    conds = a.conditions.split(",")
    tag = f"{a.game}-{a.model.replace('/', '_')}-w{a.wording}"
    root = Path(a.out) / tag
    est = estimate_usd(a.model, a.runs * len(conds))
    print(f"{len(conds) * a.runs} runs, estimated ${est:.2f} for {a.model}")
    if a.dry_run:
        return 0
    cost = CostTracker(a.model, a.budget_usd, root / "cost.json")
    be = make_backend(a.backend, a.model, a.game, ROOT)
    jobs = []
    for c in conds:
        for i in range(a.runs):
            f = root / c / f"run_{a.seed0 + i}.jsonl"
            if f.exists():
                continue
            pm = None
            if c.startswith("pup-"):
                parts = c.split("-"); T, A = parts[2][0], parts[2][1]; dev = len(parts) > 3 and parts[3] == "dev"; coh = len(parts) > 3
                nm = {"c": "collude", "h": "honest"}
                ts = root / nm[T] / f"run_{a.seed0 + (i + 1) % a.runs}.jsonl"
                as_ = root / nm[A] / f"run_{a.seed0 + ((i + 1) if coh else (i + 2)) % a.runs}.jsonl"
                if not (ts.exists() and as_.exists()):
                    sys.exit(f"{c} needs source runs {ts} and {as_}")
                roles = make_game(a.game, a.rounds).roles
                jobs.append((c, a.seed0 + i, f, ("pup", roles[i % len(roles)], load_rows(ts), load_rows(as_), dev)))
                continue
            if c.endswith("_swap") or c.endswith("_xswap"):
                # _swap: text from another run of the same condition; _xswap: text from the opposite
                # condition (collude reads honest-run text, honest reads collude-run text), cross-condition replay
                if c.endswith("_xswap"):
                    src = {"collude": "honest", "honest": "collude"}[c[: -len("_xswap")]]
                else:
                    src = c[: -len("_swap")]
                pf = root / src / f"run_{a.seed0 + (i + 1) % a.runs}.jsonl"
                if not pf.exists():
                    sys.exit(f"{c} needs {pf} first: run the base condition before the swap condition")
                pm = load_msgs(pf)
            jobs.append((c, a.seed0 + i, f, pm))

    def work(j):
        c, seed, f, pm = j
        cost.check_headroom(estimate_usd(a.model, 1))
        if isinstance(pm, tuple):
            rows = run_puppet(a.game, be, cost, c, a.wording, a.rounds, seed, pm[1], pm[2], pm[3], a.max_tokens, pm[4])
        else:
            rows = run_one(a.game, be, cost, c, a.wording, a.rounds, seed, pm, a.max_tokens)
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        tmp.replace(f)  # a run file exists only if the run finished
        return f

    stopped = None
    try:
        with ThreadPoolExecutor(a.workers) as ex:
            for _ in ex.map(work, jobs):
                pass
    except BudgetExceeded as e:
        stopped = str(e)
    cost.save()
    (root / "meta.json").write_text(json.dumps({"game": a.game, "model": a.model, "wording": a.wording, "rounds": a.rounds, "conditions": conds}, indent=1))
    print(f"spent ${cost.usd:.4f} over {cost.calls} calls" + (f"; STOPPED: {stopped}" if stopped else ""))
    return 1 if stopped else 0


if __name__ == "__main__":
    raise SystemExit(main())
