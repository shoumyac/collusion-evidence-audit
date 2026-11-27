"""Model backends. All return (text, input_tokens, output_tokens).

stub       : rule-based agents for free end-to-end tests (no network).
anthropic  : Anthropic Messages API (key from ANTHROPIC_API_KEY or a gitignored .anthropic_key file at the repo root).
openai     : any OpenAI-compatible server (vLLM, Ollama, a hosted provider); set LLM_BASE_URL and optionally LLM_API_KEY.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.request
from pathlib import Path


class Stub:
    """Deterministic fake agent. A collusion instruction moves its choice toward the 'good' end of the range, so a stub run
    exercises the whole pipeline and gives a known positive effect."""

    def __init__(self, game_name: str):
        self.g = game_name

    def ask(self, system: str, user: str, max_tokens: int = 200):
        seed = int(hashlib.sha256((system + user).encode()).hexdigest()[:12], 16)
        r = random.Random(seed)
        collude = "coordinate" in system or "steer the market" in system or "Signal this" in system
        if self.g == "pricing":
            x, label = r.gauss(2.0 + (1.5 if collude else 0.0), 0.4), "Price"
        elif self.g == "auction":
            x, label = r.gauss(9.5 - (4.0 if collude else 0.0), 0.6), "Bid"
        else:
            x, label = r.gauss(12.0 - (2.5 if collude else 0.0), 0.7), "Quantity"
        x = max(0.0, x)
        said = "Let us keep things steady." if collude else "I will just look after my own profit."
        text = f"{said} {label}:{x:.2f}"
        return text, len(system.split()) + len(user.split()), len(text.split())


class Anthropic:
    def __init__(self, model: str, root: Path):
        import anthropic  # imported lazily so the stub needs nothing installed

        key = os.environ.get("ANTHROPIC_API_KEY")
        kf = root / ".anthropic_key"
        if not key and kf.exists():
            key = kf.read_text().strip()
        if not key:
            raise RuntimeError("no API key: set ANTHROPIC_API_KEY or create .anthropic_key at the repo root (it is gitignored)")
        self.m = model
        self.c = anthropic.Anthropic(api_key=key, max_retries=4)

    def ask(self, system: str, user: str, max_tokens: int = 250):
        err = None
        for a in range(3):
            try:
                r = self.c.messages.create(model=self.m, system=system, messages=[{"role": "user", "content": user}], max_tokens=max_tokens,
                                           thinking={"type": "between_tools" if "sonnet" in self.m else "disabled"})
                text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
                return text, r.usage.input_tokens, r.usage.output_tokens
            except Exception as e:  # noqa: BLE001
                err = e
                time.sleep(2 + 3 * a)
        raise RuntimeError(f"call failed: {err!r}")


class OpenAICompat:
    def __init__(self, model: str):
        self.m = model
        self.base = os.environ["LLM_BASE_URL"].rstrip("/")
        self.key = os.environ.get("LLM_API_KEY", "none")

    def ask(self, system: str, user: str, max_tokens: int = 250):
        req_body = {"model": self.m, "temperature": 0.7, "max_tokens": max_tokens,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if os.environ.get("LLM_THINKING", "off") == "off":  # Qwen3-style models otherwise spend the token budget on <think> blocks
            req_body["chat_template_kwargs"] = {"enable_thinking": False}
        body = json.dumps(req_body).encode()
        err = None
        for a in range(3):
            try:
                req = urllib.request.Request(self.base + "/chat/completions", body, {"Content-Type": "application/json", "Authorization": "Bearer " + self.key})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    d = json.load(resp)
                u = d.get("usage", {})
                return d["choices"][0]["message"]["content"], int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))
            except Exception as e:  # noqa: BLE001
                err = e
                time.sleep(2 + 3 * a)
        raise RuntimeError(f"call failed: {err!r}")


def make_backend(kind: str, model: str, game: str, root: Path):
    if kind == "stub":
        return Stub(game)
    if kind == "anthropic":
        return Anthropic(model, root)
    if kind == "openai":
        return OpenAICompat(model)
    raise ValueError(kind)
