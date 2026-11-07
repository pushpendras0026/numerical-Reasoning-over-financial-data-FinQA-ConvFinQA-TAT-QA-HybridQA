#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if pgrep -af '[/]run_local_submission.sh|local_submission.py run|nrqa.experiment run'; then
  echo 'An old runner may still be active; refusing new dispatch.' >&2
  exit 1
fi
if ! command -v pdflatex >/dev/null || ! command -v pdftoppm >/dev/null; then
  sudo apt-get install -y texlive-latex-base texlive-latex-recommended texlive-fonts-recommended poppler-utils
fi
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://172.25.80.1:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b-instruct}"
bash scripts/resume_bounded_submission.sh
if [[ -f report/main.pdf ]]; then
  pdfinfo report/main.pdf > artifacts/bounded_submission/pdf_info.txt
  pdftotext report/main.pdf artifacts/bounded_submission/report_text.txt
  mkdir -p artifacts/bounded_submission/pdf_preview
  pdftoppm -scale-to 1400 -png report/main.pdf artifacts/bounded_submission/pdf_preview/page
  echo 'Compiled PDF: report/main.pdf. Inspect the rendered pages before submitting.'
else
  echo 'PDF compilation failed: inspect report/main.log; source archive is not a final PDF.' >&2
  exit 1
fi
