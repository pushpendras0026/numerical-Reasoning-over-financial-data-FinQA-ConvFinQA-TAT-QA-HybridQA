"""Classify every non-credited executor answer in a run. Exact counts from saved outputs."""
import collections
import json
import sys
from pathlib import Path
from nrqa.execute import number

NAMES = ['finqa', 'convfinqa', 'tatqa', 'tathqa', 'hybridqa', 'multihiertt']


def value(text):
    try:
        return float(number(str(text)))
    except Exception:
        return None


def classify(status, answer, gold, error):
    if status == 'abstain':
        return 'abstained'
    if status == 'unsupported_export':
        return 'no official program'
    if status != 'ok':
        if 'not in evidence' in (error or ''):
            return 'value not in evidence'
        return 'rejected plan'
    a, g = value(answer), value(gold)
    if a is None or g is None:
        return 'wrong span or text'
    if g and abs(abs(a / g) - 1) < .01:
        return 'wrong sign'
    for factor in (100, 1000, 1e6, .01, .001, 1e-6):
        if g and abs(a / g / factor - 1) < .01:
            return 'wrong scale'
    return 'wrong value'


def main(root, suffix, variant):
    table = {}
    for name in NAMES:
        run = Path(root) / f'{name}_{suffix}'
        if not (run / 'metrics.json').exists():
            continue
        metrics = json.loads((run / 'metrics.json').read_text())[variant]
        rows = {r['id']: r for r in json.loads((run / 'results.json').read_text()) if r['variant'] == variant}
        frozen = json.loads(Path(f"experiments/frozen_v11/{Path(root).name}/{name}_{suffix}.json").read_text())
        key = 'execution' if name in ('finqa', 'convfinqa') else 'f1'
        scoring = json.loads((run / variant / 'scoring_inputs.json').read_text())
        gold = {r['id']: r['reference'] for r in scoring['records']}
        counts = collections.Counter()
        for row in metrics['per_example']:
            if row['status'] == 'missing' or row['score'].get(key, 0) >= .999:
                continue
            execution = rows[row['id']]['prediction'].get('execution', {})
            label = gold[row['id']]
            target = label.get('exe_ans', label.get('answer'))
            target = target[0] if isinstance(target, list) and target else target
            counts[classify(row['status'], execution.get('answer'), target, execution.get('error'))] += 1
        table[name] = dict(counts)
        print(name, sum(counts.values()), '/', metrics['denominator'], dict(counts.most_common()))
    Path(root, 'errors.json').write_text(json.dumps(table, indent=1) + '\n')


if __name__ == '__main__':
    main(*sys.argv[1:4])
