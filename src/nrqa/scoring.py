"""Dataset output conversion and isolated official scoring. Never used for inference."""
import json
import os
from pathlib import Path
import subprocess
import sys
from .core import canonical
from .execute import number,NUMBER
from .evaluation import check_coverage

REPOS={'finqa':'FinQA','convfinqa':'ConvFinQA','tatqa':'TAT-QA','tathqa':'TAT-HQA','hybridqa':'HybridQA','multihiertt':'MultiHiertt'}


def convert_output(dataset,qid,result):
    ok=result.get('status')=='ok';answer=result.get('answer','') if ok else '';tokens=result.get('tokens') if ok else None
    if dataset in ('finqa','convfinqa'):
        if dataset=='convfinqa' and ok and not tokens and isinstance(answer,str):
            # A single-number turn is a valid official program; keep only the number.
            match=NUMBER.search(answer.replace('$',''))
            if match:tokens=[match.group().replace(',','').replace(' ','').strip(),'EOF']
        return {'id':qid,'predicted':tokens or ['EOF']}
    if dataset in ('tatqa','tathqa'):
        scale=result.get('scale','') if ok else ''
        if isinstance(answer,str) and ' | ' in answer:answer=[a.strip() for a in answer.split(' | ')]
        if scale=='percent_fraction':  # TAT labels hold percentage points; the plan holds a fraction.
            try:answer=str(number(str(answer))*100)
            except Exception:pass
            scale='percent'
        return {qid:[answer,scale]}
    if dataset=='hybridqa':return {'question_id':qid,'pred':str(answer) if not isinstance(answer,list) else ' '.join(answer)}
    if dataset=='multihiertt':
        program=tokens if tokens and tokens!=['EOF'] else []
        # Upstream program callback emits a JSON number. Mixed span/program
        # scoring passes it directly to math.isclose, which rejects numeric strings.
        numeric_answer=float(number(str(answer))) if program else answer
        return {'uid':qid,'predicted_ans':numeric_answer,'predicted_program':program}
    raise ValueError('Unknown dataset')


def official_score(dataset,examples,references,results,out,repositories,answering="program"):
    """Full denominator, invalid outputs forced to zero; unchanged raw score also saved."""
    expected=[e.id for e in examples]
    check_coverage([{'id':k} for k in results],expected)
    if not expected:raise ValueError('Cannot score empty split')
    required={'program','exe_ans'} if dataset in ('finqa','convfinqa') else {'answer'}
    if len(references)!=len(examples):raise ValueError('Reference count mismatch')
    hidden=any(not required<=set(r.labels) or r.labels.get('answer',True) is None for r in references)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records=[];outputs=[];hybrid_groups={}
    if dataset=='hybridqa':
        for e in examples[:1]:
            if e.facts:
                reference_path=Path(e.facts[0].source['file']).parent/'dev_reference.json'
                if reference_path.exists() and e.split=='dev':
                    group_data=json.loads(reference_path.read_text())
                    for group in ('table','passage'):
                        for qid in group_data[group]:hybrid_groups[qid]=group
    for e,r in zip(examples,references):
        if e.id!=r.id:raise ValueError('Reference alignment mismatch')
        records.append({'id':e.id,'reference':r.labels,'table':e.document.get('table',[]),'result':results[e.id],'subgroup':hybrid_groups.get(e.id)})
        outputs.append(convert_output(dataset,e.id,results[e.id]))
    if dataset in ('tatqa','tathqa'):outputs={k:v for row in outputs for k,v in row.items()}
    (out/'official_predictions.json').write_text(canonical(outputs)+'\n')
    if hidden:
        summary={'status':'hidden_labels','denominator':len(expected),'submission_exported':True}
        (out/'metrics.json').write_text(canonical(summary)+'\n')
        return summary
    payload={'dataset':dataset,'repo':str(Path(repositories).resolve()/REPOS[dataset]),'records':records,'answering':answering}
    (out/'scoring_inputs.json').write_text(canonical(payload)+'\n')
    proc=subprocess.run([sys.executable,'-m','nrqa.official_worker',str(out/'scoring_inputs.json'),str(out/'metrics.json')],
                        capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    (out/'evaluator.log').write_text(proc.stdout+proc.stderr)
    if proc.returncode:raise RuntimeError('Official scoring failed; inspect '+str(out/'evaluator.log'))
    return json.loads((out/'metrics.json').read_text())
