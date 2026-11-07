"""Real-data submission/scorer contracts, never model predictions or QA accuracy."""
import json
import re
from pathlib import Path
from nrqa.core import PredictionExample,ReferenceRecord
from nrqa.datasets import multi
from nrqa.data_paths import source_path
from nrqa.experiment import ROOT,write
from nrqa.scoring import official_score


def main():
    out=ROOT/'artifacts/data_integration_v3/scoring_contracts';summary={}
    config=json.loads((ROOT/'experiments/multihiertt_pilot.json').read_text())
    for split in ('train','dev','test'):
        current=dict(config,source=str(Path(config['source']).with_name(split+'.json')),split=split)
        path=source_path(current);rows=json.loads(path.read_text())
        examples=[PredictionExample('multihiertt','real-release',split,r['uid'],r['qa']['question'],{},()) for r in rows]
        refs=[ReferenceRecord(r['uid'],{k:v for k,v in r['qa'].items() if k!='question'}) for r in rows]
        results={e.id:{'status':'abstain'} for e in examples}
        scores=official_score('multihiertt',examples,refs,results,out/split/'all_abstentions',ROOT.parent)
        record={'examples':len(rows),'status':scores['status'],'all_expected_ids_exported':True,'label':'Abstention/export contract only; NOT model accuracy'}
        if split!='test':
            chosen=[];kinds=set()
            for i,row in enumerate(rows):
                kind=row['qa']['question_type']
                if kind not in kinds:kinds.add(kind);chosen.append((i,row))
            es=[];rs=[];predictions={}
            for i,row in chosen:
                e,r=multi(row,split,str(path),i);es.append(e);rs.append(r)
                program=row['qa']['program']
                tokens=re.findall(r'[^\s(),]+\(|[^\s(),]+|\)',program)+['EOF'] if program else None
                predictions[e.id]={'status':'ok','answer':str(row['qa']['answer']),'tokens':tokens}
            echo=official_score('multihiertt',es,rs,predictions,out/split/'reference_echo',ROOT.parent)
            if echo['metrics']['em']!=1 or echo['metrics']['f1']!=1:raise ValueError('Reference/output round-trip failed')
            record['reference_echo_contracts']=len(chosen);record['echo_types']=sorted(kinds)
        summary[split]=record
    write(out/'summary.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
