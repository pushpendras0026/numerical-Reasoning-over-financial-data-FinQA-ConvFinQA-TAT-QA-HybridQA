#!/usr/bin/env bash
# Spark preparation at three real data sizes and four core counts, checked against
# the Python reference after every run. Sizes are records per dev source.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
export JAVA_HOME=/opt/homebrew/opt/openjdk@17
export PYSPARK_SUBMIT_ARGS="--driver-memory ${SPARK_DRIVER_MEMORY:-3g} pyspark-shell"
PY=.venv/bin/python
CONFIGS=(experiments/v11/finqa_eval.json experiments/v11/tatqa_eval.json experiments/v11/tathqa_eval.json
         experiments/v11/convfinqa_eval.json experiments/v11/hybridqa_eval.json experiments/v11/multihiertt_eval.json)
for size in "$@"; do
  out="artifacts/v11/spark/$size"; mkdir -p "$out/spark-events"
  limit=(); [ "$size" = full ] || limit=(--limit "$size")
  $PY scripts/measure_resources.py --out "$out/python.json" -- \
    $PY scripts/prepare_data.py "${CONFIGS[@]}" --out "$out" ${limit[@]+"${limit[@]}"} > /dev/null
  # Same workload as Spark's, on already-prepared JSONL, so the two are comparable.
  $PY scripts/measure_resources.py --out "$out/python_workload.json" -- \
    $PY -c "from nrqa.preparation import reference; reference('$out')" > /dev/null
  for cores in 1 2 4 8; do
    $PY scripts/measure_resources.py --out "$out/resources_$cores.json" -- \
      $PY scripts/prepare_data.py --out "$out" --spark --master "local[$cores]" > /dev/null
    cp "$out/spark_measurement.json" "$out/measurement_$cores.json"
    echo "$size local[$cores] done"
  done
done
