"""Prediction-only normalized preparation; Python reference and Spark local workload."""
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
from .core import canonical
from .experiment import load_examples,write


def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()


def prepare(configs,out,limit=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);documents={};facts={};questions=[]
    for path in configs:
        config=json.loads(Path(path).read_text());examples,_=load_examples(config)
        if limit:examples=examples[:limit]
        for e in examples:
            # Text/table content fingerprints exclude dataset-specific UIDs and labels.
            payload={'tables':e.document.get('tables',e.document.get('table',e.document.get('tables_html',[]))),
                     'text':[f.raw for f in e.facts if f.kind=='text']}
            content=fingerprint(payload);key=f'{e.dataset}:{e.split}:{content}'
            if key not in documents:
                documents[key]={'document_id':key,'dataset':e.dataset,'split':e.split,'content_hash':content,'source_document_ids':[]}
            if e.document['id'] not in documents[key]['source_document_ids']:documents[key]['source_document_ids'].append(e.document['id'])
            questions.append({'id':e.id,'document_id':key,'dataset':e.dataset,'split':e.split,
                              'source_document_id':e.document['id'],'question_hash':fingerprint(e.question.strip().lower()),'content_hash':content,
                              'question_context_hash':fingerprint([content,e.question.strip().lower()])})
            aliases={}
            for f in e.facts:
                location={k:v for k,v in f.source.items() if k in ('field','table','row','column','order','start','end','link')}
                if 'order' not in location and 'paragraph' in f.source:location['paragraph']=f.source['paragraph']
                aliases[f.id]=key+':fact:'+fingerprint([f.kind,location,f.raw])
            for f in e.facts:
                fid=aliases[f.id];dependencies=[aliases[d] for d in f.dependencies]
                if fid not in facts:
                    facts[fid]={'id':fid,'document_id':key,'dataset':e.dataset,'split':e.split,'raw':f.raw,
                                'dependencies':dependencies,'kind':f.kind,'source_ids':[]}
                if facts[fid]['dependencies']!=dependencies:raise ValueError('Inconsistent dependencies for deduplicated fact')
                if f.id not in facts[fid]['source_ids']:facts[fid]['source_ids'].append(f.id)
    for row in documents.values():row['source_document_ids'].sort()
    for row in facts.values():row['source_ids'].sort()
    for name,rows in [('documents',documents.values()),('facts',facts.values()),('questions',questions)]:
        path=out/(name+'.jsonl')
        with path.open('w') as stream:
            for row in sorted(rows,key=canonical):stream.write(canonical(row)+'\n')
    write(out/'source_manifest.json',{'configurations':[str(p) for p in configs],'limit_per_source':limit,
                                    'documents':len(documents),'facts':len(facts),'questions':len(questions),
                                    'labels_included':False,'synthetic_replication':False})
    return reference(out)


def read_rows(path):
    with Path(path).open() as stream:
        for line in stream:yield json.loads(line)


def reference(out):
    out=Path(out);docs={r['document_id']:r for r in read_rows(out/'documents.jsonl')}
    joined=[{'id':r['id'],'document_id':r['document_id'],'content_hash':docs[r['document_id']]['content_hash']} for r in read_rows(out/'questions.jsonl')]
    links=[{'fact_id':f['id'],'dependency':dep} for f in read_rows(out/'facts.jsonl') for dep in f['dependencies']]
    fact_ids={f['id'] for f in read_rows(out/'facts.jsonl')}
    unresolved=sum(x['dependency'] not in fact_ids for x in links)
    groups=defaultdict(list)
    for d in docs.values():groups[d['content_hash']].append(d)
    overlap=[]
    for content,group in groups.items():
        for a in group:
            for b in group:
                if a['document_id']<b['document_id']:
                    overlap.append({'left':a['document_id'],'right':b['document_id'],'content_hash':content})
    result={'joined_count':len(joined),'joined_hash':fingerprint(sorted(joined,key=canonical)),
            'edge_count':len(links),'unresolved_edges':unresolved,'overlap':sorted(overlap,key=canonical)}
    write(out/'python_reference.json',result);return result


def spark(out,master='local[4]'):
    from pyspark.sql import SparkSession,functions as F
    out=Path(out).resolve();start=time.monotonic()
    session=(SparkSession.builder.master(master).appName('NRQA prediction-only preparation')
             .config('spark.sql.shuffle.partitions','8').config('spark.ui.enabled','false')
             .config('spark.eventLog.enabled','true').config('spark.eventLog.dir',str(out/'spark-events'))
             .getOrCreate())
    try:
        docs=session.read.json(str(out/'documents.jsonl'));facts=session.read.json(str(out/'facts.jsonl'));questions=session.read.json(str(out/'questions.jsonl'))
        joined=questions.drop('content_hash').join(docs.select('document_id','content_hash'),'document_id').select('id','document_id','content_hash')
        edges=facts.select(F.col('id').alias('fact_id'),F.explode('dependencies').alias('dependency'))
        unresolved=edges.join(facts.select(F.col('id').alias('dependency')),'dependency','left_anti').count()
        a,b=docs.alias('a'),docs.alias('b')
        overlaps=a.join(b,(F.col('a.content_hash')==F.col('b.content_hash'))&(F.col('a.document_id')<F.col('b.document_id'))).select(F.col('a.document_id').alias('left'),F.col('b.document_id').alias('right'),F.col('a.content_hash').alias('content_hash'))
        for name,df in [('facts',facts),('documents',docs),('questions',questions)]:df.write.mode('overwrite').partitionBy('dataset','split').parquet(str(out/'parquet'/name))
        result={'joined_count':joined.count(),'joined_hash':fingerprint(sorted([r.asDict() for r in joined.collect()],key=canonical)),
                'edge_count':edges.count(),'unresolved_edges':unresolved,
                'overlap':sorted([r.asDict() for r in overlaps.collect()],key=canonical)}
        expected=json.loads((out/'python_reference.json').read_text());equal=result==expected
        write(out/'spark_measurement.json',{'master':master,'distributed_cluster':not master.startswith('local'),
              'wall_seconds':time.monotonic()-start,'equals_python':equal,'result':result,
              'spark_version':session.version,'resource_measurement':'Use /usr/bin/time -v for driver; see docs/final-testing.md for JVM process-tree sampling and Spark event logs'})
        if not equal:raise ValueError('Spark differs from Python reference')
        return result
    finally:session.stop()
