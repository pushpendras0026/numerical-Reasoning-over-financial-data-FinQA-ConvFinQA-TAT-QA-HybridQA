"""Dataset-neutral evidence, deterministic retrieval and budgeted packing."""
import json
import re
from dataclasses import dataclass, asdict
from decimal import Decimal


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


@dataclass(frozen=True)
class EvidenceFact:
    id: str
    raw: str
    source: dict
    dependencies: tuple = ()
    kind: str = 'text'
    unit: str = 'unknown'
    structure_uncertain: bool = False
    parsed_decimal: str | None = None
    scale: str = 'unknown'


@dataclass(frozen=True)
class PredictionExample:
    dataset: str
    version: str
    split: str
    id: str
    question: str
    document: dict
    facts: tuple
    earlier_questions: tuple = ()


@dataclass(frozen=True)
class ReferenceRecord:
    id: str
    labels: dict


class EstimatedTokens:
    """UTF-8 bytes / 4, rounded up. Estimate only; NOT a model token count."""
    name = 'estimated_utf8_bytes_div4'
    estimated = True

    def count(self, text):
        return (len(text.encode('utf-8')) + 3) // 4


def render(facts):
    return canonical([asdict(f) for f in facts])


def retrieve(example):
    """Deterministic BM25 over supplied candidates, with immediate readable headers."""
    import math
    from collections import Counter
    facts = {f.id: f for f in example.facts}
    candidates = [f for f in example.facts if f.kind in ('cell', 'text', 'history')]
    def terms(text): return re.findall(r'\w+', text.lower())
    query = set(terms(example.question + ' ' + ' '.join(example.earlier_questions)))
    texts = [terms(f.raw + ' ' + ' '.join(facts[d].raw for d in f.dependencies)) for f in candidates]
    avg = sum(map(len,texts)) / max(1,len(texts)) or 1
    df=Counter(t for text in texts for t in set(text))
    def score(item):
        f,text=item;tf=Counter(text)
        value=sum(math.log(1+(len(texts)-df[t]+0.5)/(df[t]+0.5))*tf[t]*2.2 /
                  (tf[t]+1.2*(0.25+0.75*len(text)/avg)) for t in query if tf[t])
        return -value,f.id
    return [f.id for f,_ in sorted(zip(candidates,texts),key=score)]


def pack(example, candidates, cap, dependent=False, counter=None):
    counter = counter or EstimatedTokens()
    if cap < counter.count(render([])):
        raise ValueError('Budget cannot hold empty evidence envelope')
    facts = {f.id: f for f in example.facts}
    selected, seeds, added, dropped = [], [], [], []
    def closure(fid, active=()):
        if fid in active:
            raise ValueError('Dependency cycle')
        f = facts[fid]
        result = []
        if dependent:
            for dep in f.dependencies:
                result += closure(dep, active + (fid,))
        # Baseline has readable headers inline, at the same accounting cost.
        if not dependent and f.dependencies:
            f = EvidenceFact(f.id, ' | '.join(facts[d].raw for d in f.dependencies) + ' | ' + f.raw,
                             f.source, (), f.kind, f.unit, f.structure_uncertain, f.parsed_decimal, f.scale)
        return result + [f]
    for seed in candidates:
        bundle = closure(seed)
        seen = {f.id for f in selected}
        novel = []
        for f in bundle:
            if f.id not in seen:
                novel.append(f)
                seen.add(f.id)
        if counter.count(render(selected + novel)) <= cap:
            selected += novel
            seeds.append(seed)
            added += [f.id for f in novel if f.id != seed]
        else:
            dropped.append(seed)
    return {'facts': [asdict(f) for f in selected], 'seeds': seeds,
            'added_dependencies': added, 'dropped': dropped, 'truncated': bool(dropped),
            'token_count': counter.count(render(selected)), 'token_cap': cap,
            'counter': counter.name, 'token_count_is_estimate': counter.estimated}


def pack_method(example, method, cap, counter=None):
    """A/B/C with whole facts only; C expands neighboring context to B's length."""
    counter=counter or EstimatedTokens()
    ranked=retrieve(example)
    if method in ('ordinary','dependency'):
        return pack(example,ranked,cap,method=='dependency',counter)
    if method!='length_matched':raise ValueError('Unknown packing method')
    target=pack(example,ranked,cap,True,counter)['token_count']
    # Start with the highest ranked candidate, then its immediate source neighbors.
    # Repeat deterministically. Neighbors never consult dependency edges or labels.
    eligible=[f.id for f in example.facts if f.kind in ('cell','text','history')]
    positions={fid:i for i,fid in enumerate(eligible)}
    order=[]
    for seed in ranked:
        i=positions[seed]
        order.extend([seed]+[eligible[j] for j in (i-1,i+1) if 0<=j<len(eligible)])
    order=list(dict.fromkeys(order))
    result=pack(example,order,target,False,counter)
    result.update(target_tokens=target,matching_gap=target-result['token_count'],
                  matching_rule='whole neighboring candidates; never pad or cut strings; may underfill')
    return result
