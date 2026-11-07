"""Two independent dataset workers; each owns a locked ledger and sequential chains."""
import argparse, concurrent.futures, json, os, random, signal, subprocess, sys, time, fcntl
from pathlib import Path
from nrqa.experiment import ROOT, freeze, load_examples, write, run, evaluate
BASE=ROOT/'artifacts/bounded_submission'
NAMES=['tatqa','tathqa','multihiertt','convfinqa']

def prepare():
    BASE.mkdir(exist_ok=True)
    index={}
    digest=json.loads((ROOT/'artifacts/ollama_submission/finqa_full_dev/manifest.json').read_text())['identity']['digest']
    for name in NAMES:
        c=json.loads((ROOT/f'experiments/ollama/{name}_pilot.json').read_text())
        excluded=set()
        for p in (ROOT/'artifacts').rglob('results.json'):
            if BASE in p.parents: continue
            try:
                m=json.loads((p.parent/'manifest.json').read_text())
                if m.get('mode')=='live' and m.get('frozen',{}).get('config',{}).get('dataset')==name:
                    excluded.update(r['id'] for r in json.loads(p.read_text()))
            except (OSError,KeyError,TypeError): pass
        pilot=ROOT/f'experiments/ollama_frozen/{name}_pilot.json'
        if pilot.exists():excluded.update(json.loads(pilot.read_text())['ids'])
        c.update(seed=2626,selection='subset',sample_size=20,exclude_ids=sorted(excluded),max_generation_calls=300,expected_digest=digest)
        c.pop('ids',None)
        if name=='convfinqa':
            examples,_=load_examples(c);groups={}
            for e in examples: groups.setdefault(e.document['conversation_id'],[]).append(e.id)
            keys=sorted(k for k,v in groups.items() if not excluded.intersection(v));random.Random(2626).shuffle(keys)
            ids=[]
            for k in keys:
                ids.extend(groups[k])
                if len(ids)>=20:break
            c['ids']=ids
        cp=BASE/f'{name}.config.json';fp=BASE/f'{name}.frozen.json'
        if fp.exists():
            f=json.loads(fp.read_text())
        else:
            write(cp,c);f=freeze(cp,fp)
        index[name]={'frozen':str(fp),'questions':len(f['ids']),'prior_example_overlap':sorted(set(f['ids'])&excluded),'excluded_prior_ids':len(excluded),'seed':2626}
    write(BASE/'scope.json',{'runs':index,'hybridqa':'blocked: genuine linked evidence missing','selection':'seeded question IDs / intact conversations; no answer or performance filtering'})
    print(json.dumps(index,indent=2))

