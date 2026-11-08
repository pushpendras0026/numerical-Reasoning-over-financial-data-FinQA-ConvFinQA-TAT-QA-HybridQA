"""Configuration-driven preparation, frozen selection, sequential inference and scoring."""
import argparse
from functools import partial
from collections import Counter
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
import random
import sys
import time
from .core import canonical,pack_method,EvidenceFact,VisibleTokens
from .datasets import read,VERSIONS
from .data_paths import source_path,corpus_path
from .model import request,cache_key,INSTRUCTIONS,SCHEMA,SETTINGS
from . import grounded
from .runner import Ledger,StopRun
from .providers import Gemini,ProviderError,transport
from .openai_provider import OpenAI,local_environment,SETTINGS as OPENAI_SETTINGS
from .ollama_provider import Ollama, SETTINGS as OLLAMA_SETTINGS
from .scoring import official_score,convert_output

ROOT=Path(__file__).resolve().parents[2]


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(canonical(value)+'\n');temp.replace(path)


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_hashes():
    return {str(p.relative_to(ROOT)):digest(p) for root in ('src',) for p in sorted((ROOT/root).rglob('*.py'))}


def load_examples(config):
    examples=[];references=[]
    path=source_path(config);corpus=corpus_path(config) if config['dataset']=='hybridqa' else None
    for e,r in read(config['dataset'],path,config['split'],corpus,config.get('member')):
        examples.append(e);references.append(r)
    ids=[e.id for e in examples]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate dataset IDs')
    return examples,references


def freeze(config_path,out):
    config=json.loads(Path(config_path).read_text())
    if config.get('spending_ceiling_usd')!=0:raise ValueError('Only zero-spend policy supported')
    if config.get('provider') not in ('gemini','openai','ollama'):raise ValueError('Unsupported provider')
    if not isinstance(config.get('model'),str) or not config['model']:raise ValueError('Explicit frozen model required')
    if type(config.get('seed')) is not int:raise ValueError('Integer seed required')
    if config.get('selection') not in ('subset','full'):raise ValueError('Explicit subset/full selection required')
    if config.get('selection')=='subset' and (type(config.get('sample_size')) is not int or config['sample_size']<1):raise ValueError('Positive subset size required')
    if not config.get('variants') or set(config['variants'])-{'ordinary','dependency','length_matched'}:raise ValueError('Invalid variants')
    if type(config.get('evidence_cap'))is not int or config['evidence_cap']<1:raise ValueError('Invalid cap')
    if type(config.get('max_generation_calls'))is not int or config['max_generation_calls']<1:raise ValueError('Invalid request bound')
    if config.get('ablation','none') not in ('none','no_headers','no_links','no_history','no_overlay'):raise ValueError('Unsupported ablation')
    if config.get('answering','program') not in ('program','direct','grounded'):raise ValueError('Unsupported answering mode')
    if type(config.get("generation_attempts",3)) is not int or not 1 <= config.get("generation_attempts",3) <= 3:raise ValueError("Invalid generation attempts")
    if type(config.get("response_timeout_seconds",60)) is not int or not 1 <= config.get("response_timeout_seconds",60) <= 180:raise ValueError("Invalid timeout")
    examples,_=load_examples(config)
    if config.get('ids'):
        wanted=set(config['ids']);chosen=[e for e in examples if e.id in wanted]
        if len(chosen)!=len(wanted) or len(wanted)!=len(config['ids']):raise ValueError('Invalid explicit IDs')
    elif config.get('selection')=='full':chosen=examples
    else:
        groups={}
        for e in examples:groups.setdefault(e.document.get('conversation_id',e.id),[]).append(e)
        excluded=set(config.get('exclude_ids',[]));keys=sorted(k for k,v in groups.items() if not any(e.id in excluded for e in v))
        random.Random(config['seed']).shuffle(keys)
        n=config['sample_size']
        if n>len(keys):raise ValueError('Subset larger than available groups')
        chosen=[e for k in sorted(keys[:n]) for e in groups[k]]
    if not chosen:raise ValueError('Empty evaluation selection')
    if config['dataset']=='convfinqa':
        wanted={e.id for e in chosen}
        for e in examples:
            if e.document['conversation_id'] in {x.document['conversation_id'] for x in chosen} and e.id not in wanted:raise ValueError('Select complete conversations')
    frozen={'config':config,'ids':[e.id for e in chosen],'source_sha256':digest(source_path(config)),
            'input_hashes':{e.id:cache_key(asdict(e)) for e in chosen},'revision':VERSIONS[config['dataset']],
            'instructions':grounded.INSTRUCTIONS if config.get('answering')=='grounded' else grounded.DIRECT_INSTRUCTIONS if config.get('answering')=='direct' else INSTRUCTIONS,'schema':grounded.SCHEMA if config.get('answering')=='grounded' else grounded.DIRECT_SCHEMA if config.get('answering')=='direct' else SCHEMA,'code_hashes':code_hashes(),
            'settings':SETTINGS if config['provider']=='gemini' else OLLAMA_SETTINGS if config['provider']=='ollama' else OPENAI_SETTINGS,
            'selection_unit':'whole conversations' if config['dataset']=='convfinqa' else 'questions'}
    frozen['contract']=cache_key(frozen)
    target=Path(out)
    if target.exists() and json.loads(target.read_text())!=frozen:raise ValueError('Frozen file exists and differs; use new version path')
    write(target,frozen);return frozen


