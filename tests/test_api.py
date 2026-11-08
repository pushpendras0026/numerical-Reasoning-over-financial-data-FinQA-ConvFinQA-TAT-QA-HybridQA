import copy
from datetime import datetime, timezone
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from nrqa.core import canonical, pack, retrieve
from nrqa.finqa import convert
from nrqa.model import request, parse_and_execute, cache_key
from nrqa.providers import Gemini, ProviderError
from nrqa.runner import Ledger, StopRun

ROOT = Path(__file__).resolve().parents[1]
ENV = {'GEMINI_API_KEY': 'synthetic-secret', 'GEMINI_MODEL': 'gemini-3.8-flash',
       'GEMINI_FREE_TIER_CONFIRMED': 'gemini-3.8-flash:' + datetime.now(timezone.utc).date().isoformat()}


class MockHTTP:
    def __init__(self, errors=(), output=None, model=None):
        self.model = model
        self.errors = list(errors)
        self.calls = []
        self.output = output or {'kind': 'abstain'}

    def __call__(self, method, url, headers, body=None):
        self.calls.append((method, url, body))  # Never retain auth headers.
        if url.endswith(':countTokens'):
            return {'totalTokens': (len(canonical(body).encode()) + 3) // 4}
        if url.endswith(':generateContent'):
            if self.errors:
                raise ProviderError(self.errors.pop(0))
            return {'modelVersion': 'gemini-3.8-flash',
                    'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': canonical(self.output)}]}}],
                    'usageMetadata': {'promptTokenCount': 123, 'candidatesTokenCount': 7}}
        return self.model if self.model is not None else {'name': 'models/gemini-3.8-flash', 'version': '001',
                'supportedGenerationMethods': ['generateContent', 'countTokens']}

    def generations(self):
        return sum(url.endswith(':generateContent') for _, url, _ in self.calls)


def provider(http=None):
    p = Gemini(ENV, http or MockHTTP())
    p.verify_free()
    return p


def bundle():
    return {'facts': [{'id': 'selected', 'raw': '10', 'unit': 'unknown'}]}


