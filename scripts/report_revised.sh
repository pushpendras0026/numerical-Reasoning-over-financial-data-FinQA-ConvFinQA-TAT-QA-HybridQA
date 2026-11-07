#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src:$PWD/scripts${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
/home/p_2626/bigdata-env/bin/python - <<'PY'
import json,collections
from pathlib import Path
from nrqa.experiment import write
from aggregate_results import aggregate
base=Path('artifacts');records=[];lines=[r'\section{Revised executable-plan evaluation}','Original zero-score bounded results and the full FinQA baseline above remain unchanged. Revised contracts are separate experiments. The broad schema was replaced by a disjunction of kind-specific schemas with required fields; strict executor validation remains active. Instructions were shortened to fit the unchanged context budget. Training diagnostics informed an explicit rule forbidding forward or self references in the first arithmetic step. No prediction was repaired using gold answers or reference programs. The same local model digest, generation settings and evidence cap were retained.', 'Version 1 stopped at the context-budget guard before inference. Version 2 used compact instructions; version 3 added an explicit prior-step rule and illustration. Development selection used seed 2626 before inference. Non-FinQA dev selections exclude original evaluated IDs and earlier revised frozen selections. FinQA uses an explicitly authorized overlapping 40-question dev rerun because all 883 dev questions were already evaluated. It is not a fresh independent sample.']
audit=json.loads((base/'revised_evaluation_v2/failure_sample_audit.json').read_text())
lines.append('A fixed seed-2626 sample of 12 saved original failures per dataset was inspected before revision. The following groups retain the actual violated rule; detailed IDs and saved errors are in the audit JSON.')
for n,groups in audit.items():lines.append(n+': '+', '.join(f'{k} ({len(v)})' for k,v in groups.items())+'.')
for version in ['v2','v3','v4','v5']:
 b=base/f'revised_evaluation_{version}';runs=[]
 for stage in ['training_diagnostic','dev','direct_training']:
  if not list(b.glob(f'*_{stage}/metrics.json')):continue
  lines.extend([r'\begin{center}\small\setlength{\tabcolsep}{2pt}\begin{tabular}{llrrrrr}',r'Dataset & Method & $N$ & Parse & Exec & Correct & Score\\\hline'])
  for n in ['finqa','tatqa','tathqa','multihiertt','convfinqa']:
   p=b/f'{n}_{stage}';mp=p/'metrics.json'
   if not mp.exists():continue
   rows=json.loads((p/'results.json').read_text()) if (p/'results.json').exists() else [];metrics=json.loads(mp.read_text())
   for v,z in metrics.items():
    selected=[r for r in rows if r['variant']==v];parsed=sum(r['prediction'].get('parsed_prediction') is not None for r in selected);exportable=z['counts'].get('ok',0);executed=sum(r['prediction'].get('execution',{}).get('status')=='ok' for r in selected);key='execution' if n in ['finqa','convfinqa'] else 'f1';score=z['metrics'].get('direct_numeric_auxiliary',z['metrics'].get(key,0));correct_key='direct_numeric_auxiliary' if 'direct_numeric_auxiliary' in z['metrics'] else 'execution' if n in ['finqa','convfinqa'] else 'em';correct=sum(x.get('score',{}).get(correct_key,0)==1 for x in z.get('per_example',[]))
    label={'finqa':'FinQA','tatqa':'TAT-QA','tathqa':'TAT-HQA','convfinqa':'ConvFinQA','multihiertt':'MultiHiertt'}[n];method={'ordinary':'O','dependency':'D','length_matched':'L'}[v]
    lines.append(f'{label} & {method} & {z["denominator"]} & {parsed} & {executed} & {correct} & {100*score:.2f}\\\\')
    records.append({'version':version,'stage':stage,'dataset':n,'method':v,'selected':z['denominator'],'saved':len(selected),'parsed':parsed,'executable':executed,'exportable_executable':exportable,'correct':correct,'counts':z['counts'],'official_metrics':z['metrics']})
   if stage=='dev':runs.append(p)
  lines.extend([r'\end{tabular}\end{center}',f'{version}, '+stage.replace('_',' ')+'. Parse counts include well-formed abstentions; executable counts exclude abstentions and include locally executed answers without an official program export; unsupported exports are listed separately and score zero. Correct counts exact matches (or correct official executions); partial-credit F1 is reported separately. Score is percent official execution accuracy (FinQA/ConvFinQA) or F1 (others). Missing and failed outputs remain in the denominator.'])
 for p in b.glob('*.scale_blocked.json'):lines.append(version+' '+p.name.split('.')[0]+' was blocked from scaling: no executable training diagnostic output. This is not a measured zero development score.')
 if runs:
  aggregate(runs,b/'aggregate')
  summary=json.loads((b/'aggregate/summary.json').read_text())
  for comparison in summary['comparisons']:
   z=comparison['paired_bootstrap'];lines.append(f"{version} {comparison['dataset']}: paired dependency minus ordinary {comparison['metric']} difference {z['difference']:.5f}, document/conversation bootstrap 95\\% interval [{z['ci95'][0]:.5f}, {z['ci95'][1]:.5f}], {z['clusters']} clusters, 1000 resamples, seed 2626.")
lines.append('Versions 4 and 5 are restricted single-operation arithmetic ablation: prior-step references are disallowed by schema. It cannot solve general multi-step arithmetic and is not equivalent to the full executor configuration. Version 4 stopped at the context-budget guard; version 5 shortens its instructions without changing the restriction. Direct training rows are a separate baseline; their Exec column counts accepted direct answers rather than executed numerical programs; FinQA and ConvFinQA use auxiliary numeric accuracy, not official program accuracy.')
lines.append('HybridQA remains unevaluated: a required genuine linked table file is missing. The revised studies are separated by contract and dataset; overlapping source datasets are not pooled as independent observations. Training diagnostic success is a gate, not evidence of generalization or guaranteed packing improvement.')
lines.append('For direct training diagnostics, FinQA and ConvFinQA scores are auxiliary numeric accuracy, not official program accuracy. Version-4 context-blocked trials are incomplete diagnostic failures, not completed development scores. Failure tables below sum the three methods; per-method counts remain in the JSON summary.')
for version in ['v2','v3','v4','v5']:
 for stage in ['training_diagnostic','dev','direct_training']:
  group=[r for r in records if r['version']==version and r['stage']==stage]
  if not group:continue
  lines.extend([r'\begin{center}\small\setlength{\tabcolsep}{2pt}\begin{tabular}{lrrrrr}',r'Dataset & Saved & A & E & I & M\\\hline'])
  for n in sorted({r['dataset'] for r in group}):
   rows=[r for r in group if r['dataset']==n];c=collections.Counter()
   for r in rows:c.update(r['counts'])
   errors=c.get('invalid',0)+c.get('unsupported_export',0)
   lines.append(f"{n} & {sum(r['saved'] for r in rows)} & {c.get('abstain',0)} & {errors} & {c.get('api_failure',0)} & {c.get('missing',0)}\\\\")
  lines.extend([r'\end{tabular}\end{center}',version+' '+stage.replace('_',' ')+': A abstained; E invalid or unsupported export; I infrastructure failure; M missing.'])
Path('report/generated/revised_results.tex').write_text('\n'.join(lines)+'\n');write(base/'revised_evaluation_summary.json',records)
p=Path('report/main.tex');s=p.read_text();needle=r'\input{generated/revised_results.tex}'
if needle not in s:s=s.replace(r'\section{Reproducibility}',needle+'\n\n'+r'\section{Reproducibility}');p.write_text(s)
PY
make -C report > artifacts/revised_pdf_build.log 2>&1
