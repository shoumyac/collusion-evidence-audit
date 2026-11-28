#!/bin/bash
# Cross-condition replay (collude agents read honest-run text, honest agents read collude-run text).
# Usage: LLM_BASE_URL=<endpoint>/v1 bash games/run_xswap.sh <model> <results_subdir> <runs>
# Example: LLM_BASE_URL=https://.../v1 bash games/run_xswap.sh Qwen/Qwen3-8B qwen3_8b 100
set -e
M=$1; SUB=$2; N=${3:-50}
cd "$(dirname "$0")/.."
OUT=${OUT:-/tmp/xswap_$SUB}
mkdir -p "$OUT"; cp -r results/$SUB/* "$OUT"/   # base runs are the text source
for w in 1 2 3; do
  python3 -m games.runner --game pricing --backend openai --model $M --runs $N --wording $w --workers 40 \
    --conditions collude_xswap,honest_xswap --out "$OUT" || true
done
mkdir -p results_xswap/$SUB
for d in "$OUT"/pricing-*; do n=$(basename $d); mkdir -p results_xswap/$SUB/$n; cp -r $d/collude_xswap $d/honest_xswap results_xswap/$SUB/$n/ 2>/dev/null || true; done
