"""Exact numbers behind the presentation clips, computed with the pipeline's own code.

Writes artifacts/v11/video_examples.json. Nothing here calls a model: the replayed
TAT-QA case is read from the saved Block A results.
"""
import json
from dataclasses import asdict
from pathlib import Path

import report_tables
from nrqa.core import EvidenceFact, VisibleTokens, evidence_item, pack, retrieve
from nrqa.coverage import SOURCES
from nrqa.datasets import read

ROOT = Path('artifacts/v11')
vt = VisibleTokens()


def example(dataset, prefix):
    path, member, corpus = SOURCES[dataset]
    return next(e for e, _ in read(dataset, path, 'dev', corpus, member) if e.id.startswith(prefix))


def ordinary(f, facts):
    labels = [facts[d].raw for d in f.dependencies if facts[d].kind != 'text']
    return EvidenceFact(f.id, ' | '.join(labels) + ' | ' + f.raw, f.source, (), f.kind) if labels else f


def split(cost, parts):
    """Share an exact token cost among text parts in proportion to their UTF-8 bytes."""
    sizes = [len(p.encode()) for p in parts]
    raw = [cost * s / sum(sizes) for s in sizes]
    whole = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: whole[i] - raw[i])[:cost - sum(whole)]:
        whole[i] += 1
    return whole


def visa():
    ex = example('finqa', 'V/2008/page_17.pdf-1')
    facts = {f.id: f for f in ex.facts}
    cell = lambda r, c: facts[f"{ex.document['id']}:table:{r}:{c}"]
    row = [cell(3, c) for c in range(1, 5)]
    ranked = [i for i in retrieve(ex) if facts[i].kind == 'cell']
    ordinary_facts = []
    for f in row:
        o = ordinary(f, facts)
        header, label = facts[f.dependencies[0]].raw, facts[f.dependencies[1]].raw
        ordinary_facts.append({'value': f.raw, 'cost': vt.cost(o), 'rendered': evidence_item(o.raw, asdict(o)['source'], o.kind).strip(' |'),
                               'parts': split(vt.cost(o), [f"c{f.source['column']}={header} | ", f'{label} | ', f'{f.raw} | '])})
    dependency_facts, packed = [], set()
    for f in row:
        bundle = [facts[d] for d in f.dependencies if d not in packed]
        packed.update(d.id for d in bundle)
        dependency_facts.append({'value': f.raw, 'parts': [vt.cost(b) for b in bundle] + [vt.cost(f)],
                                 'kinds': ['row' if b.source['column'] == 0 else 'column' for b in bundle] + ['value']})
    cumulative = {m: [pack(ex, [f.id for f in row[:k]], 10 ** 6, m == 'dependency', vt)['token_count'] for k in range(1, 5)]
                  for m in ('ordinary', 'dependency')}
    # Length-matched on the same four seeds: ordinary facts plus document neighbours, up to D's tokens.
    eligible = [f.id for f in ex.facts if f.kind in ('cell', 'text', 'history')]
    order = []
    for seed in row:
        i = eligible.index(seed.id)
        order += [seed.id] + [eligible[j] for j in (i - 1, i + 1) if 0 <= j < len(eligible)]
    length = pack(ex, list(dict.fromkeys(order)), cumulative['dependency'][-1], False, vt)
    return {'id': ex.id, 'question': ex.question, 'table': ex.document['table'],
            'top_cells': [facts[i].raw for i in ranked[:2]], 'row_rank': [facts[i].raw for i in ranked if i in {f.id for f in row}],
            'headers': {f.raw: [facts[d].raw for d in f.dependencies] for f in row}, 'ordinary': ordinary_facts, 'dependency': dependency_facts,
            'cumulative': cumulative,
            'length_matched': [{'raw': f['raw'], 'cost': vt.cost(EvidenceFact(f['id'], f['raw'], f['source'], (), f['kind']))}
                               for f in length['facts']]}


def replay():
    run = ROOT / 'a/tatqa_eval'
    rows = [r for r in json.loads((run / 'results.json').read_text()) if r['id'].startswith('32cbd9ff')]
    scores = {m: {x['id']: x['score']['f1'] for x in json.loads((run / m / 'metrics.json').read_text())['per_example']}
              for m in ('ordinary', 'dependency')}
    out = {}
    for r in rows:
        if r['variant'] == 'length_matched':
            continue
        p = r['prediction']['parsed_prediction']
        out[r['variant']] = {
            'facts': [{'kind': f['kind'], 'raw': f['raw'], 'cost': vt.cost(EvidenceFact(f['id'], f['raw'], f['source'], (), f['kind']))}
                      for f in r['packing']['facts']],
            'used': r['packing']['token_count'], 'cap': r['packing']['token_cap'], 'reasoning': p['reasoning'],
            'steps': p['steps'], 'answer': r['prediction'].get('execution', {}).get('answer'), 'f1': scores[r['variant']][r['id']]}
        question = r['request']['input'].split('\n')[0].removeprefix('Question: ')
    ex = example('tatqa', '32cbd9ff')
    facts = {f.id: f for f in ex.facts}
    missing = next(f for f in ex.facts if f.raw == '358')
    gold = next(r['reference'] for r in json.loads((run / 'dependency/scoring_inputs.json').read_text())['records']
                if r['id'].startswith('32cbd9ff'))
    return {'question': question, 'gold': gold['answer'], **out, 'missing_cell_ordinary_cost': vt.cost(ordinary(missing, facts))}


def withdrawn():
    sensitivity = json.loads((ROOT / 'multihiertt_sensitivity.json').read_text())
    groups = {r['id']: r['group'] for r in json.loads((ROOT / 'b/multihiertt_b_grounded/results.json').read_text())}
    diff, low, high, _ = report_tables.bootstrap(sensitivity['differences'], groups)
    return {**{k: v for k, v in sensitivity.items() if k != 'differences'}, 'relaxed_diff': diff, 'relaxed_ci': [low, high]}


def dots():
    c = json.loads((ROOT / 'coverage.json').read_text())['hybridqa']
    n, kept, split_ = c['n'], c['coverage']['1500'], c['discordant']['1500']
    ordinary_kept = round(kept['ordinary'] * n)
    both = ordinary_kept - split_['ord_only']
    return {'n': n, 'both': both, 'dep_only': split_['dep_only'], 'ord_only': split_['ord_only'],
            'neither': n - both - split_['dep_only'] - split_['ord_only']}


if __name__ == '__main__':
    result = {'visa': visa(), 'replay': replay(), 'withdrawn': withdrawn(), 'hybridqa_dots': dots()}
    (ROOT / 'video_examples.json').write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps(result, indent=1)[:6000])
