"""One subprocess per evaluator: isolates upstream module names and sys.path changes."""
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from .core import canonical
from .scoring import convert_output


def load(path,definitions_only=False):
    if definitions_only:
        tree=ast.parse(path.read_text());tree.body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))]
        namespace={'__name__':'official_functions','__file__':str(path)}
        exec(compile(tree,str(path),'exec'),namespace) # trusted local evaluator source only
        from types import SimpleNamespace
        return SimpleNamespace(**namespace)
    spec=importlib.util.spec_from_file_location('official',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def first_number(text):
    from .execute import number,NUMBER
    try:return float(number(str(text)))
    except Exception:pass
    match=NUMBER.search(str(text).replace('$',''))
    negative=str(text).strip().startswith(('-','('))
    if not match:return None
    value=float(number(match.group()))
    return -abs(value) if negative else value


def relaxed_numeric(answer,gold):
    """Auxiliary, NOT official: same rule for executor and direct answers.

    Accepts 1% relative error (rounded free-text answers) and the fraction/percent
    forms of one value. Official execution accuracy stays the primary metric.
    """
    if isinstance(gold,str):return float(str(answer).strip().lower().rstrip('.')==gold.strip().lower())
    value=first_number(answer)
    if value is None:return 0.
    return float(any(math.isclose(c,gold,rel_tol=.01,abs_tol=1e-9) for c in (value,value/100,value*100)))


def main(payload):
    d=payload['dataset'];repo=Path(payload['repo']);sys.path.insert(0,str(repo))
    path=repo/({'finqa':'code/evaluate/evaluate.py','convfinqa':'code/utils/general_utils.py',
               'tatqa':'tatqa_metric.py','tathqa':'evaluate.py','hybridqa':'evaluate_script.py','multihiertt':'evaluate.py'}[d])
    scorer=load(path,d=='hybridqa');details=[]
    for row in payload['records']:
        qid=row['id'];ref=row['reference'];result=row['result'];pred=convert_output(d,qid,result)
        invalid=result.get('status')!='ok';raw={};error=None
        if d in ('finqa','convfinqa'):
            program=scorer.program_tokenization(ref['program'])
            # FinQA tokenizer already adds EOF. Both repositories do so.
            flag,value=scorer.eval_program(pred['predicted'],row['table'])
            raw={'execution':float(not flag and value==ref['exe_ans']),
                 'program':float(not flag and scorer.equal_program(program,pred['predicted']))}
            raw['relaxed_numeric']=relaxed_numeric(result.get('answer',''),ref['exe_ans'])
            if payload.get('answering')=='direct' or result.get('answering')=='direct_no_executor':
                raw={'relaxed_numeric':raw['relaxed_numeric']}  # No program exists to score officially.
        elif d in ('tatqa','tathqa'):
            metric=scorer.TaTQAEmAndF1();a,scale=pred[qid]
            metric(ground_truth=ref,prediction=a,pred_scale=scale)
            values=metric.get_overall_metric();raw={'em':values[0],'f1':values[1],'scale':values[2]}
        elif d=='hybridqa':raw={'em':scorer.compute_exact(ref['answer'],pred['pred']), 'f1':scorer.compute_f1(ref['answer'],pred['pred'])}
        else:
            goldprog=ref.get('program');pp=pred['predicted_program'];ans=pred['predicted_ans'];gold=ref['answer']
            try:
                if pp and goldprog:em,f1=scorer.evaluate_program_result(pp,goldprog)
                elif not pp and not goldprog:em,f1=scorer.get_span_selection_metrics(str(ans),str(gold))
                elif not pp:em,f1=scorer.evaluate_span_program_result(str(ans),gold)
                else:em,f1=scorer.evaluate_span_program_result(str(gold),ans)
                raw={'em':em,'f1':f1}
            except (ValueError,TypeError,ZeroDivisionError,IndexError) as exc:
                error=type(exc).__name__;raw={'em':0.,'f1':0.}
        details.append({'id':qid,'subgroup':row.get('subgroup'),'status':result.get('status','missing'),'official_raw':raw,
                        # A valid answer with no official program still has a comparable value.
                        'score':{k:v if k=='relaxed_numeric' and result.get('status')=='unsupported_export' else 0. if invalid else v
                                 for k,v in raw.items()},'official_error':error})
    n=len(details);keys=details[0]['score'].keys()
    subgroups={}
    for group in ('table','passage'):
        members=[x for x in details if x['subgroup']==group]
        if members:subgroups[group]={'n':len(members),'metrics':{k:sum(x['score'][k] for x in members)/len(members) for k in keys}}
    return {'subgroups':subgroups,'status':'scored','denominator':n,'metrics':{k:sum(x['score'][k] for x in details)/n for k in keys},
            'official_raw_metrics':{k:sum(x['official_raw'][k] for x in details)/n for k in keys},
            'rule':'All expected examples; invalid/abstained/missing/API failure forced to zero. Raw official-function scores retained.',
            'per_example':details,'scorer_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'evaluator_dependencies':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in repo.rglob('*.py') if '__pycache__' not in str(p)}}

if __name__=='__main__':
    result=main(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(canonical(result)+'\n')
