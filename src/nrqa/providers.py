"""Gemini Developer API. API-key auth; explicit console eligibility gate; no fallback."""
from datetime import datetime, timezone
import json
import os
import socket
import re
from urllib.parse import urlsplit, parse_qsl
import time
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError
from .core import canonical


class ProviderError(Exception):
    def __init__(self, code, retry_after=0, details=None):
        super().__init__(code)  # Never include URLs, remote bodies or credentials.
        self.code, self.retry_after = code, retry_after
        self.details = details or {}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def safe_message(value, url, headers):
    # Redact known credentials and ALL query values, regardless of parameter name.
    secrets = [v for _, v in parse_qsl(urlsplit(url).query, keep_blank_values=True)]
    secrets.extend(part.partition('=')[2] for part in urlsplit(url).query.split('&'))
    for name, value_header in headers.items():
        if name.lower() in ('authorization', 'x-goog-api-key', 'api-key', 'x-api-key'):
            secrets.extend([value_header, value_header.removeprefix('Bearer ')])
    text = str(value)
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = text.replace(secret, '[REDACTED]')
    text = re.sub(r'https?://[^\s"<>]+', '[URL REDACTED]', text)
    text = re.sub(r'(?:AIza[\w-]{15,}|sk-[\w-]{8,})', '[REDACTED]', text)
    text = re.sub(r'(?i)(?:api[_-]?key|authorization|bearer)[= :]+[^\r\n,;}]+', '[REDACTED]', text)
    text = re.sub(r'projects/[A-Za-z0-9_-]+', 'projects/[REDACTED]', text)
    return text[:1500]


def error_context(error, method, url, headers, stage, start, response=None):
    reason = getattr(error, 'reason', error)
    timeout = isinstance(reason, (TimeoutError, socket.timeout))
    detail = {'method': method, 'endpoint_path': safe_message(urlsplit(url).path, url, headers),
              'host': urlsplit(url).hostname, 'operation': urlsplit(url).path.rsplit('/', 1)[-1],
              'stage': stage, 'exception_type': type(error).__name__,
              'reason_type': type(reason).__name__,
              'safe_message': safe_message(reason, url, headers),
              'timeout_category': ('response_read' if stage == 'response_read' else
                                   'connection_or_response_headers_unknown') if timeout else 'not_identified',
              'elapsed_seconds': time.monotonic() - start,
              'dispatch_outcome': 'not_dispatched' if stage == 'before_dispatch' else 'unknown'}
    if response is not None:
        detail['http_status'] = getattr(response, 'status', getattr(response, 'code', None))
        response_headers = getattr(response, 'headers', {}) or {}
        request_id = response_headers.get('x-request-id') or response_headers.get('x-goog-request-id')
        if request_id:
            detail['request_id'] = safe_message(request_id, url, headers)
    return detail


def redacted_error(error, method, url, headers):
    detail = {}
    try:
        payload = json.loads(error.read(16384)); remote = payload.get('error', {})
        if isinstance(remote, dict):
            detail['provider_error'] = {k: safe_message(remote[k], url, headers)
                                        for k in ('code', 'status', 'type', 'param', 'message') if k in remote}
    except (ValueError, UnicodeError, OSError):
        detail['body_format'] = 'non_json_or_unreadable; body not retained'
    return detail


def transport(method, url, headers, body=None, timeout=60):
    start = time.monotonic()
    stage = 'before_dispatch'
    response = None
    try:
        req = Request(url, data=None if body is None else canonical(body).encode(),
                      headers=dict(headers, **{'Content-Type': 'application/json'}), method=method)
        opener = build_opener(NoRedirect)
        # urllib.open includes connection, TLS, sending, and waiting for headers.
        # A failure here cannot establish how far dispatch progressed.
        stage = 'connection_or_response_headers_unknown'
        with opener.open(req, timeout=timeout) as response:
            stage = 'response_read'
            content = response.read()
            stage = 'response_decode'
            return json.loads(content)
    except HTTPError as error:
        detail = error_context(error, method, url, headers, 'http_error_response', start, error)
        detail.update(redacted_error(error, method, url, headers))
        detail['elapsed_seconds'] = time.monotonic() - start
        wait = error.headers.get('Retry-After', '0')
        if wait.isdigit():
            wait = int(wait)
        else:
            try:
                wait = max(0, int(parsedate_to_datetime(wait).timestamp() - time.time()) + 1)
            except (ValueError, TypeError, OverflowError):
                wait = 60
        code = ('quota_exhausted' if error.code in (402, 429) else
                'transient_server' if 500 <= error.code <= 599 else 'http_' + str(error.code))
        raise ProviderError(code, wait, detail) from None
    except (URLError, TimeoutError, socket.timeout, OSError) as error:
        raise ProviderError('ambiguous_transport', details=error_context(
            error, method, url, headers, stage, start, response)) from None
    except (ValueError, UnicodeError) as error:
        raise ProviderError('ambiguous_response', details=error_context(
            error, method, url, headers, stage, start, response)) from None


