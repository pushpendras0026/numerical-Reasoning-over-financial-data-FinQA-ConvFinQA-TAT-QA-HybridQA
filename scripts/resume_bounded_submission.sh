#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/scripts:$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://172.25.80.1:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b-instruct}"
PYTHON=/home/p_2626/bigdata-env/bin/python
if [[ "${1:-}" != finalize ]]; then
  "$PYTHON" scripts/bounded_submission.py workflow --dispatch-hours 3.5
fi
"$PYTHON" - <<'PY'
import json,collections,hashlib
from pathlib import Path
from nrqa.experiment import evaluate,write
from aggregate_results import aggregate
base=Path('artifacts/bounded_submission');names=['tatqa','tathqa','multihiertt','convfinqa'];runs=[Path('artifacts/ollama_submission/finqa_full_dev')]
coverage={}
for n in names:
 p=base/n;f=json.loads((base/f'{n}.frozen.json').read_text());m=json.loads((p/'manifest.json').read_text());expected={(i,v) for i in f['ids'] for v in f['config']['variants']}
 rows=json.loads((p/'results.json').read_text()) if (p/'results.json').exists() else []
 saved={(r['id'],r['variant']) for r in rows};assert saved<=expected
 evaluate(base/f'{n}.frozen.json',p);runs.append(p)
 coverage[n]={'status':m['status'],'saved_rows':len(saved),'expected_rows':len(expected),'pending_rows':len(expected-saved),'prediction_statuses':dict(collections.Counter(r['prediction']['status'] for r in rows)),'error':m.get('error')}
write(base/'resume_coverage.json',coverage)
aggregate(runs,base/'aggregate')
def tex(s):
 for a,b in [('\\',r'\textbackslash{}'),('_',r'\_'),('%',r'\%'),('&',r'\&'),('#',r'\#'),('$',r'\$'),('{',r'\{'),('}',r'\}')]:s=str(s).replace(a,b)
 return s
lines=[r'\section{Measured results and coverage}',
'FinQA uses the full 883-question development split. The other datasets use the original frozen development subsets: 20 questions each for TAT-QA, TAT-HQA and MultiHiertt, and 22 ordered ConvFinQA turns in complete conversations. Seed 2626 and all three packing methods are fixed; no selected examples overlap the earlier pilots. HybridQA is unevaluated: the genuine linked evidence corpus remains missing.',
'FinQA test remains incomplete (162 saved rows, 54 per method, one unresolved inflight request) and is excluded from architectural comparisons.',
r'\begin{center}\small\setlength{\tabcolsep}{2pt}\begin{tabular}{llrrr}',r'Dataset & Method & $N$ & Saved & Score\\\hline']
statuslines=[r'\begin{center}\small\setlength{\tabcolsep}{2pt}\begin{tabular}{llrrrrr}',r'Dataset & Method & V & A & E & I & M\\\hline']
details=[];labels={'finqa_full_dev':'FinQA','tatqa':'TAT-QA','tathqa':'TAT-HQA','multihiertt':'MultiHiertt','convfinqa':'ConvFinQA'}
for p in runs:
 metrics=json.loads((p/'metrics.json').read_text());rows=json.loads((p/'results.json').read_text()) if (p/'results.json').exists() else []
 for v in ['ordinary','dependency','length_matched']:
  z=metrics[v];c=z.get('counts',{});method={'ordinary':'O','dependency':'D','length_matched':'L'}[v];n=z['denominator'];key='execution' if p.name in ['finqa_full_dev','convfinqa'] else 'f1';score=z.get('metrics',{}).get(key)
  saved=sum(r['variant']==v for r in rows);infra=c.get('api_failure',0);missing=c.get('missing',0);valid=c.get('ok',0);abstain=c.get('abstain',0);invalid=sum(c.values())-valid-abstain-infra-missing
  # No all-missing run is represented as an observed zero accuracy.
  display=f'{100*score:.2f}' if score is not None and saved else '--'
  label=labels[p.name];lines.append(f'{label} & {method} & {n} & {saved} & {display}\\\\')
  statuslines.append(f'{label} & {method} & {valid} & {abstain} & {invalid} & {infra} & {missing}\\\\')
  details.append({'dataset':p.name,'method':v,'selected_examples':n,'saved_predictions':saved,'valid':valid,'abstentions':abstain,'execution_or_export_failures':invalid,'infrastructure_failures':infra,'missing_outputs':missing,'scores':z.get('metrics',{}),'inference_observed':bool(saved)})
