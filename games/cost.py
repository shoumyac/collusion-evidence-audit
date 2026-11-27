"""Token and dollar accounting with a hard cap. Prices are USD per 1M tokens (input, output) as we used them in Nov 2026;
check the provider's current price list before relying on the totals."""
from __future__ import annotations

import json
import threading
from pathlib import Path

PRICES = {"haiku": (0.10, 0.50), "sonnet": (2.0, 10.0), "opus": (4.0, 20.0), "fable": (10.0, 50.0)}


class BudgetExceeded(RuntimeError):
    pass


def price_for(model: str):
    m = model.lower()
    for k, v in PRICES.items():
        if k in m:
            return v
    return (0.0, 0.0)  # open weights on your own GPU or the stub: no API fee


class CostTracker:
    def __init__(self, model: str, budget_usd: float | None = None, log: Path | None = None):
        self.pin, self.pout = price_for(model)
        self.budget, self.log = budget_usd, log
        self.i = self.o = self.calls = 0
        self._lock = threading.Lock()

    @property
    def usd(self) -> float:
        return self.i * self.pin / 1e6 + self.o * self.pout / 1e6

    def add(self, tin: int, tout: int) -> None:
        with self._lock:
            self.i += tin
            self.o += tout
            self.calls += 1
            if self.budget is not None and self.usd > self.budget:
                raise BudgetExceeded(f"spent ${self.usd:.2f}, over the cap of ${self.budget:.2f}")

    def check_headroom(self, extra_usd: float) -> None:
        if self.budget is not None and self.usd + extra_usd > self.budget:
            raise BudgetExceeded(f"next run could exceed the cap (${self.usd:.2f} spent, cap ${self.budget:.2f})")

    def save(self) -> None:
        if self.log:
            self.log.parent.mkdir(parents=True, exist_ok=True)
            self.log.write_text(json.dumps({"calls": self.calls, "input_tokens": self.i, "output_tokens": self.o, "usd": round(self.usd, 4),
                                            "budget_usd": self.budget}, indent=1))


def estimate_usd(model: str, runs: int, in_tokens_per_run: int = 39000, out_tokens_per_run: int = 2300) -> float:
    pin, pout = price_for(model)
    return runs * (in_tokens_per_run * pin + out_tokens_per_run * pout) / 1e6