class Gemini:
    name = 'gemini'
    # Reviewed against Google's pricing page 2026-11-06. Unknown models fail closed.
    FREE_MODELS = {'gemini-3.8-flash'}

    def __init__(self, env=None, http=transport):
        env = os.environ if env is None else env
        self.key = env.get('GEMINI_API_KEY', '')
        self.model = env.get('GEMINI_MODEL', 'gemini-3.8-flash')
        # Operator confirmation is policy evidence, NOT an authentication token.
        # It covers the project owning THIS key, billing disabled, and nonzero
        # free quota for THIS model. Never infer eligibility from public pricing.
        self.free_confirmation = env.get('GEMINI_FREE_TIER_CONFIRMED', '')
        self.http = http
        self.identity = {'provider': self.name, 'model': self.model, 'api': 'v1beta'}
        self.verified = False

    def clean(self, value):
        # Defense in depth for raw success responses (including echoed strings).
        if isinstance(value, dict):
            return {self.clean(k): self.clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.clean(v) for v in value]
        if isinstance(value, str):
            for secret in (self.key,):
                if secret:
                    value = value.replace(secret, '[REDACTED]')
        return value

    def verify_free(self):
        self.verified = False
        missing = [name for name, val in [('GEMINI_API_KEY', self.key),
            ('GEMINI_MODEL', self.model)] if not val]
        if missing:
            raise ProviderError('missing_configuration:' + ','.join(missing))
        if not re.fullmatch(r'[A-Za-z0-9._-]+', self.model):
            raise ProviderError('invalid_gemini_model')
        if self.model not in self.FREE_MODELS:
            raise ProviderError('model_not_reviewed_for_free_tier')
        checked_on = datetime.now(timezone.utc).date().isoformat()
        if self.free_confirmation != f'{self.model}:{checked_on}':
            raise ProviderError('free_tier_console_confirmation_required')
        model = self.http('GET', self.base(), {'x-goog-api-key': self.key})
        if (model.get('name') != 'models/' + self.model or
                not {'generateContent', 'countTokens'}.issubset(model.get('supportedGenerationMethods', []))):
            raise ProviderError('model_unavailable')
        if not model.get('version'):
            raise ProviderError('missing_model_version')
        self.identity['version'] = model['version']
        self.verified = True
        return {'status': 'console_attested_and_model_available',
                'account_check': {'method': 'operator_console_confirmation', 'checked_on_utc': checked_on,
                                 'scope': 'owning project of configured key; Free tier; billing disabled; nonzero model quota',
                                 'independently_verified': False},
                'model': self.identity, 'basis': 'console attestation plus authenticated models.get; quota may change',
                'pricing_source': 'https://ai.google.dev/gemini-api/docs/pricing',
                'reviewed_on': '2026-11-06', 'paid_fallback': False, 'spending_ceiling_usd': 0}

    def base(self):
        return 'https://generativelanguage.googleapis.com/v1beta/models/' + self.model

    def call(self, method, body):
        if not self.verified:
            raise ProviderError('free_access_not_verified')
        return self.clean(self.http('POST', self.base() + ':' + method,
                                   {'x-goog-api-key': self.key}, body))

    def count(self, text):
        raw = self.call('countTokens', {'contents': [{'role': 'user', 'parts': [{'text': text}]}]})
        count = raw.get('totalTokens')
        if type(count) is not int or count < 0:
            raise ProviderError('invalid_token_count')
        return count

    def generate(self, request):
        if not self.verified:
            raise ProviderError('free_access_not_verified')
        return self.call('generateContent', {
            'systemInstruction': {'parts': [{'text': request['instructions']}]},
            'contents': [{'role': 'user', 'parts': [{'text': canonical(request['input'])}]}],
            'generationConfig': dict(request['settings'], responseMimeType='application/json',
                                      responseJsonSchema=request['schema'])})

    def response_text(self, raw):
        candidates = raw.get('candidates', [])
        if len(candidates) != 1 or candidates[0].get('finishReason') != 'STOP':
            raise ProviderError('blocked_or_incomplete_output')
        parts = candidates[0].get('content', {}).get('parts', [])
        if not parts or any('text' not in p or p.get('thought') for p in parts):
            raise ProviderError('invalid_response_parts')
        return ''.join(p['text'] for p in parts)