lines += [r'\end{tabular}\end{center}','O: ordinary; D: dependency; L: length matched. Scores are percentages: official execution accuracy for FinQA/ConvFinQA and official F1 for the other datasets. All selected examples remain in the denominator; missing, infrastructure-failed, abstained and invalid answers receive zero. Saved coverage includes invalid answers, rather than equating response completion with valid execution.']
lines += statuslines+[r'\end{tabular}\end{center}','V: valid executable/exportable answer; A: abstention; E: execution, plan-validation or official-export failure; I: infrastructure failure; M: missing output. A missing-only run is reported as unevaluated rather than an observed zero score.']
for n,z in coverage.items():lines.append(tex(f"{labels[n]}: status {z['status']}; saved {z['saved_rows']}/{z['expected_rows']}, pending {z['pending_rows']}."))
summary=json.loads((base/'aggregate/summary.json').read_text())
for c in summary['comparisons']:
 if c['dataset']!='finqa' and coverage[c['dataset']]['saved_rows']==0:continue
 b=c['paired_bootstrap'];lines.append(f"{tex(c['dataset'])}: dependency minus ordinary {tex(c['metric'])} = {b['difference']:.5f}; paired document/conversation bootstrap 95\\% interval [{b['ci95'][0]:.5f}, {b['ci95'][1]:.5f}], {b['clusters']} clusters (1000 resamples; seed 2626).")
lines.append('Subsets and rare successes yield unstable intervals and cannot establish population improvement. Zero-width bootstrap intervals for all-zero samples reflect absent empirical variation and do not establish equivalence. Related datasets share source tables, so scores and uncertainty are kept separate. FinQA dependency packing achieved two correct executions out of 883, compared with none for ordinary and length matched; this is weak evidence rather than guaranteed improvement. No changes to prompts or outputs were tuned against evaluation answers.')
for p in runs:
 rows=json.loads((p/'results.json').read_text()) if (p/'results.json').exists() else []
 failures=[r for r in rows if r['prediction'].get('execution',{}).get('status')=='invalid']
 if failures:
  r=failures[0];lines.append(tex(f"Failure ({labels[p.name]}, {r['variant']}, {r['id']}): {str(r['prediction']['execution'].get('error','invalid plan'))[:140]}."))
Path('report/generated/bounded_results.tex').write_text('\n'.join(lines)+'\n');write(base/'report_measurements.json',details)
original=json.loads((base/'before_resume/finqa_sha256.json').read_text());finqa=Path('artifacts/ollama_submission/finqa_full_dev')
assert all(hashlib.sha256((finqa/n).read_bytes()).hexdigest()==h for n,h in original.items()),'FinQA artifact changed'
write(base/'finqa_preservation_check.json',{'all_original_hashes_match':True})
print(json.dumps(coverage,indent=2))
PY
make -C report > artifacts/bounded_submission/pdf_build_resume.log 2>&1
pdfinfo report/main.pdf > artifacts/bounded_submission/pdf_info_resume.txt
pdftotext report/main.pdf artifacts/bounded_submission/report_text_resume.txt
mkdir -p artifacts/bounded_submission/pdf_preview_resume
pdftoppm -scale-to 1400 -png report/main.pdf artifacts/bounded_submission/pdf_preview_resume/page
"$PYTHON" scripts/package_delivery.py --out artifacts/bounded_submission/nrqa-source.tar.gz
