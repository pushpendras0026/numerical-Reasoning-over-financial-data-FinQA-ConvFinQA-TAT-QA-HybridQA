"""What inline labels cost. Exact under core.py's rules, over every dev document.

Per cell: ordinary cost (labels inline) against the bare cell (dependency's marginal
cost once its headers are packed). Per document: tokens needed to show the whole
document under each method (dependency = every fact once; ordinary = cells with
labels inline plus text, headers never shown on their own).
Writes artifacts/v11/label_cost.json.
"""
import json
import statistics
from nrqa.coverage import SOURCES
from nrqa.datasets import read
from nrqa.core import VisibleTokens, EvidenceFact

vt = VisibleTokens()


def ordinary(f, facts):
    labels = [facts[d].raw for d in f.dependencies if facts[d].kind != 'text']
    if f.dependencies and f.kind != 'history' and labels:
        return EvidenceFact(f.id, ' | '.join(labels) + ' | ' + f.raw, f.source, (), f.kind)
    return f


out = {}
for name, (path, member, corpus) in SOURCES.items():
    seen, o_cell, d_cell, o_doc, d_doc = set(), [], [], [], []
    for ex, _ in read(name, path, 'dev', corpus, member):
        if ex.document['id'] in seen:
            continue
        seen.add(ex.document['id'])
        facts = {f.id: f for f in ex.facts}
        d_doc.append(sum(vt.cost(f) for f in ex.facts))
        o_doc.append(sum(vt.cost(ordinary(f, facts)) for f in ex.facts if f.kind in ('cell', 'text', 'history')))
        for f in ex.facts:
            if f.kind == 'cell' and any(facts[d].kind != 'text' for d in f.dependencies):
                o_cell.append(vt.cost(ordinary(f, facts)))
                d_cell.append(vt.cost(f))
    out[name] = {'documents': len(d_doc), 'cells': len(o_cell),
                 'cell_ordinary_mean': statistics.mean(o_cell), 'cell_bare_mean': statistics.mean(d_cell),
                 'doc_dependency_median': statistics.median(d_doc), 'doc_ordinary_median': statistics.median(o_doc)}
    print(name, {k: round(v, 1) for k, v in out[name].items()}, flush=True)
json.dump(out, open('artifacts/v11/label_cost.json', 'w'), indent=1)
