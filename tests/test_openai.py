from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nrqa.core import canonical
from nrqa.model import request
from nrqa.openai_provider import OpenAI, SETTINGS, local_environment
from nrqa.providers import ProviderError
from nrqa.runner import Ledger, StopRun

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'synthetic-nonreasoning-snapshot'
ENV = {'OPENAI_API_KEY': 'synthetic-openai-secret', 'OPENAI_MODEL': MODEL,
       'OPENAI_FREE_CREDITS_CONFIRMED': MODEL + ':' + datetime.now(timezone.utc).date().isoformat()}


class HTTP:
    def __init__(self, quota=False):
        self.calls = []
        self.quota = quota

    def __call__(self, method, url, headers, body=None):
        if headers != {'Authorization': 'Bearer ' + ENV['OPENAI_API_KEY']}:
            raise AssertionError('incorrect authentication')
        self.calls.append((method, url, body))
        if method == 'GET':
            return {'id': MODEL}
        if url.endswith('/input_tokens'):
            return {'input_tokens': (len(body['input'].encode()) + 3) // 4 + 3}
        if self.quota:
            raise ProviderError('quota_exhausted')
        return {'model': MODEL, 'status': 'completed', 'output': [
            {'type': 'message', 'role': 'assistant', 'status': 'completed', 'content': [
                {'type': 'output_text', 'text': canonical({'kind': 'abstain'})}]}],
                'usage': {'input_tokens': 123, 'output_tokens': 7}}

    def generations(self):
        return sum(url.endswith('/responses') for _, url, _ in self.calls)


class OpenAIIntegration(unittest.TestCase):
    def test_literal_env_loader_no_execution_or_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            path = Path(tmp) / '.env'
            path.write_text("OPEN_AI='synthetic-file-key'\nOPENAI_MODEL=from-file\nOTHER=ignored\n")
            self.assertEqual(local_environment(path)['OPENAI_API_KEY'], 'synthetic-file-key')
            self.assertNotIn('OTHER', local_environment(path))
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-process-key'}):
                self.assertEqual(local_environment(path)['OPENAI_API_KEY'], 'synthetic-process-key')
            path.write_text('OPENAI_API_KEY=$(touch unwanted)\n')
            self.assertEqual(local_environment(path)['OPENAI_API_KEY'], '$(touch unwanted)')
            path.write_text('not an assignment\n')
            with self.assertRaises(ProviderError): local_environment(path)

    def test_gemini_local_configuration_is_isolated_and_literal(self):
        allowed = {'GEMINI_API_KEY', 'GEMINI_MODEL', 'GEMINI_FREE_TIER_CONFIRMED'}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            path = Path(tmp) / '.env'
            path.write_text("GEMINI_API_KEY='synthetic-google-key'\nOPENAI_API_KEY=excluded\n")
            values = local_environment(path, allowed)
            self.assertEqual(values, {'GEMINI_API_KEY': 'synthetic-google-key'})
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'synthetic-override'}):
                self.assertEqual(local_environment(path, allowed)['GEMINI_API_KEY'], 'synthetic-override')
            path.write_text('GEMINI_API_KEY=$(touch unwanted)\n')
            self.assertEqual(local_environment(path, allowed)['GEMINI_API_KEY'], '$(touch unwanted)')

    def test_unverified_account_never_dispatches(self):
        for env in [dict(ENV, OPENAI_API_KEY=''), dict(ENV, OPENAI_MODEL=''),
                    dict(ENV, OPENAI_FREE_CREDITS_CONFIRMED=''),
                    dict(ENV, OPENAI_FREE_CREDITS_CONFIRMED=MODEL + ':2000-01-01'),
                    dict(ENV, OPENAI_FREE_CREDITS_CONFIRMED='other:' + datetime.now(timezone.utc).date().isoformat())]:
            http = HTTP()
            provider = OpenAI(env, http)
            with self.assertRaises(ProviderError): provider.verify_free()
            with self.assertRaises(ProviderError): provider.count('text')
            self.assertEqual(http.calls, [])

    def test_usage_packed_request_and_quota_resume(self):
        bundle = {'facts': [{'id': 'selected', 'raw': '10', 'unit': 'unknown'}]}
        for quota in (False, True):
            http = HTTP(quota)
            p = OpenAI(ENV, http)
            self.assertFalse(p.verify_free()['account_check']['independently_verified'])
            req = request('q', bundle, p.identity, SETTINGS)
            with tempfile.TemporaryDirectory() as tmp:
                ledger = Ledger(Path(tmp) / 'cache.sqlite', p, sleep=lambda _: None)
                try:
                    if quota:
                        with self.assertRaises(StopRun): ledger.predict(req, bundle)
                        with self.assertRaises(StopRun): ledger.predict(req, bundle)
                    else:
                        result = ledger.predict(req, bundle)
                        self.assertEqual(result['usage'], {'input_tokens': 123, 'output_tokens': 7})
                        self.assertEqual(result['resolved_model'], MODEL)
                        self.assertTrue(ledger.predict(req, bundle)['cache_hit'])
                        sent = http.calls[-1][2]
                        self.assertEqual(json.loads(sent['input']), req['input'])
                        self.assertEqual(sent['instructions'], req['instructions'])
                        self.assertFalse(sent['store'])
                        self.assertNotIn('tools', sent)
                        self.assertEqual(p.clean(ENV['OPENAI_API_KEY']), '[REDACTED]')
                    self.assertEqual(http.generations(), 8 if quota else 1)  # Rate waits are bounded.
                finally:
                    ledger.close()

    def test_refusal_incomplete_and_unexpected_parts(self):
        p = OpenAI(ENV)
        for raw in [{'status': 'incomplete'}, {'status': 'completed', 'output': []},
                    {'status': 'completed', 'output': [{'type': 'message', 'role': 'assistant',
                     'status': 'completed', 'content': [{'type': 'refusal', 'refusal': 'refused'}]}]}]:
            with self.assertRaises(ProviderError): p.response_text(raw)

    def test_three_fixed_questions_two_packers_and_cached_resume(self):
        spec = importlib.util.spec_from_file_location('openai_smoke', ROOT / 'scripts/run_api_finqa.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        http = HTTP()
        def factory():
            p = OpenAI(ENV, http)
            p.identity['transport'] = 'mock'
            return p
        with tempfile.TemporaryDirectory() as tmp:
            for _ in range(2): module.main(factory, ['--out', tmp], settings=SETTINGS)
            manifest = json.loads((Path(tmp) / 'manifest.json').read_text())
            results = json.loads((Path(tmp) / 'results.json').read_text())
            self.assertEqual(manifest['cache_hits'], 6)
            self.assertEqual(manifest['model_calls_this_invocation'], 0)
            self.assertEqual(http.generations(), 6)
            self.assertEqual({canonical(row['request']['settings']) for row in results}, {canonical(SETTINGS)})
            self.assertTrue(all(row['packing']['token_count'] <= 4000 for row in results))
            self.assertTrue(all(not row['packing']['token_count_is_estimate'] for row in results))
            self.assertTrue(all(row['prediction']['usage']['input_tokens'] == 123 for row in results))
