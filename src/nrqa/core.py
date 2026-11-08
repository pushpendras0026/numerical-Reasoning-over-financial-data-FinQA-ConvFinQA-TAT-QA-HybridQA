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


class VisibleTokens(EstimatedTokens):
    """Local budget over the evidence text the model sees; never calls a provider.

    Costs are additive per fact, so packing is linear and the same budget applies
    to every method. Actual prompt tokens are recorded from provider usage metadata.
    """
    name = 'estimated_utf8_bytes_div4_of_rendered_evidence'

    def cost(self, fact):
        return (len(evidence_item(fact.raw, asdict(fact)['source'], fact.kind).encode('utf-8')) + 3) // 4


def evidence_item(raw, source, kind):
    """One fact as shown to the model; `render_evidence` joins these into lines."""
    if 'turn' in source and kind in ('history', 'text'):
        return f"{raw}\n"
    if 'column' in source and 'link' not in source:
        return f"c{source['column']}={raw} | "
    return f"{raw}\n"


def render_evidence(facts):
    """Plain-text evidence in document order: table rows stay rows, text stays text."""
    lines, row_key, row = [], None, []
    def flush():
        nonlocal row, row_key
        if row:
            lines.append(f"table {row_key[0]} row {row_key[1]}: " + ''.join(row).rstrip(' |'))
        row, row_key = [], None
    for f in facts:
        source = f.get('source', {})
        item = evidence_item(f['raw'], source, f.get('kind', 'text'))
        if 'turn' in source and f.get('kind') in ('history', 'text'):
            flush()
            label = 'earlier answer' if f.get('kind') == 'history' else 'earlier question'
            lines.append(f"{label} (turn {source['turn']}): {item.rstrip()}")
        elif 'column' in source and 'link' not in source:
            key = (source.get('table', '0'), source.get('row'))
            if key != row_key:
                flush()
                row_key = key
            row.append(item)
        else:
            flush()
            prefix = f"linked to table row {source['row']}: " if 'link' in source else ''
            lines.append(prefix + item.rstrip())
    flush()
    return '\n'.join(lines)


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
    cost = getattr(counter, 'cost', None)
    if cap < counter.count(render([])):
        raise ValueError('Budget cannot hold empty evidence envelope')
    used = 0
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
        # Baseline has readable labels inline, at the same accounting cost. Only
        # structural labels are inlined: copying whole unit paragraphs into every
        # cell would charge the baseline for text it needs once, and rewriting a
        # history fact would break its exact-value check in the executor.
        labels = [facts[d].raw for d in f.dependencies if facts[d].kind != 'text']
        if not dependent and f.dependencies and f.kind != 'history' and labels:
            f = EvidenceFact(f.id, ' | '.join(labels) + ' | ' + f.raw,
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
        extra = sum(cost(f) for f in novel) if cost else None
        if (used + extra <= cap) if cost else (counter.count(render(selected + novel)) <= cap):
            used += extra or 0
            selected += novel
            seeds.append(seed)
            added += [f.id for f in novel if f.id != seed]
        else:
            dropped.append(seed)
    return {'facts': [asdict(f) for f in selected], 'seeds': seeds,
            'added_dependencies': added, 'dropped': dropped, 'truncated': bool(dropped),
            'token_count': used if cost else counter.count(render(selected)), 'token_cap': cap,
            'counter': counter.name, 'token_count_is_estimate': counter.estimated}


def pack_method(example, method, cap, counter=None):
    """A/B/C with whole facts only; C expands neighboring context to B's length."""
    counter=counter or VisibleTokens()
    ranked=retrieve(example)
    # Conversation state is admitted first for every method, newest turn first,
    # so all methods spend budget on it identically.
    history=sorted((i for i in ranked if i.startswith('history:')),
                   key=lambda i:(-int(i.rsplit(':',1)[1]),i))
    ranked=history+[i for i in ranked if not i.startswith('history:')]
    position={f.id:i for i,f in enumerate(example.facts)}
    def ordered(result):
        # Selection is by rank; presentation is in document order for every method.
        result['facts'].sort(key=lambda f:position[f['id']])
        return result
    if method in ('ordinary','dependency'):
        return ordered(pack(example,ranked,cap,method=='dependency',counter))
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
    return ordered(result)
