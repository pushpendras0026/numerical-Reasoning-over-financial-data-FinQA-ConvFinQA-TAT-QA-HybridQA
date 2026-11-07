"""Resumable local-only experiment orchestration. Never imports cloud credentials."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from nrqa.experiment import ROOT, freeze, run, evaluate, write, selected
from nrqa.ollama_provider import Ollama, SETTINGS
from nrqa.providers import ProviderError
from nrqa.openai_provider import local_environment
from nrqa.model import request
from nrqa.core import pack_method

BASE = ROOT/'artifacts/ollama_submission'
FROZEN = ROOT/'experiments/ollama_frozen'

def prepare():
    env = local_environment(ROOT/'.env', {'OLLAMA_MODEL','OLLAMA_BASE_URL'})
    configs = ROOT/'experiments/ollama'; configs.mkdir(exist_ok=True)
    readiness=json.loads((BASE/'data_validation.json').read_text())['datasets']
    names=['smoke','finqa_pilot','convfinqa_pilot','tatqa_pilot','tathqa_pilot','multihiertt_pilot',
           'finqa_full_dev','finqa_full_test','convfinqa_full_dev','convfinqa_full_test',
           'tatqa_full_dev','tatqa_full_test','tathqa_full_dev','tathqa_full_test',
           'multihiertt_full_dev','multihiertt_full_test']
    index={}; blocked={}
    for name in names:
        source=ROOT/'experiments'/f'{name}.json'
        if not source.exists():continue
        c=json.loads(source.read_text()); status=readiness.get(c['dataset'],{})
        if status.get('blocked_examples',0) or status.get('required_evidence_reference_issues',0) or status.get('status')=='missing_external_data':
            blocked[name]=status;continue
        c.update(provider='ollama',model=env.get('OLLAMA_MODEL','qwen2.5:7b-instruct'),evidence_cap=3000,
                 generation_attempts=1,response_timeout_seconds=180)
        cp=configs/f'{name}.json';write(cp,c)
        fp=FROZEN/f'{name}.json';f=freeze(cp,fp)
        index[name]={'frozen':str(fp),'questions':len(f['ids']),'predictions':len(f['ids'])*len(c['variants'])}
    blocked['hybridqa']='Linked evidence corpus absent; never substitute gold evidence.'
    write(BASE/'index.json',{'runs':index,'blocked':blocked})

def diagnostic():
    from functools import partial
    from nrqa.providers import transport
    p=Ollama(local_environment(ROOT/'.env',{'OLLAMA_BASE_URL','OLLAMA_MODEL'}),http=partial(transport,timeout=180))
    p.verify_free()
    f=json.loads((FROZEN/'smoke.json').read_text());e=selected(f)[0][0]
    counter=type('ByteBound',(),{'name':p.counter_name,'estimated':True,'count':staticmethod(p.count)})()
    bundle=pack_method(e,'ordinary',3000,counter)
    req=request(e.question,bundle,dict(p.identity),SETTINGS)
    from nrqa.runner import Ledger, StopRun
    ledger=Ledger(BASE/'diagnostic.sqlite',p,max_calls=1,generation_attempts=1)
    try:
        prediction=ledger.predict(req,bundle)
        if prediction['status']!='completed':raise StopRun(prediction.get('error','diagnostic_failed'))
        raw=prediction['raw_response'];p.response_text(raw)
    finally:ledger.close()
    write(BASE/'diagnostic.json',{'label':'engineering diagnostic; excluded from scored comparisons',
          'identity':p.identity,'request':req,'raw':raw})

def execute(name):
    idx=json.loads((BASE/'index.json').read_text())['runs']
    if name not in idx:raise SystemExit('Blocked or unavailable dataset: '+name)
    fp=idx[name]['frozen'];out=BASE/name
    result=run(fp,out,'live')
    if result['status']!='completed':raise SystemExit('Infrastructure/checkpoint stop: '+str(result))
    evaluate(fp,out)

def finish():
    from aggregate_results import aggregate
    folders=[p.parent for p in BASE.glob('*/metrics.json')]
    aggregate(folders,BASE/'aggregate')
    durations=[];tokens=0;ns=0
    for folder in folders:
        for row in json.loads((folder/'results.json').read_text()):
            pred=row['prediction'];u=pred.get('usage_details',{})
            if u.get('eval_duration'):tokens+=pred.get('usage',{}).get('output_tokens',0);ns+=u['eval_duration']
            durations.extend(a['latency_seconds'] for a in pred.get('attempts',[]) if 'latency_seconds' in a)
    idx=json.loads((BASE/'index.json').read_text())['runs']
    mean=sum(durations)/len(durations) if durations else None
    write(BASE/'runtime.json',{'measured_attempts':len(durations),'mean_attempt_seconds':mean,
        'generation_tokens_per_second':tokens/(ns/1e9) if ns else None,
        'full_split_estimates_seconds':{n:v['predictions']*mean if mean else None for n,v in idx.items() if 'full_' in n},
        'caveat':'Extrapolation from completed subset; lengths and conversational history vary.'})
    import shutil
    shutil.copyfile(BASE/'aggregate/results.tex', ROOT/'report/generated/ollama_results.tex')
    write(BASE/'delivery_status.json',{'scored_runs':[p.name for p in folders], 'full_benchmark_claim':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','diagnostic','run','finish']);p.add_argument('name',nargs='?');a=p.parse_args()
    try:
        if a.action=='run':execute(a.name)
        else:globals()[a.action]()
    except ProviderError as e:
        write(BASE/'infrastructure_failure.json',{'error':e.code,'details':e.details});raise SystemExit(e.code)
