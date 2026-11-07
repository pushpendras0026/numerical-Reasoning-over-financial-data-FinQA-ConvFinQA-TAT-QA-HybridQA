import argparse
from pathlib import Path
from nrqa.preparation import prepare,spark
from nrqa.core import canonical
p=argparse.ArgumentParser();p.add_argument('configs',nargs='*');p.add_argument('--out',required=True);p.add_argument('--limit',type=int);p.add_argument('--spark',action='store_true');p.add_argument('--master',default='local[4]');a=p.parse_args()
if a.spark:
 (Path(a.out)/'spark-events').mkdir(parents=True,exist_ok=True);r=spark(a.out,a.master)
else:r=prepare(a.configs,a.out,a.limit)
print(canonical(r))
