import io
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from nrqa.providers import transport,ProviderError
from nrqa.openai_provider import OpenAI

class Diagnostics(unittest.TestCase):
    def test_redacted_404_and_retry_after(self):
        body={'error':{'status':'NOT_FOUND','message':'models/gemini-2.5-flash not supported; synthetic-secret; https://example.com?key=secret; projects/123456789'}}
        error=HTTPError('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:countTokens',404,'Not Found',{'Retry-After':'3','x-request-id':'req-fixture'},io.BytesIO(json.dumps(body).encode()))
        with patch('nrqa.providers.build_opener') as opener:
            opener.return_value.open.side_effect=error
            with self.assertRaises(ProviderError) as ctx:transport('POST',error.url,{'x-goog-api-key':'synthetic-secret'}, {})
        caught=ctx.exception;serialized=json.dumps(caught.details)
        self.assertEqual(caught.code,'http_404');self.assertEqual(caught.retry_after,3)
        self.assertIn('NOT_FOUND',serialized);self.assertIn('countTokens',serialized)
        self.assertNotIn('synthetic-secret',serialized);self.assertNotIn('123456789',serialized);self.assertNotIn('example.com',serialized)
    def test_responses_reasoning_item_before_message(self):
        p=OpenAI({})
        raw={'status':'completed','output':[{'type':'reasoning','summary':[]},{'type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':'{}'}]}]}
        self.assertEqual(p.response_text(raw),'{}')
    def test_diagnostics_persist_in_ledger(self):
        from nrqa.experiment import Mock
        from nrqa.model import request
        from nrqa.runner import Ledger
        class Failed(Mock):
            def generate(self,request):raise ProviderError('http_404',details={'http_status':404,'provider_error':{'status':'NOT_FOUND'}})
        provider=Failed();bundle={'facts':[]}
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp)/'cache.sqlite',provider)
            record=ledger.predict(request('q',bundle,provider.identity),bundle)
            self.assertEqual(record['error_details']['provider_error']['status'],'NOT_FOUND')
            self.assertTrue(ledger.predict(request('q',bundle,provider.identity),bundle)['cache_hit'])
            ledger.close()

    def test_transport_stage_timeout_and_redaction(self):
        from urllib.error import URLError
        from unittest.mock import MagicMock
        url = 'https://example.test/v1/models/mock:generateContent?secret=hidden-query'
        headers = {'Authorization': 'Bearer synthetic-secret'}
        for reading in (False, True):
            with self.subTest(reading=reading), patch('nrqa.providers.build_opener') as opener:
                error = TimeoutError('timed out synthetic-secret hidden-query https://example.test/?key=hidden-query')
                if reading:
                    response = MagicMock(status=200, headers={'x-request-id': 'fixture-id'})
                    response.read.side_effect = error
                    opener.return_value.open.return_value.__enter__.return_value = response
                else:
                    opener.return_value.open.side_effect = URLError(error)
                with self.assertRaises(ProviderError) as ctx:
                    transport('POST', url, headers, {})
                detail = ctx.exception.details
                self.assertEqual(ctx.exception.code, 'ambiguous_transport')
                self.assertEqual(detail['stage'], 'response_read' if reading else 'connection_or_response_headers_unknown')
                self.assertEqual(detail['reason_type'], 'TimeoutError')
                self.assertGreaterEqual(detail['elapsed_seconds'], 0)
                self.assertEqual(detail['dispatch_outcome'], 'unknown')
                for secret in ('synthetic-secret', 'hidden-query', 'Authorization'):
                    self.assertNotIn(secret, json.dumps(detail))
                self.assertNotIn('?', detail['endpoint_path'])
                if reading:
                    self.assertEqual(detail['http_status'], 200)
                    self.assertEqual(detail['request_id'], 'fixture-id')

    def test_before_dispatch_and_invalid_response(self):
        from unittest.mock import MagicMock
        with patch('nrqa.providers.Request', side_effect=ValueError('invalid request')), patch('nrqa.providers.build_opener') as opener:
            with self.assertRaises(ProviderError) as ctx:
                transport('POST', 'https://example.test/v1', {}, {})
            self.assertEqual(ctx.exception.details['stage'], 'before_dispatch')
            self.assertEqual(ctx.exception.details['dispatch_outcome'], 'not_dispatched')
            opener.assert_not_called()
        with patch('nrqa.providers.build_opener') as opener:
            response = MagicMock(status=200, headers={'x-goog-request-id': 'fixture'})
            response.read.return_value = b'not json'
            opener.return_value.open.return_value.__enter__.return_value = response
            with self.assertRaises(ProviderError) as ctx:
                transport('POST', 'https://example.test/v1', {}, {})
            self.assertEqual(ctx.exception.code, 'ambiguous_response')
            self.assertEqual(ctx.exception.details['stage'], 'response_decode')
            self.assertEqual(ctx.exception.details['request_id'], 'fixture')

    def test_retry_then_uncertain_manifest_and_resume(self):
        from nrqa.experiment import Mock, freeze, run, ROOT
        from nrqa.runner import Ledger, StopRun
        class Failed(Mock):
            calls = 0
            def generate(self, request):
                self.calls += 1
                if self.calls == 1:
                    raise ProviderError('transient_server', details={'http_status': 503})
                raise ProviderError('ambiguous_transport', details={'stage': 'connection_or_response_headers_unknown'})
        provider = Failed()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            frozen = tmp/'frozen.json'
            freeze(ROOT/'experiments/smoke.json', frozen)
            with patch('nrqa.runner.time.sleep'):
                # Constructor default sleep is already bound; replace only this mock run's sleep.
                original = Ledger.__init__
                def init(ledger, *args, **kwargs):
                    original(ledger, *args, **kwargs)
                    ledger.sleep = lambda _: None
                with patch.object(Ledger, '__init__', init):
                    result = run(frozen, tmp/'run', 'mock', lambda: provider)
            self.assertEqual(provider.calls, 2)
            self.assertEqual(result['model_calls'], 2)
            self.assertEqual(result['completed_requests'], 0)
            self.assertEqual(result['successful_requests'], 0)
            self.assertEqual(result['failed_requests'], 0)
            self.assertEqual(result['uncertain_requests'], 1)
            detail = result['error_details']
            self.assertEqual(detail['attempt_number'], 2)
            self.assertEqual(detail['stage'], 'connection_or_response_headers_unknown')
            ledger = Ledger(tmp/'run/cache.sqlite', provider)
            record = ledger.get(detail['logical_request_id'])
            self.assertNotIn('raw_response', record)
            self.assertEqual([a['attempt_number'] for a in record['attempts']], [1, 2])
            with self.assertRaises(StopRun) as ctx:
                ledger.predict(record['request'], {})
            self.assertEqual(ctx.exception.details, detail)
            self.assertEqual(provider.calls, 2)
            ledger.close()

    def test_terminal_http_error_reaches_manifest(self):
        from nrqa.experiment import Mock, freeze, run, ROOT
        class Failed(Mock):
            def generate(self, request):
                raise ProviderError('http_404', details={'http_status': 404, 'request_id': 'fixture'})
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            freeze(ROOT/'experiments/smoke.json', tmp/'frozen.json')
            result = run(tmp/'frozen.json', tmp/'run', 'mock', Failed)
            self.assertEqual(result['error_details']['http_status'], 404)
            self.assertEqual(result['error_details']['request_id'], 'fixture')
            self.assertEqual(result['error_details']['attempt_number'], 1)
            self.assertEqual(result['successful_requests'], 0)
            self.assertEqual(result['failed_requests'], 1)
            self.assertEqual(result['uncertain_requests'], 0)

    def test_count_error_has_logical_identity(self):
        from nrqa.experiment import Mock
        from nrqa.runner import Ledger
        class Failed(Mock):
            def count(self, text):
                raise ProviderError('ambiguous_transport', details={'stage': 'response_read'})
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Ledger(Path(tmp)/'cache.sqlite', Failed())
            with self.assertRaises(ProviderError) as ctx:
                ledger.count('fixture')
            self.assertEqual(ctx.exception.details['request_kind'], 'token_count')
            self.assertEqual(ctx.exception.details['attempt_number'], 1)
            self.assertEqual(len(ctx.exception.details['logical_request_id']), 64)
            ledger.close()