class APIIntegration(unittest.TestCase):
    def test_38_wire_contract_and_model_separated_cache(self):
        from nrqa.model import SETTINGS, SCHEMA, DIRECT_SCHEMA
        http = MockHTTP()
        p = provider(http)
        self.assertEqual(SETTINGS, {'maxOutputTokens': 2048,
                                  'thinkingConfig': {'thinkingLevel': 'low'}})
        for schema in (SCHEMA, DIRECT_SCHEMA):
            req = request('q', bundle(), p.identity)
            req['schema'] = schema
            p.generate(req)
            method, url, body = http.calls[-1]
            self.assertEqual(method, 'POST')
            self.assertEqual(url, p.base() + ':generateContent')
            self.assertEqual(body['generationConfig'], dict(SETTINGS,
                responseMimeType='application/json', responseJsonSchema=schema))
        p.count('same evidence')
        self.assertEqual(http.calls[-1], ('POST', p.base() + ':countTokens',
            {'contents': [{'role': 'user', 'parts': [{'text': 'same evidence'}]}]}))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cache.sqlite'
            # Simulate an older model's records in the SAME database. Never call it.
            old_identity = dict(p.identity, model='gemini-2.5-flash')
            old_req = request('q', bundle(), old_identity)
            ledger = Ledger(path, p)
            ledger.save(cache_key(old_req), {'status': 'completed', 'attempts': []})
            old_count = cache_key({'identity': old_identity, 'text': 'same evidence', 'method': 'countTokens'})
            with ledger.db:
                ledger.db.execute('INSERT INTO counts VALUES (?,?)', (old_count, 999999))
            count = ledger.count('same evidence')
            self.assertNotEqual(count, 999999)
            req = request('q', bundle(), p.identity)
            self.assertFalse(ledger.predict(req, bundle())['cache_hit'])
            ledger.close()
            ledger = Ledger(path, p)
            self.assertEqual(ledger.count('same evidence'), count)
            self.assertTrue(ledger.predict(req, bundle())['cache_hit'])
            self.assertEqual(ledger.count_calls, 0)
            ledger.close()

    def test_valid_plan_through_provider_ledger_and_official_execution(self):
        from nrqa.evaluation import load_official
        plan = {'kind': 'arithmetic', 'steps': [{'op': 'divide', 'args': [
            {'fact': 'selected', 'start': 0, 'end': 2}, {'constant': '100'}]}]}
        http = MockHTTP(output=plan)
        p = provider(http)
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Ledger(Path(tmp) / 'cache.sqlite', p)
            result = ledger.predict(request('synthetic question', bundle(), p.identity), bundle())
            self.assertEqual(result['parsed_prediction'], plan)
            self.assertEqual(result['execution']['answer'], '0.1')
            official = load_official(ROOT / 'third_party/FinQA/code/evaluate/evaluate.py')
            self.assertEqual(official.eval_program(result['execution']['tokens'], []), (0, 0.1))
            self.assertEqual(result['usage']['promptTokenCount'], 123)
            self.assertEqual(result['raw_response']['modelVersion'], 'gemini-3.8-flash')
            ledger.close()

    def test_gate_missing_unknown_and_unconfirmed_account(self):
        http = MockHTTP()
        p = Gemini(dict(ENV, GEMINI_API_KEY=''), http)
        with self.assertRaises(ProviderError): p.verify_free()
        with self.assertRaises(ProviderError): p.generate({})
        self.assertEqual(http.calls, [])
        http = MockHTTP()
        p = Gemini(dict(ENV, GEMINI_MODEL='unknown'), http)
        with self.assertRaises(ProviderError): p.verify_free()
        with self.assertRaises(ProviderError): p.generate({})
        self.assertEqual(http.generations(), 0)

    def test_minimum_key_auth_and_model_metadata_gate(self):
        self.assertEqual(Gemini({}).model, 'gemini-3.5-flash-lite')
        minimal = dict(ENV)
        http = MockHTTP()
        gate = Gemini(minimal, http).verify_free()
        self.assertEqual(gate['status'], 'model_available')
        self.assertEqual(len(http.calls), 1)
        self.assertEqual(http.calls[0][0], 'GET')
        for metadata in [{}, {'name': 'models/other'},
                         {'name': 'models/gemini-3.8-flash', 'version': '001',
                          'supportedGenerationMethods': ['generateContent']},
                         {'name': 'models/gemini-3.8-flash',
                          'supportedGenerationMethods': ['generateContent', 'countTokens']}]:
            p = Gemini(minimal, MockHTTP(model=metadata))
            with self.assertRaises(ProviderError): p.verify_free()
            with self.assertRaises(ProviderError): p.generate({})

    def test_schema_executor_and_hidden_operand(self):
        arg = {'fact': 'selected', 'start': 0, 'end': 2}
        plan = {'kind': 'arithmetic', 'steps': [{'op': 'divide', 'args': [arg, {'constant': '100'}]}]}
        self.assertEqual(parse_and_execute(canonical(plan), bundle())[1]['answer'], '0.1')
        plan['steps'][0]['args'][0]['fact'] = 'full-context-only'
        self.assertEqual(parse_and_execute(canonical(plan), bundle())[1]['status'], 'invalid')
        for malformed in ['{}', 'null', '{"kind":"abstain","kind":"arithmetic"}',
                          '{"kind":"arithmetic","steps":[]}', '{"kind":"abstain","answer":10}']:
            self.assertEqual(parse_and_execute(malformed, bundle())[1]['status'], 'invalid')

    def test_full_document_and_reference_mutation_cannot_enter_request(self):
        raw = json.loads((ROOT / 'third_party/FinQA/dataset/dev.json').read_text())[:3]
        for i, row in enumerate(raw):
            changed = copy.deepcopy(row)
            changed['qa'] = {'question': row['qa']['question'], 'answer': 'GOLD_SENTINEL', 'program': 'GOLD_SENTINEL'}
            changed['annotation'] = 'GOLD_SENTINEL'
            a = convert(row, 'dev', 'dev.json', i)[0]
            b = convert(changed, 'dev', 'dev.json', i)[0]
            for dependent in (False, True):
                pa = pack(a, retrieve(a), 1200, dependent)
                pb = pack(b, retrieve(b), 1200, dependent)
                ra = request(a.question, pa, {'model': 'fixed'})
                self.assertEqual(ra, request(b.question, pb, {'model': 'fixed'}))
                self.assertNotIn('GOLD_SENTINEL', canonical(ra))
                self.assertEqual(set(ra['input']), {'question', 'evidence'})
                self.assertEqual({f['id'] for f in ra['input']['evidence']}, {f['id'] for f in pa['facts']})
                self.assertTrue(len(pa['facts']) < len(a.facts))
                # Mutate the whole document AFTER packing: transport stays identical.
                a.document.clear()
                a.document['answer'] = 'HIDDEN_FULL_CONTEXT'
                self.assertEqual(ra, request(a.question, pa, {'model': 'fixed'}))

    def test_cache_dimensions(self):
        req = request('q', bundle(), {'provider': 'gemini', 'model': 'fixed'})
        for key in ('provider', 'instructions', 'input', 'schema', 'settings'):
            changed = copy.deepcopy(req)
            changed[key] = {'changed': True}
            self.assertNotEqual(cache_key(req), cache_key(changed))

    def test_resume_no_duplicate_and_raw_preserved(self):
        http = MockHTTP()
        p = provider(http)
        req = request('q', bundle(), p.identity)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cache.sqlite'
            ledger = Ledger(path, p)
            first = ledger.predict(req, bundle())
            ledger.close()
            ledger = Ledger(path, p)
            second = ledger.predict(req, bundle())
            self.assertTrue(second['cache_hit'])
            self.assertEqual(first['raw_response'], second['raw_response'])
            self.assertEqual(http.generations(), 1)
            self.assertEqual(ledger.calls(), 1)
            # On free tier a crash after dispatch cannot bill, so the request is resent.
            interrupted = dict(req, instructions='interrupted')
            ledger.save(cache_key(interrupted), {'key': cache_key(interrupted), 'request': interrupted,
                                                 'status': 'inflight', 'attempts': [{}]})
            self.assertEqual(ledger.predict(interrupted, bundle())['status'], 'completed')
            self.assertEqual(http.generations(), 2)
            ledger.close()

    def test_retry_ceiling_and_persistent_quota_stop(self):
        for errors, expected, stop in [(['transient_server'] * 4, 3, False),
                                       (['transient_server'], 2, False),
                                       (['quota_exhausted'], 2, False),
                                       (['quota_exhausted'] * 20, 8, True),
                                       (['ambiguous_transport'], 2, False)]:
            http = MockHTTP(errors=errors)
            p = provider(http)
            req = request('q', bundle(), p.identity)
            with tempfile.TemporaryDirectory() as tmp:
                ledger = Ledger(Path(tmp) / 'cache.sqlite', p, sleep=lambda _: None)
                if stop:
                    with self.assertRaises(StopRun): ledger.predict(req, bundle())
                    with self.assertRaises(StopRun): ledger.predict(req, bundle())
                else:
                    ledger.predict(req, bundle())
                    ledger.predict(req, bundle())
                self.assertEqual(http.generations(), expected)
                ledger.close()

    def test_global_call_limit_and_response_saved_resume(self):
        http = MockHTTP()
        p = provider(http)
        req = request('q', bundle(), p.identity)
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Ledger(Path(tmp) / 'cache.sqlite', p, max_calls=1)
            first = ledger.predict(req, bundle())
            with self.assertRaises(StopRun): ledger.predict(dict(req, instructions='new'), bundle())
            first['status'] = 'response_saved'
            ledger.save(cache_key(req), first)
            self.assertEqual(ledger.predict(req, bundle())['execution']['status'], 'abstain')
            self.assertEqual(http.generations(), 1)
            ledger.close()

    def test_transport_schema_count_and_secret_redaction(self):
        http = MockHTTP()
        p = provider(http)
        self.assertIsInstance(p.count('test'), int)
        p.generate(request('q', bundle(), p.identity))
        sent = http.calls[-1][2]
        self.assertEqual(sent['generationConfig']['responseMimeType'], 'application/json')
        self.assertNotIn('tools', sent)
        self.assertNotIn('api_key', canonical(sent))
        self.assertEqual(p.clean({'echo': ENV['GEMINI_API_KEY']}), {'echo': '[REDACTED]'})

    def test_three_dev_mock_smoke_and_resume(self):
        spec = importlib.util.spec_from_file_location('api_smoke', ROOT / 'scripts/run_api_finqa.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        http = MockHTTP()
        def mock_provider():
            p = Gemini(ENV, http)
            p.identity['transport'] = 'mock'
            return p
        with tempfile.TemporaryDirectory() as tmp:
            for _ in range(2):
                module.main(mock_provider, ['--out', tmp])
            manifest = json.loads((Path(tmp) / 'manifest.json').read_text())
            results = json.loads((Path(tmp) / 'results.json').read_text())
            self.assertEqual(manifest['completed_requests'], 6)
            self.assertEqual(manifest['model_calls_this_invocation'], 0)
            self.assertEqual(manifest['cache_hits'], 6)
            self.assertEqual(http.generations(), 6)
            for entry in results:
                self.assertFalse(entry['packing']['token_count_is_estimate'])
                self.assertLessEqual(entry['packing']['token_count'], 4000)
            for result in manifest['official_scores'].values():
                self.assertEqual(result['denominator'], 3)
                self.assertEqual(result['official_execution_fraction'], 0)
