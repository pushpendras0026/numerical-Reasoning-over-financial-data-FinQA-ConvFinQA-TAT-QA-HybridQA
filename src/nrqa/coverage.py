"""Post-inference audit: does gold evidence survive packing? Labels never reach inference.

A question counts as covered when every gold operand (or answer phrase) appears in the
packed evidence or the question; allowed constants need no evidence.
"""
import re
from .core import pack_method
from .datasets import read
from .execute import number,NUMBER,CONSTANTS
from .grounded import literal_spans

SOURCES={'finqa':('data/FinQA/dev.json',None,None),'tatqa':('data/TAT-QA/tatqa_dataset_dev.json',None,None),
 'tathqa':('third_party/TAT-HQA/dataset_extra_field/counter/tatqa_and_hqa_field_dev.json',None,None),
 'convfinqa':('data/ConvFinQA/data.zip','data/dev.json',None),'hybridqa':('data/HybridQA/dev.json',None,'data/WikiTables-WithLinks'),
 'multihiertt':('data/MultiHiertt/dev.json',None,None)}
CAPS=(200,400,800,1500,4000)
METHODS=('ordinary','dependency','length_matched')

def key(text):
    try:return abs(number(text.replace('%','')))
    except Exception:return None

def program_numbers(program):
    out=[]
    for op,args in re.findall(r'([a-z_]+)\(([^()]*)\)',program):
        if op.startswith('table_'):continue
        out+=[a.strip() for a in args.split(',') if a.strip() and not a.strip().startswith(('#','const_'))]
    if '(' not in program and program.strip():out.append(program.strip())
    return out

def targets(dataset,labels):
    """(numbers, phrases) a correct answer needs, or None when undefined."""
    if dataset in ('finqa','convfinqa'):return program_numbers(labels['program']),[]
    if dataset=='multihiertt':
        return (program_numbers(labels['program']),[]) if labels.get('program') else ([],[str(labels['answer'])])
    if dataset=='hybridqa':return [],[str(labels['answer'])]
    kind=labels.get('answer_type')
    if kind=='arithmetic':return [m.group() for m in NUMBER.finditer(labels.get('derivation',''))],[]
    if kind in ('span','multi-span'):return [],[str(a) for a in labels['answer']]
    return None

def covered(want,facts,question):
    numbers,phrases=want
    facts=list(facts)+[{'raw':question}]  # The model may also copy from the question.
    found=set()
    for f in facts:
        for a,b in literal_spans(f['raw']):
            v=key(f['raw'][a:b])
            if v is not None:found.add(v)
    text=' '.join(f['raw'] for f in facts).casefold()
    constants={abs(v) for v in CONSTANTS.values()}
    return all(key(n) in found or key(n) in constants for n in numbers if key(n) is not None) and all(p.strip().casefold() in text for p in phrases)

def one(item):
    example,labels,dataset=item
    want=targets(dataset,labels)
    if want is None or not (want[0] or want[1]):return None
    return {c:{m:covered(want,pack_method(example,m,c)['facts'],example.question) for m in METHODS} for c in CAPS}

def load(dataset):
    path,member,corpus=SOURCES[dataset]
    return [(e,r.labels,dataset) for e,r in read(dataset,path,'dev',corpus,member)]

def summarize(rows):
    rows=[r for r in rows if r]
    return {'n':len(rows),'coverage':{str(c):{m:sum(r[c][m] for r in rows)/len(rows) for m in METHODS} for c in CAPS},
      'discordant':{str(c):{'dep_only':sum(r[c]['dependency'] and not r[c]['ordinary'] for r in rows),
                            'ord_only':sum(r[c]['ordinary'] and not r[c]['dependency'] for r in rows)} for c in CAPS}}
