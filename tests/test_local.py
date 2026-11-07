import copy
import hashlib
import json
import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

from nrqa.core import EvidenceFact, PredictionExample, canonical, retrieve, pack, EstimatedTokens, render
from nrqa.finqa import convert
from nrqa.execute import execute, number
from nrqa.evaluation import check_coverage, load_official

ROOT = Path(__file__).resolve().parents[1]


class LocalMilestone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((ROOT.parent / 'FinQA/dataset/train.json').read_text())[:10]

    def example(self, record=None):
        return convert(record or self.raw[0], 'train', '../FinQA/dataset/train.json', 0)[0]

    def test_reference_firewall_all_ten(self):
        for raw in self.raw:
            before = canonical(asdict(self.example(raw)))
            changed = copy.deepcopy(raw)
            changed['qa'] = {'question': raw['qa']['question'], 'answer': 'POISON',
                             'program': 'POISON', 'gold_inds': {'POISON': 'POISON'}}
            for key in ('table_retrieved', 'text_retrieved', 'model_input', 'annotation'):
                changed[key] = 'POISON'
            self.assertEqual(before, canonical(asdict(self.example(changed))))
            changed['qa'] = {'question': raw['qa']['question']}
            self.assertEqual(before, canonical(asdict(self.example(changed))))

    def test_source_roundtrip_headers_and_units(self):
        for raw in self.raw:
            ex = self.example(raw)
            self.assertEqual(ex.document['table_ori'], raw['table_ori'])
            for f in ex.facts:
                s = f.source
                if s['field'] == 'table':
                    self.assertEqual(f.raw, raw['table'][s['row']][s['column']])
                    if f.kind == 'cell':
                        self.assertTrue(any(':table:0:' in d for d in f.dependencies))
                        self.assertTrue(any(d.endswith(':0') for d in f.dependencies))
                else:
                    self.assertEqual(f.raw, raw[s['field']][s['paragraph']][s['start']:s['end']])
        raw = copy.deepcopy(self.raw[0])
        raw['pre_text'].append('Amounts in millions of dollars')
        ex = self.example(raw)
        cell = next(f for f in ex.facts if f.kind == 'cell')
        bundle = pack(ex, [cell.id], 100000, True)
        self.assertTrue(any('Amounts in millions' in f['raw'] for f in bundle['facts']))

    def test_budget_and_dependency_closure(self):
        facts = (EvidenceFact('ancestor', 'USD in millions', {}),
                 EvidenceFact('header', '2020', {}, ('ancestor',), 'header'),
                 EvidenceFact('value', '42', {}, ('header',), 'cell'),
                 EvidenceFact('other', '43', {}, ('header',), 'cell'))
        ex = PredictionExample('fixture', '1', 'train', 'x', '2020', {}, facts)
        full = pack(ex, ['value', 'other'], 10000, True)
        self.assertEqual([f['id'] for f in full['facts']], ['ancestor', 'header', 'value', 'other'])
        self.assertEqual(full['added_dependencies'].count('ancestor'), 1)
        for cap in (1, 20, full['token_count'] - 1, full['token_count']):
            for dependent in (False, True):
                packed = pack(ex, ['value', 'other'], cap, dependent)
                self.assertLessEqual(packed['token_count'], cap)
                self.assertTrue(packed['token_count_is_estimate'])
                if dependent:
                    ids = {f['id'] for f in packed['facts']}
                    for f in packed['facts']:
                        self.assertTrue(set(f['dependencies']) <= ids)
        self.assertEqual(pack(ex, ['value'], 1, True)['facts'], [])
        cycle = PredictionExample('fixture', '1', 'train', 'x', '', {},
                                  (EvidenceFact('a', '', {}, ('a',)),))
        with self.assertRaises(ValueError): pack(cycle, ['a'], 100, True)

    def test_arithmetic_and_invalid_operations(self):
        evidence = {'facts': [{'id': 'a', 'raw': '10', 'unit': 'unknown'},
                              {'id': 'b', 'raw': '0', 'unit': 'unknown'}]}
        a = {'fact': 'a', 'start': 0, 'end': 2}
        b = {'fact': 'b', 'start': 0, 'end': 1}
        def run(op, args):
            return execute({'kind': 'arithmetic', 'steps': [{'op': op, 'args': args}]}, evidence)
        self.assertEqual(run('add', [a, a])['answer'], '20')
        self.assertEqual(run('subtract', [b, a])['answer'], '-10')
        for op, args in [('divide', [a, b]), ('eval', [a, a]), ('add', [a, {'step': 0}]),
                         ('exp', [a, {'constant': '100'}]), ('add', [a, {'literal': 3}]),
                         ('add', [a, dict(a, fact='missing')]), ('add', [a, dict(a, end=99)])]:
            self.assertEqual(run(op, args)['status'], 'invalid')
        self.assertEqual(number('(1,234.5)'), -number('1234.5'))
        self.assertEqual(number('25%'), number('0.25'))
        with self.assertRaises(Exception): number('-')
        result = execute({'kind': 'extract', 'operand': a}, evidence)
        self.assertEqual(result['answer'], '10')
        self.assertIsNone(result['tokens'])  # No fabricated FinQA identity program.

    def test_official_semantics_and_coverage(self):
        official = load_official(ROOT.parent / 'FinQA/code/evaluate/evaluate.py')
        for op, a, b, expected in [('divide', '1', '3', 0.33333),
                                   ('multiply', '-2', '25%', -0.5)]:
            invalid, answer = official.eval_program([op+'(', a, b, ')', 'EOF'], [])
            self.assertEqual((invalid, answer), (0, expected))
        self.assertEqual(official.eval_program(['divide(', '1', '0', ')', 'EOF'], [])[0], 1)
        for predictions in ([], [{'id': 'x'}, {'id': 'x'}], [{'id': 'extra'}]):
            with self.assertRaises(ValueError): check_coverage(predictions, ['x'])

    def test_repeatable_complete_run(self):
        def run():
            subprocess.run([sys.executable, 'scripts/run_local_finqa.py'], cwd=ROOT, check=True,
                           stdout=subprocess.PIPE, text=True)
            return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (ROOT / 'artifacts/local_finqa').glob('*.json')}
        self.assertEqual(run(), run())


if __name__ == '__main__': unittest.main()
