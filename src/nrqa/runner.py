"""Persistent single-process request ledger. Commit dispatch before any remote call."""
import json
import random
import sqlite3
import time
import fcntl
import os

STOP_DISPATCH = False
from .core import canonical
from . import grounded
from .model import cache_key, parse_and_execute, visible_evidence, validate
from .providers import ProviderError


class StopRun(Exception):
    def __init__(self, code, details=None):
        super().__init__(code)
        self.details = details or {}


class Ledger:
    def __init__(self, path, provider, max_calls=18, sleep=time.sleep, generation_attempts=3):
        self.generation_attempts = generation_attempts
        self.lock = open(str(path) + '.lock', 'a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise StopRun('run_already_active') from None
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS requests (key TEXT PRIMARY KEY, record TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS counts (key TEXT PRIMARY KEY, value INTEGER NOT NULL)')
        self.provider, self.max_calls, self.sleep = provider, max_calls, sleep
        self.cache_hits = 0
        self.count_calls = 0
        self.rate_waits = 0

    def close(self):
        self.db.close()
        self.lock.close()

    def get(self, key):
        row = self.db.execute('SELECT record FROM requests WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, key, value):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO requests VALUES (?,?)', (key, canonical(value)))

    def calls(self):
        return sum(len(json.loads(row[0])['attempts']) for row in self.db.execute('SELECT record FROM requests'))

    def outcome_counts(self):
        records = [json.loads(row[0]) for row in self.db.execute('SELECT record FROM requests')]
        uncertain = {'inflight', 'quota_exhausted', 'ambiguous_transport', 'ambiguous_response'}
        return {'successful_requests': sum(r['status'] == 'completed' for r in records),
                'failed_requests': sum(r['status'] == 'failed' for r in records),
                'uncertain_requests': sum(r['status'] in uncertain for r in records)}

    def count(self, text):
        key = cache_key({'identity': self.provider.identity, 'text': text, 'method': 'countTokens'})
        row = self.db.execute('SELECT value FROM counts WHERE key=?', (key,)).fetchone()
        if row:
            return row[0]
        if self.count_calls >= 1000 and not getattr(self.provider, 'count_estimated', False):
            raise StopRun('token_count_call_limit')
        self.count_calls += 1
        try:
            value = self.provider.count(text)
        except ProviderError as error:
            error.details = dict(error.details, attempt_number=1, logical_request_id=key,
                                 request_kind="token_count")
            raise
        with self.db:
            self.db.execute('INSERT INTO counts VALUES (?,?)', (key, value))
        return value

    def predict(self, request, packed):
        if request.get('provider') != self.provider.identity:
            raise StopRun('request_provider_identity_mismatch')
        key = cache_key(request)
        record = self.get(key)
        if record and record['status'] == 'completed':
            self.cache_hits += 1
            return dict(record, cache_hit=True)
        if record and record['status'] in ('inflight', 'quota_exhausted', 'ambiguous_transport', 'ambiguous_response'):
            # Free-tier only: re-sending cannot bill, so an unresolved request is simply resent.
            record['status'] = 'ready'
        if record and record['status'] == 'response_saved':
            return self.finish(key, record, packed)
        if record and record['status'] == 'failed':
            self.cache_hits += 1
            return dict(record, cache_hit=True)
        record = record or {'key': key, 'request': request, 'attempts': [], 'status': 'ready'}
        while len(record['attempts']) < self.generation_attempts:
            if STOP_DISPATCH or time.time() >= float(os.environ.get('NRQA_DISPATCH_DEADLINE', 'inf')):
                raise StopRun('dispatch_deadline_or_signal')
            if self.calls() >= self.max_calls:
                raise StopRun('generation_call_limit')
            attempt = {'started_unix': time.time(), 'status': 'inflight',
                       'attempt_number': len(record['attempts']) + 1, 'logical_request_id': key,
                       'provider_model': dict(self.provider.identity)}
            record['attempts'].append(attempt)
            record['status'] = 'inflight'
            self.save(key, record)
            start = time.monotonic()
            try:
                raw = self.provider.generate(request)
                attempt.update(status='response', latency_seconds=time.monotonic() - start,
                               usage=raw.get('usageMetadata', raw.get('usage', {})),
                               usage_details=raw.get('usageDetails', {}))
                self.rate_waits = 0
                record.update(raw_response=raw, status='response_saved')
                self.save(key, record)  # Preserve raw output even if local parsing is interrupted.
                return self.finish(key, record, packed)
            except ProviderError as error:
                attempt.update(status=error.code, latency_seconds=time.monotonic() - start,
                               retry_after_seconds=error.retry_after)
                error.details = dict(error.details, attempt_number=len(record['attempts']), logical_request_id=key)
                record['error'] = error.code
                record['error_details'] = error.details
                attempt['error_details'] = error.details
                record['status'] = error.code if error.code in ('quota_exhausted', 'ambiguous_transport', 'ambiguous_response') else 'failed'
                if error.code == 'quota_exhausted' and 'PerDay' not in str(error.details.get('quota_id', '')) and error.retry_after <= 120:
                    # Per-minute limit: the request was refused, so wait without spending an attempt.
                    record['attempts'].pop()
                    record['status'] = 'ready'
                    self.save(key, record)
                    self.rate_waits += 1
                    if self.rate_waits > 6:  # Waiting is not clearing it: treat as a daily limit.
                        raise StopRun('quota_exhausted', error.details) from None
                    self.sleep(max(error.retry_after, 30) + 1)
                    continue
                if error.code in ('transient_server', 'ambiguous_transport') and len(record['attempts']) < self.generation_attempts and error.retry_after <= 60:
                    record['status'] = 'retryable'
                self.save(key, record)
                if record['status'] in ('quota_exhausted', 'ambiguous_transport', 'ambiguous_response'):
                    raise StopRun(error.code, error.details) from None
                if record['status'] == 'retryable':
                    delay = min(60, max(error.retry_after, 2 ** len(record['attempts']) + random.random()))
                    self.sleep(delay)
                    continue
                return dict(record, cache_hit=False)
        record['status'] = 'failed'
        self.save(key, record)
        return dict(record, cache_hit=False)

    def finish(self, key, record, packed):
        raw = record['raw_response']
        try:
            text = self.provider.response_text(raw)
            plan, result = (grounded.parse(text, packed) if record['request']['schema'] == grounded.SCHEMA else grounded.parse_direct(text) if record['request']['schema'] == grounded.DIRECT_SCHEMA else parse_and_execute(text, packed))
            if plan is not None:
                try: validate(plan, record['request']['schema'])
                except ValueError: plan, result = None, {'status':'invalid','tokens':['EOF'],'error':'Disabled tool or schema violation'}
            record.update(parsed_prediction=plan, execution=result)
        except ProviderError as error:
            record.update(parsed_prediction=None, execution={'status': 'invalid', 'tokens': ['EOF'], 'error': error.code})
        record.update(status='completed', usage=raw.get('usageMetadata', raw.get('usage', raw.get('usageDetails', {}))),
                      usage_details=raw.get('usageDetails', {}),
                      resolved_model=raw.get('modelVersion', raw.get('model')), cache_hit=False)
        self.save(key, record)
        return record


class ProviderCounter:
    name = 'gemini_countTokens_evidence_serialization'
    estimated = False

    def __init__(self, ledger):
        self.ledger = ledger
        self.name = getattr(ledger.provider, 'counter_name', self.name)
        self.estimated = getattr(ledger.provider, 'count_estimated', False)

    def count(self, text):
        # Budget the exact evidence serialization sent to the provider, rather
        # than charging for provenance metadata that stays in local artifacts.
        return self.ledger.count(canonical(visible_evidence(json.loads(text))))
