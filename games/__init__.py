"""Small, dependency-light game runner for the next version of the collusion audit.

Three repeated games (pricing duopoly, first-price auction, Cournot duopoly), four prompt wordings, the swap control,
three backends (stub for free testing, Anthropic API, any OpenAI-compatible server such as vLLM) and a hard cost cap.
Run `python -m games.runner --help` from the repository root.
"""
