"""Sensitivity of Block B on MultiHiertt to the official evaluator's number handling.

The official span path strips minus signs and has no fraction/percent equivalence.
FinQA and ConvFinQA use the relaxed measure in Block B; this applies the same rule
to numeric MultiHiertt golds on both sides, keeping official scores for text golds.
"""
import json
from pathlib import Path
from nrqa.official_worker import relaxed_numeric

ROOT = Path('artifacts/v11/b')


def load(run):
    records = json.loads((ROOT / run / 'dependency/scoring_inputs.json').read_text())['records']
    metrics = {m['id']: m for m in json.loads((ROOT / run / 'metrics.json').read_text())['dependency']['per_example']}
    results = {r['id']: r['prediction'].get('execution', {}) for r in json.loads((ROOT / run / 'results.json').read_text())}
    return records, metrics, results


def relaxed(run):
    records, metrics, results = load(run)
    scores = {}
    for record in records:
        qid = record['id']
        gold = record['reference'].get('answer')
        official = metrics[qid]['score']['f1']
        numeric = isinstance(gold, (int, float)) and not isinstance(gold, bool)
        answered = metrics[qid]['status'] == 'ok'
        scores[qid] = relaxed_numeric(results[qid].get('answer', ''), gold) if numeric and answered else official
    return scores, {q: metrics[q]['score']['f1'] for q in scores}


def main():
    left, left_official = relaxed('multihiertt_b_grounded')
    right, right_official = relaxed('multihiertt_b_direct')
    n = len(left)
    result = {'n': n, 'official': {'executor': sum(left_official.values()) / n, 'direct': sum(right_official.values()) / n},
              'relaxed_numeric': {'executor': sum(left.values()) / n, 'direct': sum(right.values()) / n},
              'gained': {'executor': sum(left[q] > left_official[q] for q in left), 'direct': sum(right[q] > right_official[q] for q in right)}}
    result['differences'] = {q: left[q] - right[q] for q in left}
    Path('artifacts/v11/multihiertt_sensitivity.json').write_text(json.dumps(result, indent=1) + '\n')
    print({k: v for k, v in result.items() if k != 'differences'})


if __name__ == '__main__':
    main()
