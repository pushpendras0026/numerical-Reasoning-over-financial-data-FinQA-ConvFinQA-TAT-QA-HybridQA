import json
import unittest
from decimal import Decimal
from nrqa.core import EvidenceFact, PredictionExample, VisibleTokens, pack, pack_method, render_evidence
from nrqa.execute import execute
from nrqa.grounded import cited_facts, locate_number, parse, parse_direct, request
from nrqa.scoring import convert_output


def plan(steps=(), quotes=(), kind='arithmetic', scale=''):
    return json.dumps({'reasoning': '', 'kind': kind, 'quotes': list(quotes), 'scale': scale,
                       'steps': [{'op': o, 'a': a, 'b': b} for o, a, b in steps]})


class GroundedTests(unittest.TestCase):
    def setUp(self):
        self.p = {'question': 'What is the growth if it were 120?',
                  'facts': [{'id': 'a', 'raw': '80', 'unit': 'unknown'}, {'id': 'b', 'raw': 'Revenue was 1,100.', 'unit': 'unknown'},
                            {'id': 'c', 'raw': 'loss (35) rate 3.5%', 'unit': 'unknown'}]}

    def test_multistep_fraction(self):
        _, r = parse(plan([('subtract', '1,100', '80'), ('divide', '#0', '80')], scale='percent_fraction'), self.p)
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(float(r['answer']), 12.75)
        self.assertEqual(r['tokens'], ['subtract(', '1100', '80', ')', 'divide(', '#0', '80', ')', 'EOF'])

    def test_sentence_final_number_is_complete(self):
        self.assertEqual(parse(plan([('add', '1100', '80')]), self.p)[1]['answer'], '1180')

    def test_invented_number_rejected(self):
        _, r = parse(plan([('add', '999', '80')]), self.p)
        self.assertEqual(r['status'], 'invalid')
        self.assertIn('Number not in evidence', r['error'])

    def test_question_number_allowed(self):
        self.assertEqual(parse(plan([('subtract', '120', '80')]), self.p)[1]['answer'], '40')

    def test_accounting_negative_and_percent_keep_source_meaning(self):
        self.assertEqual(parse(plan([('add', '(35)', '80')]), self.p)[1]['answer'], '45')
        self.assertEqual(Decimal(parse(plan([('multiply', '3.5%', '80')]), self.p)[1]['answer']), Decimal('2.8'))

    def test_bare_allowed_constant(self):
        _, r = parse(plan([('add', '1100', '80'), ('divide', '#0', '5')]), self.p)
        self.assertEqual(r['tokens'][-3:-1], ['const_5', ')'])

    def test_non_numeric_literal_is_invalid_not_a_crash(self):
        self.assertEqual(parse(plan([('add', 'N/A', '80')]), self.p)[1]['status'], 'invalid')

    def test_quote_repeats_map_to_distinct_spans(self):
        self.p['facts'][0]['raw'] = 'alpha and alpha'
        _, r = parse(plan(quotes=['alpha', 'alpha'], kind='count'), self.p)
        self.assertEqual(r['answer'], '2')

    def test_invented_quote_rejected(self):
        self.assertEqual(parse(plan(quotes=['absent'], kind='extract'), self.p)[1]['status'], 'invalid')

    def test_arithmetic_with_only_a_quote_is_a_lookup(self):
        self.assertEqual(parse(plan(quotes=['1,100']), self.p)[1]['answer'], '1,100')

    def test_prior_answer_prefers_history_fact(self):
        self.p['facts'].append({'id': 'h', 'raw': '80', 'kind': 'history', 'source': {'predicted_value': '80', 'program_tokens': None}})
        self.assertEqual(locate_number('80', self.p['facts'])['fact'], 'h')

    def test_request_no_labels_and_cited_facts(self):
        self.p['gold_answer'] = 'secret'
        self.assertNotIn('secret', json.dumps(request(self.p['question'], self.p, {}, {})))
        _, r = parse(plan([('add', '1,100', '80')]), self.p)
        self.assertEqual(cited_facts(r), ['b', 'a'])

    def test_direct(self):
        self.assertEqual(parse_direct(json.dumps({'reasoning': '', 'kind': 'direct', 'answer': '5', 'scale': ''}))[1]['answer'], '5')


class Adapters(unittest.TestCase):
    def test_tat_percent_fraction(self):
        self.assertEqual(convert_output('tatqa', 'q', {'status': 'ok', 'answer': '0.25', 'scale': 'percent_fraction'}), {'q': ['25.00', 'percent']})

    def test_conv_single_number(self):
        self.assertEqual(convert_output('convfinqa', 'q', {'status': 'ok', 'answer': '$ 1,183', 'tokens': None})['predicted'], ['1183', 'EOF'])


class Packing(unittest.TestCase):
    def example(self):
        header = EvidenceFact('h', 'Revenue', {'row': 0, 'column': 0, 'table': '0'}, kind='header')
        unit = EvidenceFact('u', 'amounts in millions ' * 5, {'paragraph': 0})
        cells = tuple(EvidenceFact(f'c{i}', str(i), {'row': 1, 'column': i, 'table': '0'}, ('h', 'u'), 'cell') for i in range(1, 4))
        return PredictionExample('t', '1', 'dev', 'q', 'Revenue', {'id': 'd'}, (header, unit) + cells)

    def test_baseline_inlines_labels_not_paragraphs(self):
        facts = pack_method(self.example(), 'ordinary', 200)['facts']
        self.assertEqual(next(f for f in facts if f['id'] == 'c1')['raw'], 'Revenue | 1')

    def test_budget_is_respected_and_counted_on_shown_text(self):
        for method in ('ordinary', 'dependency', 'length_matched'):
            self.assertLessEqual(pack_method(self.example(), method, 40)['token_count'], 40)

    def test_rows_render_in_document_order(self):
        text = render_evidence(pack_method(self.example(), 'dependency', 200)['facts'])
        self.assertIn('table 0 row 1: c1=1 | c2=2 | c3=3', text)


if __name__ == '__main__':
    unittest.main()
