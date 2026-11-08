#!/usr/bin/env bash
# Freeze Block A under the final code and carry its saved responses forward once.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
for data in finqa tatqa tathqa convfinqa hybridqa multihiertt; do
  name="${data}_eval"; out="artifacts/v11/a/$name"; mkdir -p "$out"
  [ -f "experiments/frozen_v11/a/$name.json" ] || .venv/bin/python -m nrqa.experiment freeze "experiments/v11/$name.json" "experiments/frozen_v11/a/$name.json" >/dev/null
  [ -f "$out/cache.sqlite" ] || .venv/bin/python scripts/carry_ledger.py "artifacts/v11/t50/$name/cache.sqlite" "$out/cache.sqlite"
done
