"""Real-file input and annotation audits, kept outside inference preparation."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import copy
import hashlib
import json
import re
from .core import canonical,pack_method
from .datasets import multi,hybrid
from .data_paths import source_path,corpus_path,corpus_candidates


def file_hash(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def check_example(example):
    facts={f.id:f for f in example.facts}
    if len(facts)!=len(example.facts):raise ValueError(f'Duplicate facts: {example.id}')
    ids=set(facts)
    for fact in example.facts:
        if not set(fact.dependencies)<=ids:raise ValueError(f'Unresolved dependency: {example.id}/{fact.id}')
    done=set()
    def visit(fid,active):
        if fid in active:raise ValueError(f'Dependency cycle: {example.id}/{fid}')
        if fid in done:return
        for dep in facts[fid].dependencies:visit(dep,active|{fid})
        done.add(fid)
    for fid in facts:visit(fid,set())
    return sum(len(f.dependencies) for f in example.facts)


def audit_multi(config):
    path=source_path(config);rows=json.loads(path.read_text());seen=set();stats=Counter();issues=[];leak_checks=[];packing={};kinds=set()
    for index,row in enumerate(rows):
        if row['uid'] in seen:raise ValueError(f'Duplicate MultiHiertt ID: {row["uid"]}')
        seen.add(row['uid']);ex,ref=multi(row,config['split'],str(path),index)
        stats['dependency_edges']+=check_example(ex);stats['facts']+=len(ex.facts);stats['tables']+=len(ex.document['geometry'])
        for table in ex.document['geometry']:
            stats['cells']+=len(table)
            stats['merged_cells']+=sum(c['rowspan']>1 or c['colspan']>1 for c in table)
            stats['explicit_th_cells']+=sum(c['tag']=='th' for c in table)
        stats['table_text_links']+=len(ex.document['table_text_links'])
        stats['alias_coordinates']+=sum(k!=v for k,v in ex.document['cell_aliases'].items())
        facts={f.id:f for f in ex.facts};prefix=f'multihiertt:{config["split"]}:{row["uid"]}:cell:'
        for field,values in (('table_description',row['table_description']),('table_evidence',ref.labels.get('table_evidence',[]))):
            if not isinstance(values,(dict,list)):raise ValueError(f'Invalid {field}: {row["uid"]}')
            for cid in values:
                stats[field+'_references']+=1
                target=ex.document['cell_aliases'].get(cid)
                if target is None or prefix+target not in facts:
                    issues.append({'id':row['uid'],'field':field,'target':cid});stats[field+'_unresolved']+=1
                elif target!=cid:stats[field+'_merged_alias_references']+=1
        for pid in ref.labels.get('text_evidence',[]):
            stats['text_evidence_references']+=1
            if type(pid)is not int or not 0<=pid<len(row['paragraphs']):
                issues.append({'id':row['uid'],'field':'text_evidence','target':pid});stats['text_evidence_unresolved']+=1
        category=ref.labels.get('question_type','hidden')
        if category not in kinds:
            kinds.add(category);changed=dict(row,qa={'question':row['qa']['question'],'answer':'__GOLD_SENTINEL__','program':'__GOLD_SENTINEL__','table_evidence':['__GOLD_SENTINEL__'],'text_evidence':['__GOLD_SENTINEL__']},table_description='__GOLD_SENTINEL__',model_input='__GOLD_SENTINEL__')
            altered=multi(changed,config['split'],str(path),index)[0]
            if canonical(asdict(ex))!=canonical(asdict(altered)):raise ValueError('Reference leakage: '+ex.id)
            leak_checks.append({'id':ex.id,'category':category,'unchanged_after_reference_mutation':True})
        if index==0:
            for method in ('ordinary','dependency','length_matched'):
                bundle=pack_method(ex,method,4000)
                if bundle['token_count']>4000:raise ValueError('Packing budget violated')
                packing[method]={k:bundle[k] for k in ('token_count','token_cap','matching_gap') if k in bundle}
    required_issues=[x for x in issues if x['field']!='table_description']
    return {'status':'real_split_reader_checked' if not issues else 'real_split_checked_with_annotation_issues',
            'source':str(path),'source_sha256':file_hash(path),'examples':len(rows),'duplicate_ids':0,'unresolved_dependencies':0,'dependency_cycles':0,
            'counts':dict(stats),'annotation_issues':issues,'required_evidence_reference_issues':len(required_issues),
            'leakage_checks':leak_checks,'sampled_packing':packing,'labels_available':all('answer' in r['qa'] for r in rows),
            'question_types':dict(Counter(r['qa'].get('question_type','hidden') for r in rows)),
            'inference_inputs_validated':len(rows),'inference_calls':0}


def audit_hybrid(config):
    path=source_path(config);rows=json.loads(path.read_text());ids=[r['question_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate HybridQA question IDs')
    root=corpus_path(config);by_table={};indices={r['question_id']:i for i,r in enumerate(rows)}
    for row in rows:by_table.setdefault(row['table_id'],[]).append(row)
    missing=[];broken=[];blocked=set();resolved=0;links=0
    for tid,questions in sorted(by_table.items()):
        absent=[]
        for folder in ('tables_tok','request_tok'):
            target=root/folder/f'{tid}.json'
            if not target.is_file():absent.append(str(target))
        if absent:
            missing.append({'table_id':tid,'files':absent,'question_ids':[q['question_id'] for q in questions]});blocked.update(q['question_id'] for q in questions);continue
        table=json.loads((root/'tables_tok'/f'{tid}.json').read_text());passages=json.loads((root/'request_tok'/f'{tid}.json').read_text())
        targets={link for row in [table['header']]+table['data'] for cell in row for link in cell[1]}
        unresolved=[link for link in targets if link not in passages or not isinstance(passages[link],str) or not passages[link].strip()]
        if unresolved:
            broken.append({'table_id':tid,'links':sorted(unresolved),'question_ids':[q['question_id'] for q in questions]});blocked.update(q['question_id'] for q in questions);continue
        for q in questions:
            ex,_=hybrid(q,config['split'],str(path),indices[q['question_id']],root);check_example(ex);resolved+=1
        links+=len(targets)
    reference_check=None
    reference=path.parent/'dev_reference.json'
    if config['split']=='dev' and reference.exists():
        gold=json.loads(reference.read_text())['reference']
        reference_check={'ids_match':set(gold)==set(ids),'answer_mismatches':sum(gold.get(r['question_id'])!=r.get('answer-text') for r in rows)}
        if not reference_check['ids_match'] or reference_check['answer_mismatches']:raise ValueError('HybridQA dev reference release mismatch')
    return {'status':'missing_external_data' if missing or broken else 'real_split_reader_checked','source':str(path),'source_sha256':file_hash(path),
            'questions':len(rows),'examples':len(rows),'unique_tables':len(by_table),'duplicate_ids':0,'validated_prediction_inputs':resolved,
            'blocked_examples':len(blocked),'blocked_question_ids':sorted(blocked),'missing_resources':missing,'broken_passage_links':broken,
            'resolved_unique_passage_links':links,'passage_resolution_complete':not bool(blocked),
            'corpus_locations_checked':[str(p) for p in corpus_candidates(config)],'reference_check':reference_check,'labels_available':all('answer-text' in r for r in rows)}
