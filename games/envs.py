"""Pure-python environments with closed-form benchmarks. No third-party imports.

Each game has: roles, action name, reset(seed), observe(role), step(actions) -> (rewards, info), benchmarks and a headline
`metric` (the number we compare across conditions: mean price, clearing price or total quantity).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Tuple


@dataclass
class Game:
    name: str
    roles: Tuple[str, ...]
    action: str           # label the agent must use, e.g. "Price"
    lo: float
    hi: float
    rounds: int = 10
    rng: random.Random = field(default_factory=random.Random)
    round: int = 0

    # ---- interface -------------------------------------------------------------------------------
    def reset(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.round = 0
        self._draw()

    def _draw(self) -> None:  # per-round private draws, overridden where needed
        pass

    def observe(self, role: str) -> Dict[str, float]:
        return {}

    def step(self, actions: Mapping[str, float]) -> Tuple[Dict[str, float], Dict[str, float]]:
        raise NotImplementedError

    def benchmarks(self) -> Dict[str, float]:
        return {}

    def clip(self, x: float) -> float:
        return min(max(float(x), self.lo), self.hi)


class Pricing(Game):
    """Differentiated Bertrand duopoly: q_i = max(0, 10 - 1.5 p_i + 0.5 p_j), unit cost 1 (the sprint's pricing game)."""

    def __init__(self, rounds: int = 10):
        super().__init__("pricing", ("firm_a", "firm_b"), "Price", 0.0, 10.0, rounds)

    def step(self, actions):
        a, b = actions["firm_a"], actions["firm_b"]
        qa, qb = max(0.0, 10 - 1.5 * a + 0.5 * b), max(0.0, 10 - 1.5 * b + 0.5 * a)
        rew = {"firm_a": (a - 1) * qa, "firm_b": (b - 1) * qb}
        self.round += 1
        return rew, {"metric": (a + b) / 2, "qa": qa, "qb": qb}

    def benchmarks(self):
        return {"cost": 1.0, "nash": 4.6, "joint": 5.5}


class Auction(Game):
    """First-price sealed-bid auction, 3 bidders, private values ~ N(10, 2) floored at the reserve 3."""

    def __init__(self, rounds: int = 10):
        super().__init__("auction", ("bidder_a", "bidder_b", "bidder_c"), "Bid", 0.0, 50.0, rounds)
        self.values: Dict[str, float] = {}

    def _draw(self):
        self.values = {r: max(3.0, self.rng.gauss(10, 2)) for r in self.roles}

    def observe(self, role):
        return {"value": self.values[role]}

    def step(self, actions):
        valid = {r: b for r, b in actions.items() if b >= 3.0}
        rew = {r: 0.0 for r in self.roles}
        if valid:
            top = max(valid.values())
            winners = [r for r, b in valid.items() if b == top]
            w = winners[self.rng.randrange(len(winners))]
            rew[w] = self.values[w] - top
            price = top
        else:
            w, price = "", 0.0
        info = {"metric": price, "winner": w, "values": dict(self.values)}
        self.round += 1
        self._draw()
        return rew, info

    def benchmarks(self):
        return {"reserve": 3.0, "mean_value": 10.0}


class Cournot(Game):
    """Cournot duopoly: P = max(0, 20 - Q), unit cost 2. Nash q = 6 each (Q = 12), joint-profit q = 4.5 each (Q = 9)."""

    A, C = 20.0, 2.0

    def __init__(self, rounds: int = 10):
        super().__init__("cournot", ("firm_a", "firm_b"), "Quantity", 0.0, 20.0, rounds)

    def step(self, actions):
        qa, qb = actions["firm_a"], actions["firm_b"]
        p = max(0.0, self.A - (qa + qb))
        rew = {"firm_a": (p - self.C) * qa, "firm_b": (p - self.C) * qb}
        self.round += 1
        return rew, {"metric": qa + qb, "price": p}

    def benchmarks(self):
        return {"nash_total": 12.0, "joint_total": 9.0, "competitive_total": 18.0}


GAMES = {"pricing": Pricing, "auction": Auction, "cournot": Cournot}


def make_game(name: str, rounds: int = 10) -> Game:
    return GAMES[name](rounds)