def selected(frozen):
    config=frozen['config']
    if digest(source_path(config))!=frozen['source_sha256']:raise ValueError('Dataset source changed')
    examples,refs=load_examples(config);lookup={e.id:(e,r) for e,r in zip(examples,refs)}
    chosen=[lookup[q] for q in frozen['ids']]
    if {e.id:cache_key(asdict(e)) for e,r in chosen}!=frozen['input_hashes']:raise ValueError('Prediction inputs changed (including corpus)')
    return [e for e,r in chosen],[r for e,r in chosen]


class Mock:
    identity={'provider':'mock','model':'abstention-fixture','version':'1','transport':'mock'}
    counter_name='MOCK_utf8_bytes_div4';count_scope='synthetic count; NOT provider tokens'
    def verify_free(self):return {'status':'mock','model':self.identity,'paid_fallback':False}
    def count(self,text):return (len(text.encode())+3)//4
    def generate(self,req):return {'model':'abstention-fixture','text':canonical({'kind':'abstain'}),'usage':{}}
    def response_text(self,raw):return raw['text']


def altered(example,ablation,history):
    facts=list(example.facts)
    if ablation in ('no_headers','no_links'):
        removed={f.id for f in facts if (ablation=='no_headers' and f.kind=='header') or (ablation=='no_links' and 'link' in f.source)}
        facts=[replace(f,dependencies=tuple(d for d in f.dependencies if d not in removed)) for f in facts if f.id not in removed]
    if ablation!='no_history':
        # Prior questions and predictions are budgeted evidence. No gold/future state.
        for turn,prior in enumerate(history):
            qid=f"history:question:{turn}"
            facts.append(EvidenceFact(qid,prior['question'],{'turn':turn},kind='text'))
            if prior['execution'].get('status')=='ok':
                result=prior['execution'];deps=[qid]
                available={f.id for f in facts}
                for fid in prior['evidence_ids']:
                    if fid in available:deps.append(fid)
                facts.append(EvidenceFact(f'history:prediction:{turn}',str(result['answer']),
                    {'turn':turn,'program_tokens':prior.get('program_tokens'),'predicted_value':str(result['answer'])},tuple(dict.fromkeys(deps)),kind='history'))
    return replace(example,facts=tuple(facts),earlier_questions=() if ablation=='no_history' else example.earlier_questions)


