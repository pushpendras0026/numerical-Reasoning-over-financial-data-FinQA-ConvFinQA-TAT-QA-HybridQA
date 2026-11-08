#!/usr/bin/env bash
# Resume Block A after the daily quota resets, then rebuild every table and the PDF.
# Safe to rerun: saved answers are reused, and only unanswered requests are sent.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1
PY=.venv/bin/python
DATASETS="finqa tatqa tathqa convfinqa hybridqa multihiertt"
for round in 1 2 3 4 5 6; do
  # Records with no saved response were refused, so clearing them loses nothing.
  $PY - <<'PYTHON'
import glob, json, sqlite3
for path in glob.glob('artifacts/v11/a/*_eval/cache.sqlite'):
    db = sqlite3.connect(path)
    for key, text in db.execute('SELECT key, record FROM requests').fetchall():
        if 'raw_response' not in json.loads(text):
            db.execute('DELETE FROM requests WHERE key=?', (key,))
    db.commit()
PYTHON
  scripts/run_v11.sh a gemini-3.5-flash-lite eval $DATASETS
  left=$($PY - <<'PYTHON'
import glob, json
left = 0
for path in glob.glob('artifacts/v11/a/*_eval/manifest.json'):
    m = json.load(open(path))
    left += m.get('expected_requests', 1) - m.get('completed_requests', 0)
print(left)
PYTHON
)
  echo "round $round: $left requests left"
  [ "$left" -eq 0 ] && break
  sleep 600
done
$PY scripts/error_analysis.py artifacts/v11/a eval dependency
$PY scripts/report_tables.py --a artifacts/v11/a > /dev/null
(cd report && tectonic -X compile main.tex 2>&1 | tail -1)
