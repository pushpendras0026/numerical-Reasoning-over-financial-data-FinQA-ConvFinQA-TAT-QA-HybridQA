"""Build report tables and paired document/conversation bootstrap intervals."""
import argparse
import csv
import json
from pathlib import Path
import random
import statistics
from collections import defaultdict
from nrqa.core import canonical
from nrqa.experiment import write


def bootstrap(pairs,seed=2626,n=1000):
    if not pairs:return None
    groups=sorted(pairs);rng=random.Random(seed);values=[]
    for _ in range(n):
        sample=[x for _ in groups for x in pairs[rng.choice(groups)]]
        values.append(sum(sample)/len(sample))
    values.sort();return {'difference':sum(x for g in groups for x in pairs[g])/sum(map(len,pairs.values())),
       'ci95':[values[int(.025*n)],values[min(n-1,int(.975*n))]],'clusters':len(groups),'resamples':n,'seed':seed}


def aggregate(runs,out,allow_mock=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);table=[];comparisons=[]
    for folder in runs:
        folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
        if manifest['mode']!='live' and not allow_mock:raise ValueError('Mock/preparation artifacts cannot enter live report tables')
        frozen=manifest['frozen'];config=frozen['config'];scores=json.loads((folder/'metrics.json').read_text())
        rows=json.loads((folder/'results.json').read_text()) if (folder/'results.json').exists() else []
        groups={(row['id'],row['variant']):row.get('group',row['id']) for row in rows}
        # Missing examples retain document groups from the frozen inputs.
        from nrqa.experiment import selected
        examples,_=selected(frozen)
        fallback={e.id:e.document.get('conversation_id',e.document.get('filename',e.document['id'])) for e in examples}
        for variant,score in scores.items():
            tokens=[r['packing']['token_count'] for r in rows if r['variant']==variant]
            gaps=[r['packing'].get('matching_gap',0) for r in rows if r['variant']==variant]
            statuses=score.get('counts',{})
            entries=[r['prediction'] for r in rows if r['variant']==variant]
            latencies=[a['latency_seconds'] for e in entries for a in e.get('attempts',[]) if 'latency_seconds' in a]
            usage=[e.get('usage',{}) for e in entries]
            input_tokens=sum(u.get('promptTokenCount',u.get('input_tokens',0)) for u in usage)
            output_tokens=sum(u.get('candidatesTokenCount',u.get('output_tokens',0)) for u in usage)
            thinking_tokens=sum(u.get('thoughtsTokenCount',u.get('output_tokens_details',{}).get('reasoning_tokens',0)) for u in usage)
            def percentile(values,q):
                return sorted(values)[min(len(values)-1,int(q*len(values)))] if values else None
            table.append({'run':str(folder),'dataset':config['dataset'],'split':config['split'],'variant':variant,
                'answering':config.get('answering','program'),'ablation':config.get('ablation','none'),
                'mode':manifest['mode'],'provider_model':canonical(manifest.get('identity',{})),
                'n':score['denominator'],'metrics':canonical(score.get('metrics',{})),'statuses':canonical(statuses),
                'mean_evidence_tokens':statistics.mean(tokens) if tokens else None,
                'mean_matching_gap':statistics.mean(gaps) if gaps else None,
                'input_tokens_logical_requests':input_tokens,'output_tokens_logical_requests':output_tokens,
                'reasoning_tokens_subset_or_extra_provider_specific':thinking_tokens,
                'generation_attempt_latency_p50':percentile(latencies,.5),'generation_attempt_latency_p95':percentile(latencies,.95),
                'usage_scope':'logical rows may reuse cached requests; reasoning may be included in output; not a billing total',
                'run_total_generation_attempts':manifest.get('model_calls',0),'spend':'unmeasured; zero-spend policy only'})
        if 'ordinary' in scores and 'dependency' in scores and scores['ordinary'].get('per_example'):
            key='execution' if config['dataset'] in ('finqa','convfinqa') else 'f1'
            left={r['id']:r['score'].get(key,0) for r in scores['ordinary']['per_example']}
            pairs=defaultdict(list)
            for r in scores['dependency']['per_example']:
                pairs[fallback[r['id']]].append(r['score'].get(key,0)-left[r['id']])
            comparisons.append({'run':str(folder),'dataset':config['dataset'],'metric':key,'paired_bootstrap':bootstrap(pairs)})
    write(out/'summary.json',{'rows':table,'comparisons':comparisons,'cross_dataset_independence_assumed':False})
    if table:
        with (out/'results.csv').open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=table[0]);writer.writeheader();writer.writerows(table)
    # No numeric placeholders; measured table rows keep full status counts in CSV.
    def tex(s):return str(s).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
    lines=[r'\begin{tabular}{llll}',r'Dataset & Method & $N$ & Score \\',r'\hline']
    for row in table:lines.append(f"{tex(row['dataset'])} & {tex(row['variant'])} & {row['n']} & {tex(row['metrics'])} \\\\")
    if not table:lines.append(r'All datasets & All methods & -- & Pending \\')
    lines.append(r'\end{tabular}');(out/'results.tex').write_text('\n'.join(lines)+'\n')
    return table

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('runs',nargs='*');p.add_argument('--out',required=True);p.add_argument('--allow-mock',action='store_true');a=p.parse_args();aggregate(a.runs,a.out,a.allow_mock)