def run(frozen_path,out,mode,provider_factory=None):
    frozen=json.loads(Path(frozen_path).read_text());config=frozen['config'];out=Path(out);out.mkdir(parents=True,exist_ok=True)
    check=dict(frozen);contract=check.pop('contract')
    if cache_key(check)!=contract:raise ValueError('Frozen contract corrupt')
    if frozen['code_hashes']!=code_hashes():raise ValueError('Code changed after freeze; create a new version before inference')
    examples,_=selected(frozen)
    manifest={'contract':contract,'frozen':frozen,'mode':mode,'status':'prepared','model_calls':0,
              'successful_requests':0,'failed_requests':0,'uncertain_requests':0}
    if config.get('engineering_diagnostic'):
        manifest['label']='ENGINEERING DIAGNOSTIC; fresh attempt; NOT completed experiment; earlier remote execution remains uncertain'
    previous=out/'manifest.json';old=json.loads(previous.read_text()) if previous.exists() else None
    if old and (old['contract']!=contract or old['mode']!=mode):raise ValueError('Run directory belongs to different contract/mode')
    if old and old.get('error')=='resolved_model_drift':raise ValueError('Mixed model checkpoint requires a new controlled block')
    if old:
        for pin in ('identity','resolved_models'):
            if pin in old:manifest[pin]=old[pin]
    if mode=='prepare':
        rows=[]
        for e in examples:
            for variant in config['variants']:
                bundle=pack_method(altered(e,config.get('ablation','none'),[]),variant,config['evidence_cap'])
                rows.append({'id':e.id,'variant':variant,'packing':bundle,'note':'estimated; conversations have no predictions yet'})
        write(out/'prepared.json',rows);write(previous,manifest);return manifest
    if mode=='mock':provider=Mock() if provider_factory is None else provider_factory()
    else:
        cls={'gemini':Gemini,'openai':OpenAI,'ollama':Ollama}[config['provider']]
        allowed={'GEMINI_API_KEY','GEMINI_MODEL','GEMINI_FREE_TIER_CONFIRMED'} if cls is Gemini else {
            'OPENAI_API_KEY','OPEN_AI','OPENAI_MODEL','OPENAI_FREE_CREDITS_CONFIRMED'}
        if cls is Ollama:allowed={'OLLAMA_BASE_URL','OLLAMA_MODEL'}
        env=local_environment(ROOT/'.env',allowed)
        provider=cls(env, http=partial(transport, timeout=config.get("response_timeout_seconds",60)))
        if provider.model!=config['model']:raise ValueError('Configured provider/model differs from frozen contract')
    write(previous,manifest)
    try:manifest['access']=provider.verify_free()
    except ProviderError as error:
        manifest.update(status='blocked',error=error.code,error_details=error.details);write(previous,manifest);return manifest
    if old and old.get('identity') and old['identity']!=provider.identity:raise ValueError('Provider/model metadata changed')
    if config.get('expected_digest') and provider.identity.get('digest') != config['expected_digest']:
        raise ValueError('Frozen model digest mismatch')
    manifest['identity']=dict(provider.identity);manifest['status']='running';write(previous,manifest)
    ledger=Ledger(out/'cache.sqlite',provider,config['max_generation_calls'],generation_attempts=config.get('generation_attempts',3));before=ledger.calls();outputs=[];histories={};resolved=set(old.get('resolved_models',[])) if old else set()
    try:
        for e in examples:
            for variant in config['variants']:
                group=e.document.get('conversation_id',e.document.get('filename',e.document['id']));history=histories.setdefault((group,variant),[]) if e.dataset=='convfinqa' else []
                current=altered(e,config.get('ablation','none'),history)
                bundle=pack_method(current,variant,config['evidence_cap'],VisibleTokens());bundle['question']=e.question
                req=(grounded.request if config.get('answering') in ('grounded','direct') else request)(e.question,bundle,dict(provider.identity),frozen['settings'])
                req['instructions']=frozen['instructions'];req['schema']=frozen['schema']
                if config.get('ablation')=='no_overlay' and config.get('answering','program')=='program':
                    req['schema']=json.loads(canonical(req['schema']));req['schema']['properties'].pop('changes');req['instructions']+='\\nHypothetical changes are disabled in this diagnostic.'
                entry={'id':e.id,'variant':variant,'group':group,'turn':e.document.get('turn'),'packing':bundle,'request':req}
                write(out/'current_input.json',entry)
                prediction=ledger.predict(req,bundle);entry['prediction']=prediction
                if prediction.get('resolved_model'):resolved.add(prediction['resolved_model'])
                if len(resolved)>1 or (old and old.get('resolved_models') and not resolved<=set(old['resolved_models'])):raise StopRun('resolved_model_drift')
                outputs.append(entry);write(out/'results.json',outputs)
                execution=prediction.get('execution',{'status':'api_failure'})
                program=convert_output(config['dataset'],e.id,execution).get('predicted') if config['dataset']=='convfinqa' else None
                history.append({'question':e.question,'execution':execution,'program_tokens':program,
                                'evidence_ids':grounded.cited_facts(execution)})
                if prediction['status']=='failed' and str(prediction.get('error','')).startswith('http_4'):raise StopRun(prediction['error'],prediction.get('error_details'))
    except (StopRun,ProviderError,KeyboardInterrupt) as error:
        manifest.update(status='stopped',error=str(error),error_details=getattr(error,'details',{}))
    finally:
        if manifest['status']=='running':
            expected={(e.id,v) for e in examples for v in config['variants']}
            actual={(r['id'],r['variant']) for r in outputs}
            manifest['status']='completed' if actual==expected else 'incomplete'
        manifest['expected_requests']=len(examples)*len(config['variants'])
        manifest.update(model_calls=ledger.calls(),new_calls=ledger.calls()-before,cache_hits=ledger.cache_hits,
                        count_calls=ledger.count_calls,resolved_models=sorted(resolved),completed_requests=len(outputs))
        manifest.update(ledger.outcome_counts())
        write(previous,manifest);ledger.close()
    return manifest


