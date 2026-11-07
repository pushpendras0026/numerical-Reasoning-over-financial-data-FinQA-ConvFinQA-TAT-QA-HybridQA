#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
PYTHON="${NRQA_PYTHON:-/home/p_2626/bigdata-env/bin/python}"
mkdir -p artifacts/ollama_submission
"$PYTHON" scripts/validate_local.py --out artifacts/ollama_submission/data_validation.json
"$PYTHON" scripts/local_submission.py prepare
if [[ ! -f artifacts/ollama_submission/diagnostic.json ]]; then
  "$PYTHON" scripts/local_submission.py diagnostic
fi
"$PYTHON" scripts/local_submission.py run smoke
"$PYTHON" scripts/local_submission.py run finqa_pilot
"$PYTHON" scripts/local_submission.py finish
# Other real-evidence datasets default to pilots. FULL_SPLITS=1 selects full splits.
if [[ "${FULL_SPLITS:-0}" == 1 ]]; then
  runs=(finqa_full_dev finqa_full_test convfinqa_full_dev convfinqa_full_test tatqa_full_dev tatqa_full_test tathqa_full_dev tathqa_full_test multihiertt_full_dev multihiertt_full_test)
else
  runs=(convfinqa_pilot tatqa_pilot tathqa_pilot multihiertt_pilot)
fi
for run in "${runs[@]}"; do
  "$PYTHON" scripts/local_submission.py run "$run"
  "$PYTHON" scripts/local_submission.py finish
done
make -C report
"$PYTHON" scripts/package_delivery.py --out artifacts/ollama_submission/nrqa-source.tar.gz
