#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://172.25.80.1:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b-instruct}"
curl --fail --silent --show-error --max-time 8 "$OLLAMA_BASE_URL/api/tags" >/dev/null
PYTHON_BIN="${PYTHON_BIN:-/home/p_2626/bigdata-env/bin/python}"
"$PYTHON_BIN" -u scripts/recovery_evaluation.py "$@"
