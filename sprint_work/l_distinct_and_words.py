"""(1) Apply our own pseudoreplication test to our LLM runs: how many DISTINCT price trajectories / transcripts are there per
condition? (2) Leakage check for the naive-Bayes message classifier: folds are split by run (each item is a whole run);
list the top words, with and without the prompts' own vocabulary masked.
Writes out/l_distinct.json, out/l_words.json, out/table_words.tex
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

root = Path(__file__).parent / "out"
TAGS = ["Qwen2.5-7B-Instruct", "Qwen2.5-32B-Instruct", "phi-4", "Mistral-Nemo-12B", "claude-haiku-5-5", "claude-sonnet-5-5",
        "claude-haiku-5-5-v2", "claude-sonnet-5-5-v2"]
CONDS = ["honest", "collude", "honest_silent", "collude_silent", "honest_para", "collude_para", "honest_swap", "collude_swap"]
src = (Path(__file__).parent / "c_llm_agents.py").read_text(encoding="utf-8")
PROMPT_VOCAB = set(re.findall(r"[a-z']+", src[src.index("BASE ="):src.index("PRICE_RE")].lower()))


def load(tag, cond):
    runs = []
    for p in sorted((root / "llm" / tag / cond).glob("*.jsonl")):
        recs = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        runs.append(recs)
    return runs


distinct = {}
for tag in TAGS:
    for cond in CONDS:
        runs = load(tag, cond)
        if not runs:
            continue
        paths = {tuple(tuple(r["action"] for r in rec if r["agent_id"] == a) for a in ("firm_a", "firm_b")) for rec in runs}
        msgs = {tuple(r["message"] for r in rec) for rec in runs}
        mean_p = {round(sum(float(r["action"]) for r in rec) / len(rec), 4) for rec in runs}
        distinct[f"{tag}|{cond}"] = {"runs": len(runs), "distinct_price_paths": len(paths), "distinct_transcripts": len(msgs),
                                     "distinct_run_mean_prices": len(mean_p)}
(root / "l_distinct.json").write_text(json.dumps(distinct, indent=1))


def toks(text, mask):
    ws = [w.strip(".,;:!?\"'()") for w in text.lower().replace("price:", " ").split() if not any(c.isdigit() for c in w)]
    return {w for w in ws if w and not (mask and w in PROMPT_VOCAB)}


words = {}
for tag in TAGS[:6]:
    h, c = load(tag, "honest"), load(tag, "collude")
    res = {}
    for mask in (False, True):
        cnt = {0: Counter(), 1: Counter()}
        for y, runs in ((0, h), (1, c)):
            for rec in runs:
                cnt[y].update(toks(" ".join(r["message"] for r in rec), mask))
        n0, n1 = len(h), len(c)
        scored = []
        for w in set(cnt[0]) | set(cnt[1]):
            if cnt[0][w] + cnt[1][w] < 5:
                continue
            scored.append((math.log(((cnt[1][w] + 1) / (n1 + 2)) / ((cnt[0][w] + 1) / (n0 + 2))), w))
        scored.sort()
        res["masked" if mask else "all"] = {"collude_words": [w for _, w in scored[::-1][:10]], "honest_words": [w for _, w in scored[:10]]}
    words[tag] = res
(root / "l_words.json").write_text(json.dumps(words, indent=1))
NM = {"Qwen2.5-7B-Instruct": "Qwen2.5-7B", "Qwen2.5-32B-Instruct": "Qwen2.5-32B", "phi-4": "Phi-4", "Mistral-Nemo-12B": "Mistral-Nemo",
      "claude-haiku-5-5": "Haiku 5.5", "claude-sonnet-5-5": "Sonnet 5.5"}
rows = []
for tag, r in words.items():
    esc = lambda ws: ", ".join(w.replace("_", "\\_") for w in ws[:8])
    rows.append(f"{NM[tag]} & {esc(r['masked']['collude_words'])} & {esc(r['masked']['honest_words'])} \\\\")
(root / "table_words.tex").write_text("\\begin{tabular}{lp{5.4cm}p{5.4cm}}\n\\toprule\nagents & top words, collusion condition & top words, honest condition \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
for k, v in distinct.items():
    print(k, v)
for t, r in words.items():
    print(t, "masked collude:", r["masked"]["collude_words"][:6], "| honest:", r["masked"]["honest_words"][:6])
