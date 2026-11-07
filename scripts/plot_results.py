"""Generate an exportable figure only from measured aggregate rows."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('summary');p.add_argument('--out',required=True);a=p.parse_args()
summary=json.loads(Path(a.summary).read_text());rows=summary['rows']
if any(r['mode']!='live' for r in rows):raise SystemExit('Refuse mock rows in measured figure')
if not rows:raise SystemExit('No measured results; figure remains pending')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
labels=[];values=[]
for r in rows:
 metric='execution' if r['dataset'] in ('finqa','convfinqa') else 'f1';scores=json.loads(r['metrics'])
 if metric in scores:labels.append(r['dataset']+' / '+r['variant']);values.append(scores[metric])
fig,ax=plt.subplots(figsize=(9,4));ax.bar(labels,values);ax.set_ylim(0,1);ax.set_ylabel('Official score (full denominator)');ax.tick_params(axis='x',rotation=70);fig.tight_layout();fig.savefig(a.out)
