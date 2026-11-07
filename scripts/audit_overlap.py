"""Input-only source, table, question+table and bounded near-duplicate audit."""
import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
import re
from nrqa.core import canonical
from nrqa.experiment import load_examples,write,digest
from nrqa.preparation import fingerprint

p=argparse.ArgumentParser();p.add_argument('configs',nargs='+');p.add_argument('--out',required=True);p.add_argument('--limit',type=int);p.add_argument('--max-near-pairs',type=int,default=100000);a=p.parse_args()
groups={kind:defaultdict(set) for kind in ('source','table','question_table','id','content')};documents={};counts={};hashes={}
for path in a.configs:
 config=json.loads(Path(path).read_text());examples,_=load_examples(config)
 if a.limit:examples=examples[:a.limit]
 label=config['dataset']+':'+config['split'];counts[label]=len(examples);hashes[str(path)]=digest(Path(path))
 for e in examples:
  grid=e.document.get('table',e.document.get('tables',e.document.get('tables_html',[])))
  tablehash=fingerprint(grid);docid=e.document['id'];key=label+':'+docid
  groups['source'][e.document.get('filename',docid)].add(label)
  groups['table'][tablehash].add(label);groups['question_table'][fingerprint([grid,e.question.strip().lower()])].add(label)
  groups['id'][e.id].add(label)
  text=' '.join(f.raw for f in e.facts);groups['content'][fingerprint(text)].add(label)
  if key not in documents:
   words=re.findall(r'\w+',text.lower());shingles={' '.join(words[i:i+5]) for i in range(max(0,len(words)-4))}
   documents[key]=(label,shingles)
# Deterministic MinHash buckets propose candidates, exact Jaccard verifies them.
buckets=defaultdict(list)
for key,(label,shingles) in documents.items():
 for seed in range(8):
  signature=min((fingerprint([seed,s]) for s in shingles),default='empty')
  buckets[seed,signature].append(key)
candidates=set();truncated=False
for bucket in buckets.values():
 for left,right in combinations(sorted(bucket),2):
  if documents[left][0]==documents[right][0]:continue
  if len(candidates)>=a.max_near_pairs:truncated=True;break
  candidates.add((left,right))
 if truncated:break
near=[]
for left,right in sorted(candidates):
 sa,sb=documents[left][1],documents[right][1];score=len(sa&sb)/max(1,len(sa|sb))
 if score>=.8:near.append({'left':left,'right':right,'jaccard_5gram':score})
overlap={}
for kind,index in groups.items():
 pairs=defaultdict(int)
 for members in index.values():
  for left,right in combinations(sorted(members),2):pairs[left+' / '+right]+=1
 overlap[kind]=dict(sorted(pairs.items()))
write(a.out,{'counts':counts,'limit_per_source':a.limit,'config_hashes':hashes,'exact_unique_key_overlap':overlap,
             'near_duplicates':near,'near_candidates_checked':len(candidates),'candidate_cap_reached':truncated,
             'near_method':'8 deterministic MinHash minima over word 5-grams; Jaccard >=0.8. Approximate candidate recall; not exhaustive.',
             'labels_used':False,'official_splits_changed':False})
print(canonical({'counts':counts,'near_candidates_checked':len(candidates),'candidate_cap_reached':truncated}))
