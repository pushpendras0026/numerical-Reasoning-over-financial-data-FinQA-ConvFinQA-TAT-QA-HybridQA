"""Measure a command and its live process tree. Requires psutil, no network."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import psutil
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
cmd=a.command[1:] if a.command[:1]==['--'] else a.command
start=time.monotonic();proc=subprocess.Popen(cmd);peak=0;peak_processes=0
while proc.poll() is None:
 try:
  root=psutil.Process(proc.pid);tree=[root]+root.children(recursive=True);rss=0
  for child in tree:
   try:rss+=child.memory_info().rss
   except psutil.Error:pass
  peak=max(peak,rss);peak_processes=max(peak_processes,len(tree))
 except psutil.Error:pass
 time.sleep(.1)
result={'command':cmd,'exit_code':proc.returncode,'wall_seconds':time.monotonic()-start,
        'sampled_peak_tree_rss_bytes':peak,'sample_interval_seconds':.1,'peak_process_count':peak_processes,
        'limitation':'Sum RSS can double-count shared pages; short peaks between samples may be missed.'}
Path(a.out).write_text(json.dumps(result,indent=2)+'\n');raise SystemExit(proc.returncode)
