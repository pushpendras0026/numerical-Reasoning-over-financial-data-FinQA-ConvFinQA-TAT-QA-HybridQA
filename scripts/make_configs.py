"""Write the v11 experiment configs. Caps come from label-free document sizes."""
import json
from pathlib import Path

MODEL = 'gemini-3.5-flash-lite'  # Block A: packing comparison
MODEL_B = 'gemini-3.1-flash-lite'  # Block B: executor vs direct
OUT = Path('experiments/v11')
DATASETS = {
    'finqa': dict(cap=800, dev='data/FinQA/dev.json', check=('train', 'third_party/FinQA/dataset/train.json', None)),
    'tatqa': dict(cap=400, dev='data/TAT-QA/tatqa_dataset_dev.json', check=('train', 'data/TAT-QA/tatqa_dataset_train.json', None)),
    'tathqa': dict(cap=400, dev='third_party/TAT-HQA/dataset_extra_field/counter/tatqa_and_hqa_field_dev.json',
                   check=('train', 'third_party/TAT-HQA/dataset_extra_field/counter/tatqa_and_hqa_field_train.json', None)),
    'convfinqa': dict(cap=800, dev='data/ConvFinQA/data.zip', member='data/dev.json',
                      check=('train', 'data/ConvFinQA/data.zip', 'data/train.json')),
    'hybridqa': dict(cap=1500, dev='data/HybridQA/dev.json', check=None),
    'multihiertt': dict(cap=1500, dev='data/MultiHiertt/dev.json', check=None),
}
BASE = dict(provider='gemini', model=MODEL, seed=2626, spending_ceiling_usd=0, ablation='none',
            selection='subset', generation_attempts=3, response_timeout_seconds=90, max_generation_calls=100000)


def config(name, data, split, source, member, n, variants, answering, seed=2626, extra=None):
    row = dict(BASE, dataset=name, split=split, source=source, sample_size=n, variants=variants,
               answering=answering, evidence_cap=data['cap'], seed=seed, **(extra or {}))
    if member:
        row['member'] = member
    return row


def main(n=50, conversations=15, check_n=4):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in DATASETS.items():
        size = conversations if name == 'convfinqa' else n
        small = 2 if name == 'convfinqa' else check_n
        if data['check']:
            split, source, member = data['check']
            check = config(name, data, split, source, member, small, ['ordinary', 'dependency'], 'grounded', 7)
        else:  # No train split here: a disjoint seed on dev; evaluation excludes these groups.
            check = config(name, data, 'dev', data['dev'], data.get('member'), small, ['ordinary', 'dependency'], 'grounded', 7)
        evaluation = config(name, data, 'dev', data['dev'], data.get('member'), size,
                            ['ordinary', 'dependency', 'length_matched'], 'grounded')
        # Block B: same evidence, executor vs direct, on its own model and daily quota.
        size_b = 12 if name == 'convfinqa' else 40
        grounded_b = dict(config(name, data, 'dev', data['dev'], data.get('member'), size_b, ['dependency'], 'grounded'), model=MODEL_B)
        direct_b = dict(config(name, data, 'dev', data['dev'], data.get('member'), size_b, ['dependency'], 'direct'), model=MODEL_B)
        for label, row in (('check', check), ('eval', evaluation), ('b_grounded', grounded_b), ('b_direct', direct_b)):
            (OUT / f'{name}_{label}.json').write_text(json.dumps(row, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