def finish():
    from aggregate_results import aggregate
    runs=[ROOT/'artifacts/ollama_submission/finqa_full_dev']
    for name in NAMES:
        p=BASE/name
        if (p/'manifest.json').exists():
            evaluate(BASE/f'{name}.frozen.json',p);runs.append(p)
    aggregate(runs,BASE/'aggregate')
    # Build a concise, measured report supplement, never pool dataset scores.
    lines=[r'\section{Measured checkpoint and bounded evaluation}',
      'FinQA development is the full 883-question split, with 2649 saved method rows. '
      'FinQA test is incomplete: 162 saved rows (54 per method), with one unresolved inflight request; it is excluded from comparison. '
      'Repeated identical requests share ledger entries: 2469 unique completed requests support 2649 development rows. '
      'HybridQA remains unevaluated because the genuine linked corpus is absent.',
      r'\begin{center}\small\begin{tabular}{llrrrrr}',
      r'Dataset & Method & $N$ & Valid & Abstain & Invalid & Missing\\\hline']
    details=[]
    for p in runs:
        m=json.loads((p/'metrics.json').read_text());label='FinQA full dev' if p.name=='finqa_full_dev' else p.name+' dev subset'
        for v,z in m.items():
            c=z.get('counts',{});safe=lambda x:str(x).replace('_',r'\_')
            lines.append(f"{safe(label)} & {safe(v)} & {z['denominator']} & {c.get('ok',0)} & {c.get('abstain',0)} & {c.get('invalid',0)} & {c.get('missing',0)}\\\\")
            details.append({'dataset':label,'method':v,'n':z['denominator'],'scores':z.get('metrics'),'counts':c})
    lines.append(r'\end{tabular}\end{center}')
    for d in details:
        scores=', '.join(f'{k}={v:.5f}' for k,v in d['scores'].items())
        lines.append((d['dataset']+' '+d['method']+': '+scores+'.').replace('_',r'\_'))
    summary=json.loads((BASE/'aggregate/summary.json').read_text())
    for c in summary['comparisons']:
        b=c['paired_bootstrap']
        lines.append(f"{c['dataset']}: dependency minus ordinary {c['metric']} = {b['difference']:.5f}; paired document/conversation bootstrap 95\\% interval [{b['ci95'][0]:.5f}, {b['ci95'][1]:.5f}], {b['clusters']} clusters, 1000 resamples, seed 2626.")
    lines.append('Intervals describe this selected development sample; small samples and rare successes make population improvement uncertain. Related datasets share sources and are not pooled as independent observations. FinQA dependency packing produced four executable predictions but only two officially correct executions; ordinary produced none. This does not establish reliable improvement. No tuning used evaluation answers.')
    scope=json.loads((BASE/'scope.json').read_text())
    for n,z in scope['runs'].items():
        lines.append(f"{n}: frozen {z['questions']} development turns/questions, seed 2626; {z['excluded_prior_ids']} previously used IDs excluded, {len(z['prior_example_overlap'])} selected overlaps. ConvFinQA selections retain complete conversations. {'Measured above.' if (BASE/n/'metrics.json').exists() else 'Inference pending; no score claimed.'}")
    rows=json.loads((runs[0]/'results.json').read_text())
    for r in [x for x in rows if x['prediction'].get('execution',{}).get('status')=='invalid'][:2]:
        err=r['prediction']['execution'].get('error','invalid plan');text=f"Failure example {r['id']} ({r['variant']}): {str(err)[:220]}."
        for a,b in [ ('\\',r'\textbackslash{}'),('_',r'\_'),('%',r'\%'),('&',r'\&'),('#',r'\#'),('$',r'\$')]:text=text.replace(a,b)
        lines.append(text)
    lines.append('Infrastructure failures, missing outputs and all non-executable answers receive zero in the official-scoring denominator. Full status counts, scorer hashes, paired comparisons and request metadata are preserved in the accompanying JSON artifacts.')
    write(BASE/'report_measurements.json',details)
    (ROOT/'report/generated/bounded_results.tex').write_text('\n'.join(lines)+'\n')

def worker(name):
    import nrqa.runner as runner
    def stop(signum,frame): runner.STOP_DISPATCH=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    result=run(BASE/f'{name}.frozen.json',BASE/name,'live')
    print(name,result['status'],flush=True)

def workflow(hours):
    lock=open(BASE/'workflow.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.environ.setdefault('NRQA_DISPATCH_DEADLINE',str(time.time()+hours*3600))
    def child(name):
        if time.time()>=float(os.environ['NRQA_DISPATCH_DEADLINE']):return
        return subprocess.run([sys.executable,__file__,'worker','--name',name]).returncode
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(child,NAMES))
    finally:
        finish()
        import shutil
        result=subprocess.run(['make','-C',str(ROOT/'report')]) if shutil.which('pdflatex') else None
        write(BASE/'pdf_status.json',{'compiled':result is not None and result.returncode==0,'path':'report/main.pdf','visual_inspection_required':True})
        subprocess.run([sys.executable,str(ROOT/'scripts/package_delivery.py'),'--out',str(BASE/'nrqa-source.tar.gz')],check=True)
        import tarfile
        with tarfile.open(BASE/'measurements.tar.gz','w:gz') as archive:
            for folder in [BASE, ROOT/'artifacts/ollama_submission/finqa_full_dev', ROOT/'artifacts/spark_acceptance_v3']:
                for path in folder.rglob('*'):
                    if path.is_file() and path.suffix in ('.json','.tex'):
                        archive.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
            archive.add(ROOT/'artifacts/overlap_dev_v3.json',arcname='artifacts/overlap_dev_v3.json')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','finish','workflow','worker']);p.add_argument('--name',choices=NAMES);p.add_argument('--dispatch-hours',type=float,default=3.5);a=p.parse_args()
    if a.action=='worker':worker(a.name)
    elif a.action=='workflow':workflow(a.dispatch_hours)
    else:globals()[a.action]()
