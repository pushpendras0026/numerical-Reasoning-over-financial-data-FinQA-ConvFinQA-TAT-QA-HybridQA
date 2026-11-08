"""Offline engineering demonstration. Never reads gold programs to build plans."""
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from nrqa.core import canonical, retrieve, pack
from nrqa.finqa import convert, VERSION
from nrqa.execute import NUMBER, number, execute
from nrqa.evaluation import score

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'third_party/FinQA/dataset/train.json'
OUT = ROOT / 'artifacts/local_finqa'


def fixture_plan(spec, example):
    # The literal selectors are handwritten fixture data, not a predictor.
    # Resolve them exclusively against the prediction-safe evidence view.
    def operand(value):
        if type(value) is int:
            return {'step': value}
        if value.startswith('const_'):
            return {'constant': value[6:]}
        for fact in example.facts:
            for match in NUMBER.finditer(fact.raw):
                if number(match.group()) == number(value):
                    return {'fact': fact.id, 'start': match.start(), 'end': match.end()}
        raise ValueError(f'Fixture operand {value} absent from input {example.id}')
    return {'kind': 'arithmetic', 'steps': [{'op': op, 'args': [operand(a), operand(b)]}
                                         for op, a, b in spec['steps']]}


def write(name, value):
    (OUT / name).write_text(canonical(value) + '\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = json.loads(RAW.read_text())
    fixture_path = ROOT / 'experiments/finqa_test_fixtures.json'
    fixtures = json.loads(fixture_path.read_text())
    specs = fixtures['examples']
    assert [r['id'] for r in raw[:10]] == [s['id'] for s in specs]
    predictions, inputs, refs, logs = [], [], [], []
    for index, spec in enumerate(specs):
        record = raw[index]
        example, reference = convert(record, 'train', '../FinQA/dataset/train.json', index)
        inputs.append(asdict(example))
        refs.append(asdict(reference))
        candidates = retrieve(example)
        ordinary = pack(example, candidates, 4000)
        dependent = pack(example, candidates, 4000, True)
        plan = fixture_plan(spec, example)
        # Execution contract fixtures use all supplied evidence under an explicit
        # large estimated budget. They do not claim retrieval success at 4000.
        full = pack(example, [f.id for f in example.facts], 100000, True)
        assert not full['dropped']
        result = execute(plan, full)
        assert result['status'] == 'ok', result
        predictions.append({'id': example.id, 'predicted': result['tokens']})
        logs.append({'id': example.id, 'label': fixtures['label'], 'ordinary_4000': ordinary,
                     'dependent_4000': dependent, 'execution_evidence': full,
                     'plan': plan, 'result': result})
    write('prediction_inputs.json', inputs)
    write('reference_store.json', refs)
    write('fixture_traces.json', logs)
    write('official_predictions.json', predictions)
    # Official scorer needs the original reference record shape, evaluation only.
    write('official_references.json', raw[:10])
    scorer = ROOT / 'third_party/FinQA/code/evaluate/evaluate.py'
    metrics = score(predictions, [s['id'] for s in specs], OUT / 'official_predictions.json',
                    OUT / 'official_references.json', scorer)
    write('fixture_metrics.json', metrics)
    write('manifest.json', {'label': fixtures['label'], 'dataset': 'finqa', 'split': 'train',
          'source_revision': VERSION, 'source_count': len(raw), 'evaluated_fixture_count': 10,
          'ids': [s['id'] for s in specs], 'raw_sha256': hashlib.sha256(RAW.read_bytes()).hexdigest(),
          'fixture_sha256': hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
          'estimated_budgets': {'retrieval_comparison': 4000, 'execution_contract_fixture': 100000},
          'model_calls': 0, 'scope': 'engineering fixtures only; no full-dataset evaluation'})
    print(canonical(metrics))


if __name__ == '__main__':
    main()
