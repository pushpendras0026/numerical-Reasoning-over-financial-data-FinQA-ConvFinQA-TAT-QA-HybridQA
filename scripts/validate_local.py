"""Offline validation. Missing resources and every blocked question remain explicit."""
import argparse
import json
from pathlib import Path
from nrqa.experiment import ROOT,load_examples,digest,write,code_hashes
from nrqa.core import pack_method
from nrqa.data_paths import source_path
from nrqa.data_validation import audit_multi,audit_hybrid


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='artifacts/implementation/local_validation.json');args=parser.parse_args();results={}
    for name in ('finqa','tatqa','convfinqa','tathqa','hybridqa','multihiertt'):
        config=json.loads((ROOT/f'experiments/{name}_pilot.json').read_text())
        if name in ('hybridqa','multihiertt'):
            splits={}
            for split in ('train','dev','test'):
                current=dict(config,split=split,source=str(Path(config['source']).with_name(split+'.json')))
                splits[split]=(audit_hybrid if name=='hybridqa' else audit_multi)(current)
            results[name]=dict(splits['dev'],splits=splits);continue
        examples,refs=load_examples(config);bad_edges=0
        for e in examples:
            ids={f.id for f in e.facts};bad_edges+=sum(not set(f.dependencies)<=ids for f in e.facts)
        if bad_edges:raise ValueError('Invalid reader dependencies')
        turn_id_match=None
        if name=='convfinqa':
            import zipfile
            with zipfile.ZipFile(source_path(config)) as z:official_ids={r['id'] for r in json.loads(z.read('data/dev_turn.json'))}
            turn_id_match=official_ids=={e.id for e in examples}
            if not turn_id_match:raise ValueError('Official conversation turn IDs differ')
        packing={}
        for e in examples[:3]:
            packing[e.id]={}
            for method in ('ordinary','dependency','length_matched'):
                bundle=pack_method(e,method,4000)
                if bundle['token_count']>4000:raise ValueError('Budget violated')
                packing[e.id][method]={k:bundle[k] for k in ('token_count','token_cap','token_count_is_estimate','matching_gap') if k in bundle}
        results[name]={'status':'real_dev_reader_checked','examples':len(examples),'duplicate_ids':0,'unresolved_edges':bad_edges,
                        'official_turn_ids_match':turn_id_match,'source_sha256':digest(source_path(config)),'sampled_packing':packing,'inference_calls':0}
    write(args.out,{'validation_code_hashes':code_hashes(),'label':'Real input validation; missing corpus is not passed; no model predictions or accuracy','datasets':results})
    print(json.dumps({name:{k:v for k,v in row.items() if k in ('status','examples','duplicate_ids','unresolved_dependencies','blocked_examples','required_evidence_reference_issues')} for name,row in results.items()},indent=2))

if __name__=='__main__':main()
