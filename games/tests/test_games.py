import json
import tempfile
from pathlib import Path

import pytest

from games.cost import BudgetExceeded, CostTracker, estimate_usd
from games.envs import Auction, Cournot, Pricing, make_game
from games.runner import main, parse_action
from games.summarize import summarize


def grid(f, lo, hi, n=2001):
    return max((lo + (hi - lo) * i / (n - 1) for i in range(n)), key=f)


def test_pricing_benchmarks():
    g = Pricing()
    nash = grid(lambda p: g.step({"firm_a": p, "firm_b": 4.6})[0]["firm_a"], 0, 10)
    assert abs(nash - 4.6) < 0.05
    joint = grid(lambda p: sum(Pricing().step({"firm_a": p, "firm_b": p})[0].values()), 0, 10)
    assert abs(joint - 5.5) < 0.05


def test_cournot_benchmarks():
    nash = grid(lambda q: Cournot().step({"firm_a": q, "firm_b": 6.0})[0]["firm_a"], 0, 20)
    assert abs(nash - 6.0) < 0.05
    joint = grid(lambda q: sum(Cournot().step({"firm_a": q, "firm_b": q})[0].values()), 0, 10)
    assert abs(2 * joint - 9.0) < 0.05


def test_auction_rules():
    g = Auction()
    g.reset(1)
    rew, info = g.step({"bidder_a": 2.0, "bidder_b": 2.5, "bidder_c": 1.0})  # all below reserve
    assert info["metric"] == 0.0 and all(v == 0 for v in rew.values())
    g.reset(1)
    v = dict(g.values)
    rew, info = g.step({"bidder_a": 8.0, "bidder_b": 5.0, "bidder_c": 4.0})
    assert info["winner"] == "bidder_a" and abs(rew["bidder_a"] - (v["bidder_a"] - 8.0)) < 1e-9 and info["metric"] == 8.0


def test_parse():
    g = make_game("pricing")
    assert parse_action("fine. Price:4.2", "Price", g)[0] == 4.2
    assert parse_action("no number", "Price", g)[0] == 5.0
    assert parse_action("Price:99", "Price", g)[0] == 10.0


def test_cost_cap_and_estimate():
    t = CostTracker("claude-sonnet-5-5", budget_usd=0.01)
    with pytest.raises(BudgetExceeded):
        t.add(10_000, 10_000)
    assert abs(estimate_usd("claude-sonnet-5-5", 1) - 0.101) < 0.001
    assert estimate_usd("stub", 100) == 0


@pytest.mark.parametrize("game", ["pricing", "auction", "cournot"])
def test_stub_end_to_end_with_swap_and_resume(game):
    with tempfile.TemporaryDirectory() as d:
        base = ["--game", game, "--backend", "stub", "--runs", "4", "--rounds", "4", "--out", d, "--workers", "2"]
        assert main(base + ["--conditions", "honest,collude"]) == 0
        assert main(base + ["--conditions", "honest_swap,collude_swap"]) == 0
        root = next(Path(d).iterdir())
        n_before = {f: f.stat().st_mtime_ns for f in root.rglob("*.jsonl")}
        assert len(n_before) == 16
        assert main(base + ["--conditions", "honest,collude"]) == 0  # resume: nothing rewritten
        assert {f: f.stat().st_mtime_ns for f in root.rglob("*.jsonl")} == n_before
        s = summarize(root)
        d_ = s["effect"]["d"]
        assert d_ < 0 if game in ("auction", "cournot") else d_ > 0  # the stub 'colludes' when told to
        assert "intact_minus_swapped" in s
        row = json.loads(next((root / "collude").glob("*.jsonl")).read_text().splitlines()[0])
        assert {"run_id", "round_id", "agent_id", "action", "said", "reward"} <= set(row)


def test_swap_requires_base(tmp_path):
    with pytest.raises(SystemExit):
        main(["--game", "pricing", "--backend", "stub", "--runs", "2", "--rounds", "2", "--out", str(tmp_path), "--conditions", "collude_swap"])


def test_budget_stops_run(tmp_path):
    rc = main(["--game", "pricing", "--backend", "stub", "--model", "claude-sonnet-5-5", "--runs", "3", "--rounds", "3", "--out", str(tmp_path),
               "--budget-usd", "0.0000001", "--workers", "1"])
    assert rc == 1
