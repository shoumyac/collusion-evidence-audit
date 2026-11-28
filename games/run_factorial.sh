#!/bin/bash
# Puppet factorial: one live agent vs open-loop puppet rivals; text source x action source in {collude-run, honest-run}.
# Usage: LLM_BASE_URL=<endpoint>/v1 bash games/run_factorial.sh <model> <results_subdir> <runs> "<games>"
# Example: bash games/run_factorial.sh Qwen/Qwen3-8B qwen3_8b 60 "pricing auction"
M=$1; SUB=$2; N=${3:-60}; GAMES=${4:-pricing}
cd "$(dirname "$0")/.."
OUT=${OUT:-/tmp/fact_$SUB}; mkdir -p "$OUT"; cp -r results/$SUB/* "$OUT"/
CONDS=""
for z in collude honest; do for ta in cc ch hc hh cc-coh hh-coh; do CONDS="$CONDS,pup-$z-$ta"; done; done
CONDS=${CONDS#,}
for g in $GAMES; do for w in 1 2 3; do
  python3 -m games.runner --game $g --backend openai --model $M --runs $N --wording $w --workers 40 --conditions $CONDS --out "$OUT" || true
done; done
for d in "$OUT"/*; do n=$(basename $d); mkdir -p results_factorial/$SUB/$n; for c in $d/pup-*; do cp -r $c results_factorial/$SUB/$n/; done; done
