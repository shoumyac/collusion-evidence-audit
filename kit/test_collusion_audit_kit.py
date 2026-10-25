import json
import random

import pytest

import collusion_audit_kit as k


def _run(run_id, price=1.0, rounds=3):
    return [{"run_id": run_id, "round_id": r + 1, "agent_id": a, "message": f"Price:{price}", "action": str(price), "reward": 1.0}
            for r in range(rounds) for a in ("a", "b")]


def test_split_and_distinct(tmp_path):
    f = tmp_path / "t.jsonl"
    recs = _run("x") + _run("x") + _run("x", price=2.0)  # same run appended twice, plus a different run
    f.write_text("\n".join(json.dumps(r) for r in recs))
    c = k.count_distinct_runs([f])
    assert c == {"raw": 3, "distinct_within_file": 2, "distinct_global": 2}


def test_wilson_bounds():
    lo, hi = k.wilson_interval(0, 30)
    assert lo == 0.0 and 0.05 < hi < 0.15
    assert k.wilson_interval(15, 30)[0] < 0.5 < k.wilson_interval(15, 30)[1]


def test_threshold_requires_enough_batches():
    with pytest.raises(ValueError):
        k.batch_threshold([1.0] * 5, alpha=0.01)
    assert k.batch_threshold(list(range(100)), alpha=0.05) == 95


def test_heldout_fpr_near_alpha_and_tpr_high():
    rng = random.Random(1)
    honest = [rng.gauss(0, 1) for _ in range(200)]
    colluding = [rng.gauss(4, 1) for _ in range(50)]
    r = k.heldout_rates(honest, colluding, alpha=0.05)
    assert 0.02 < r["heldout_fpr"] < 0.09 and r["tpr"] > 0.9


def test_manipulation_check_flags_null_effect():
    rng = random.Random(2)
    same_h = [rng.gauss(2, 0.1) for _ in range(40)]
    same_c = [rng.gauss(2, 0.1) for _ in range(40)]
    assert not k.manipulation_check(same_h, same_c, nash=4.6, joint_max=5.5)["label_supported"]
    up = [rng.gauss(3, 0.1) for _ in range(40)]
    assert k.manipulation_check(same_h, up, nash=4.6, joint_max=5.5)["label_supported"]


def test_auroc_inverted_is_below_half():
    scores = [0.9, 0.8, 0.1, 0.2]
    labels = [0, 0, 1, 1]
    a, (lo, hi) = k.auroc_with_ci(scores, labels)
    assert a == 0.0 and hi < 0.5
