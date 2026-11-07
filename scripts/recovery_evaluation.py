"""Bounded recovery comparison. Run from ordinary WSL with reachable local Ollama."""
import argparse,concurrent.futures,json,os,time,subprocess
from pathlib import Path
from nrqa.experiment import ROOT,write,freeze,run,evaluate

BASE=ROOT/'artifacts/grounded_recovery_v1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--datasets',nargs='+',default=['finqa','tatqa','multihiertt']);p.add_argument('--sample-size',type=int,default=10);p.add_argument('--minutes',type=int,default=40);args=p.parse_args()
 os.environ.setdefault('OLLAMA_BASE_URL','http://172.25.80.1:11434');os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b-instruct')
 os.environ['NRQA_DISPATCH_DEADLINE']=str(time.time()+args.minutes*60)
 jobs=[]
 for n in args.datasets:
  c=json.loads((ROOT/f'artifacts/revised_evaluation_v5/{n}.dev.config.json').read_text())
  # Exclude all prior selected dev IDs where available, including blocked selections.
  used=set(c.get('exclude_ids',[]))
  for fp in (ROOT/'artifacts').glob('revised_evaluation_v*/*.dev.frozen.json'):
   f=json.loads(fp.read_text())
   if f['config']['dataset']==n:used.update(f['ids'])
  c.update(sample_size=args.sample_size,max_generation_calls=300,generation_attempts=1)
  c['exclude_ids']=sorted(used) if n!='finqa' else []
  c['selection_note']='Recovery development comparison; FinQA overlaps original full dev; others exclude prior frozen selections. Not held-out test results.'
  for mode in ['direct','grounded']:
   config=dict(c,answering=mode,variants=['ordinary'] if mode=='direct' else ['ordinary','dependency'])
   cp=BASE/f'{n}.{mode}.config.json';fp=BASE/f'{n}.{mode}.frozen.json'
   write(cp,config);freeze(cp,fp);jobs.append((n,mode,fp))
 def execute(job):
  n,mode,fp=job;out=BASE/f'{n}_{mode}'
  m=run(fp,out,'live');print(n,mode,m['status'],m.get('error',''),flush=True)
  if (out/'results.json').exists():
   scores=evaluate(fp,out);print(n,mode,json.dumps(scores),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(execute,jobs))
 # Add measured recovery results only after scoring; retain missing outputs in denominator.
 lines=[r'\subsection{Measured recovery development diagnostics}',
 'Separate recovery run; direct FinQA numeric accuracy is auxiliary, grounded FinQA accuracy uses the official program executor. Development samples are small and FinQA overlaps original dev. All selected questions, including missing outputs, remain in the denominator.',
 r'\begin{center}\small\begin{tabular}{lllrr}',r'Dataset & Mode & Method & $N$ & Score\\\hline']
 measured=False
 for n,mode,fp in jobs:
  path=BASE/f'{n}_{mode}/metrics.json'
  if not path.exists():continue
  for variant,entry in json.loads(path.read_text()).items():
   metrics=entry['metrics'];key=next((k for k in ('direct_numeric_auxiliary','execution','f1') if k in metrics),None)
   if key is None:continue
   measured=True
   lines.append(f"{n} & {mode} & {variant[0].upper()} & {entry['denominator']} & {100*metrics[key]:.2f}"+r'\\')
 lines.append(r'\end{tabular}\end{center}')
 if measured:
  (ROOT/'report/generated/grounded_recovery.tex').write_text('\n'.join(lines)+'\n')
  subprocess.run(['make','-C',str(ROOT/'report')],check=True)
if __name__=='__main__':main()