def evaluate(frozen_path,out,repositories=ROOT/'third_party'):
    frozen=json.loads(Path(frozen_path).read_text());examples,refs=selected(frozen);out=Path(out)
    manifest=json.loads((out/'manifest.json').read_text())
    if manifest['contract']!=frozen['contract']:raise ValueError('Run contract mismatch')
    if manifest.get('error')=='resolved_model_drift':raise ValueError('Mixed model run cannot be scored as architectural comparison')
    rows=json.loads((out/'results.json').read_text()) if (out/'results.json').exists() else []
    lookup={(r['id'],r['variant']):r for r in rows}
    if len(lookup)!=len(rows):raise ValueError('Duplicate result records')
    metrics={}
    for variant in frozen['config']['variants']:
        results={};counts=Counter()
        for e in examples:
            row=lookup.get((e.id,variant))
            result=row['prediction'].get('execution',{'status':'api_failure'}) if row else {'status':'missing'}
            if frozen['config'].get('answering','program')!='direct' and result.get('status')=='ok':
                converted=convert_output(frozen['config']['dataset'],e.id,result)
                if frozen['config']['dataset'] in ('finqa','convfinqa') and converted['predicted']==['EOF']:
                    result=dict(result,status='unsupported_export',error='This answer mode has no supported official program representation')
            results[e.id]=result;counts[result['status']]+=1
        scores=official_score(frozen['config']['dataset'],examples,refs,results,out/variant,repositories,frozen['config'].get('answering','program'))
        scores.update(counts=dict(counts),mode=manifest['mode'],provider=manifest.get('identity'),contract=frozen['contract'],answering=frozen['config'].get('answering','program'))
        metrics[variant]=scores
    write(out/'metrics.json',metrics);return metrics


def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('freeze');p.add_argument('config');p.add_argument('out')
    p=sub.add_parser('run');p.add_argument('frozen');p.add_argument('out');p.add_argument('--mode',choices=['prepare','mock','live'],default='prepare')
    p=sub.add_parser('evaluate');p.add_argument('frozen');p.add_argument('out')
    args=parser.parse_args()
    if args.command=='freeze':r=freeze(args.config,args.out);print(canonical({'frozen':args.out,'examples':len(r['ids']),'contract':r['contract']}))
    elif args.command=='run':r=run(args.frozen,args.out,args.mode);print(canonical({k:r[k] for k in ('status','model_calls','completed_requests','error','error_details') if k in r}))
    else:r=evaluate(args.frozen,args.out);print(canonical({k:{'metrics':v.get('metrics'),'counts':v['counts'],'denominator':v['denominator']} for k,v in r.items()}))

if __name__=='__main__':main()
