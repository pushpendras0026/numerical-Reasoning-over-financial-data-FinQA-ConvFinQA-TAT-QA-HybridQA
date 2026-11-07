"""Create an allowlisted source bundle; never traverse secret or raw data paths."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--out',default='artifacts/delivery/nrqa-source.tar.gz');a=p.parse_args();target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
files=[]
for folder in ('src','scripts','tests','docs','experiments','report'):
 for path in (ROOT/folder).rglob('*'):
  if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.aux','.log','.out','.bbl','.blg') and not path.is_symlink():files.append(path)
for filename in ('README.md','Agents.md','.gitignore','.env.example','requirements-local.txt','package.json'):files.append(ROOT/filename)
for path in (ROOT/'artifacts/implementation').glob('*'):
 if path.is_file() and path.suffix in ('.txt','.json','.log'):files.append(path)
# Defense in depth: only literal known secret values are loaded for a local scan,
# never printed, copied into a manifest, or put into the archive.
from nrqa.openai_provider import local_environment
secrets=[]
for name,value in local_environment(ROOT/'.env',{'GEMINI_API_KEY','OPENAI_API_KEY','OPEN_AI'}).items():
 if value:secrets.append(value.encode())
for path in files:
 data=path.read_bytes()
 if any(secret in data for secret in secrets):raise SystemExit('Credential match found in allowlisted file: '+str(path.relative_to(ROOT)))
manifest={'label':'Source delivery draft; live acceptance and report compilation pending',
          'files':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(files))},
          'excluded':['.env','api.txt','raw datasets','provider ledgers','historical artifacts','upstream repositories'],
          'external_datasets_required':True}
with tarfile.open(target,'w:gz') as archive:
 for path in sorted(set(files)):archive.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
target.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'archive':str(target),'files':len(manifest['files']),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
