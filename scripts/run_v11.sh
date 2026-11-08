#!/usr/bin/env bash
# Freeze and run one block. Usage: run_v11.sh BLOCK MODEL MODE[,MODE] DATASET...
# Example: run_v11.sh a gemini-3.5-flash-lite eval finqa tatqa
# Reruns resume from each run's ledger; completed answers are never re-requested.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 GEMINI_MODEL=$2
BLOCK=$1; MODES=${3//,/ }; shift 3
PY=.venv/bin/python
for data in "$@"; do (
  for mode in $MODES; do
    name="${data}_${mode}"; frozen="experiments/frozen_v11/${BLOCK}/${name}.json"; out="artifacts/v11/${BLOCK}/${name}"
    [ -f "$frozen" ] || $PY -m nrqa.experiment freeze "experiments/v11/${name}.json" "$frozen" >/dev/null
    $PY -m nrqa.experiment run "$frozen" "$out" --mode live | cut -c1-200 | sed "s/^/${name}: /"
    $PY -m nrqa.experiment evaluate "$frozen" "$out" | cut -c1-400 | sed "s/^/${name} score: /"
  done ) &
done
wait
