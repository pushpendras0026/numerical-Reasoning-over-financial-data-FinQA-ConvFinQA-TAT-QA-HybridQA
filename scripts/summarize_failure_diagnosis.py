"""Summarize saved measured outcomes; no inference or prediction repair."""
import json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
labels={'finqa':'FinQA','tatqa':'TAT-QA','tathqa':'TAT-HQA','convfinqa':'ConvFinQA'}
lines=[r'\subsection{Revised evaluation and root-cause diagnosis}',
'Training diagnostics exposed a mismatch between the broad output schema and the executable contract. Kind-specific schemas improved structural guidance. Versions 4--5 restricted arithmetic to a single operation; this is a capacity-limited ablation, not a general reasoning model. The final v5 measurements are summarized below. All original and intermediate results remain in the archived artifacts.',
r'\begin{center}\small\setlength{\tabcolsep}{3pt}\begin{tabular}{llrrrr}',r'Dataset & Method & $N$ & Exec & Correct & Score\\\hline']
audit={}
for n,label in labels.items():
 base=ROOT/f'artifacts/revised_evaluation_v5/{n}_dev'
 rows=json.loads((base/'results.json').read_text());metrics=json.loads((base/'metrics.json').read_text())
 counter=collections.Counter()
 for row in rows:
  result=row['prediction']['execution'];error=result.get('error','')
  if result['status']=='ok':category='executed'
  elif result['status']=='abstain':category='abstained'
  elif 'ConversionSyntax' in error:category='nonnumeric_operand'
  elif 'Partial numeric' in error:category='partial_number'
  elif 'exact supplied id' in error:category='copied_placeholder_id'
  else:category='other_invalid'
  counter[category]+=1
 audit[n]=dict(counter)
 for v,short in [('ordinary','O'),('dependency','D'),('length_matched','L')]:
  m=metrics[v];metric=m['metrics'];score=metric['execution'] if 'execution' in metric else metric['f1']
  # Correct count comes from per-example official scores saved in metrics.
  correct=sum(bool(r.get('correct')) for r in m.get('per_example',[])) if isinstance(m.get('per_example'),list) else 0
  # All v5 exact-match / execution metrics are zero in these archived runs.
  assert metric.get('execution',metric.get('em'))==0
  lines.append(f'{label} & {short} & {m["denominator"]} & {m["counts"].get("ok",0)} & 0 & {100*score:.2f}'+r'\\')
lines += [r'\end{tabular}\end{center}',
'Score is official execution accuracy for FinQA/ConvFinQA and official F1 for TAT-QA/TAT-HQA, in percent. Exec counts local executions, including outputs without a supported official program export. Correct counts official execution matches or exact matches. Methods O/D/L denote ordinary, dependency and length-matched packing. These are development diagnostics: FinQA reuses an overlapping 40-question subset of the original full dev run; the other subsets exclude earlier frozen selections. ConvFinQA contains 141 turns in 40 complete conversations. Missing and failed outputs remain in the denominator.',
'MultiHiertt v5 produced no executable training plans and was not scaled to development evaluation. HybridQA remains blocked by missing linked evidence. Neither is assigned a fabricated development score.',
r'\paragraph{Why the scores collapse.} Across the 783 saved v5 outputs, the following counts are derived directly from execution status and error messages. These categories describe interpreter failures, not semantic accuracy.',
r'\begin{center}\small\setlength{\tabcolsep}{2pt}\begin{tabular}{lrrrr}',r'Dataset & Nonnum. & Partial & Placeholder & Exec\\\hline']
for n,label in labels.items():
 a=audit[n];lines.append(f'{label} & {a.get("nonnumeric_operand",0)} & {a.get("partial_number",0)} & {a.get("copied_placeholder_id",0)} & {a.get("executed",0)}'+r'\\')
lines += [r'\end{tabular}\end{center}',
'Nonnum. means the selected source substring could not be parsed as a number; Partial means only part of a numeric literal was selected; Placeholder means the model copied the instruction text ``exact supplied id'' instead of a supplied identifier. Additional failures include invalid spans, unknown evidence IDs, invalid table-row selections and abstentions. Some executable outputs calculate unrelated constants. Thus execution coverage alone does not demonstrate answer correctness. The one-operation restriction also prevents representing many growth, average and hypothetical calculations.',
r'\paragraph{Implemented recovery, pending live measurement.} A separate opt-in quote-grounded mode replaces long evidence IDs with local IDs and character offsets with exact source quotes. Quotes must occur exactly once in the selected fact; the code resolves their positions before the existing interpreter validates and executes them. Up to 16 operations and prior-step references are supported. Invented quotes, ambiguous matches and partial numeric operands are rejected. Existing modes and scores are preserved. A bounded recovery runner compares this mode with a direct-answer diagnostic on frozen development inputs. FinQA direct numeric checks remain auxiliary and are not official program scores. No new accuracy improvement is claimed: local inference was unreachable during this repair session.']
(ROOT/'report/generated/revised_results.tex').write_text('\n\n'.join(lines)+'\n')
(ROOT/'artifacts/grounded_recovery_v1/failure_counts.json').write_text(json.dumps(audit,indent=2)+'\n')
