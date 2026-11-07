"""Verify active contracts strictly; preserve and hash-check historical contracts."""
import argparse
import json
from pathlib import Path
import re
import shutil
from nrqa.experiment import ROOT,code_hashes,selected,cache_key,digest
from nrqa.core import canonical


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='artifacts/transport_diagnostics_v5/delivery_checks.json');parser.add_argument('--validation',default='artifacts/transport_diagnostics_v5/local_validation.json');args=parser.parse_args()
    report=(ROOT/'report/main.tex').read_text();bib=(ROOT/'report/references.bib').read_text()
    citations={key.strip() for group in re.findall(r'\\cite\w*\{([^}]+)\}',report) for key in group.split(',')}
    entries=set(re.findall(r'@\w+\{([^,]+),',bib));missing=sorted(citations-entries)
    if missing:raise SystemExit('Missing bibliography entries: '+','.join(missing))
    if (ROOT/'report/acl2023.sty').read_bytes()!=(ROOT.parent/'Current_implementation/Chiru-End-Sem/acl2023/acl2023.sty').read_bytes():raise SystemExit('Copied template style differs')
    manifest=ROOT/'experiments/contracts_v9.json'
    registry=json.loads(manifest.read_text()) if manifest.exists() else {'active':[],'historical':{}}
    historical=registry['historical'];current=code_hashes();frozen_checks={};preserved={}
    for filename,metadata in historical.items():
        path=ROOT/filename
        if not path.is_file() or digest(path)!=metadata['sha256']:raise SystemExit('Historical contract changed: '+filename)
        preserved[filename]='hash unchanged; superseded, not runnable under current code'
    paths=set((ROOT/'experiments/frozen').glob('*.json'))|set((ROOT/'experiments/frozen_v3').glob('*.json'))|set((ROOT/'experiments/frozen_v4').glob('*.json'))|set((ROOT/'experiments/frozen_v5').glob('*.json'))|set((ROOT/'experiments/frozen_v6').glob('*.json'))|set((ROOT/'experiments/frozen_v7').glob('*.json'))|set((ROOT/'experiments/frozen_v8').glob('*.json'))|set((ROOT/'experiments/frozen_v9').glob('*.json'))|set((ROOT/'experiments/frozen_v10').glob('*.json'))
    for filename in registry['active']:
        path=ROOT/filename
        if not path.is_file():raise SystemExit('Active contract missing: '+filename)
        paths.add(path)
    for path in sorted(paths):
        filename=str(path.relative_to(ROOT))
        if filename in historical:continue
        frozen=json.loads(path.read_text());payload=dict(frozen);contract=payload.pop('contract')
        if cache_key(payload)!=contract:raise SystemExit('Corrupt freeze: '+filename)
        if frozen['code_hashes']!=current:raise SystemExit('Stale active/unregistered freeze: '+filename)
        examples,_=selected(frozen);frozen_checks[filename]=len(examples)
    readiness={};audit=ROOT/args.validation
    if audit.exists():
        data=json.loads(audit.read_text())
        if manifest.exists() and data.get('validation_code_hashes')!=current:raise SystemExit('Local validation is stale; run scripts/validate_local.py first')
        for name,row in data['datasets'].items():
            readiness[name]={k:row[k] for k in ('status','examples','blocked_examples','required_evidence_reference_issues') if k in row}
    blocked=[name for name,row in readiness.items() if row['status']=='missing_external_data']
    result={'status':'offline_checks_passed_with_external_blockers' if blocked else 'offline_checks_passed',
            'citations':sorted(citations),'active_frozen_examples':frozen_checks,'historical_contracts_preserved':preserved,
            'data_readiness':readiness,'blocked_datasets':blocked,
            'latex_tools':{name:shutil.which(name) for name in ('pdflatex','bibtex','latexmk')},
            'report_status':'draft; no live model results; compilation pending','credentials_or_live_requests_used':False}
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(canonical(result)+'\n');print(canonical(result))

if __name__=='__main__':main()
