"""Explicit OpenAI route. No Gemini changes or automatic provider fallback."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from .core import canonical
from .providers import ProviderError, transport


SETTINGS = {'temperature': 0, 'topP': 1, 'candidateCount': 1, 'maxOutputTokens': 2048}


def local_environment(path, allowed=None):
    """Read only allowed settings as literal values; never source shell code."""
    allowed = ({'OPENAI_API_KEY', 'OPEN_AI', 'OPENAI_MODEL', 'OPENAI_FREE_CREDITS_CONFIRMED'}
               if allowed is None else set(allowed))
    values = {}
    path = Path(path)
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            match = re.fullmatch(r'\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*', line)
            if not match:
                raise ProviderError('invalid_dotenv_assignment')
            name, value = match.groups()
            if name not in allowed:
                continue
            if value[:1] in ('"', "'"):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ProviderError('invalid_dotenv_quoting')
                value = value[1:-1]
            values[name] = value
    values.update({name: os.environ[name] for name in allowed if name in os.environ})
    if not values.get('OPENAI_API_KEY') and values.get('OPEN_AI'):
        values['OPENAI_API_KEY'] = values['OPEN_AI']
    return values


class OpenAI:
    name = 'openai'
    counter_name = 'openai_responses_input_tokens_evidence_only_with_framing'
    count_scope = 'Responses input_tokens for user text with framing; excludes instructions/schema; not estimate'

    def __init__(self, env=None, http=transport):
        env = os.environ if env is None else env
        self.key = env.get('OPENAI_API_KEY', '')
        self.model = env.get('OPENAI_MODEL', '')
        self.confirmation = env.get('OPENAI_FREE_CREDITS_CONFIRMED', '')
        self.http = http
        self.verified = False
        self.identity = {'provider': self.name, 'model': self.model,
                         'api': 'responses/v1', 'output_format': 'json_object_local_schema_validation'}

    def clean(self, value):
        if isinstance(value, dict):
            return {self.clean(k): self.clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.clean(v) for v in value]
        if isinstance(value, str) and self.key:
            return value.replace(self.key, '[REDACTED]')
        return value

    def verify_free(self):
        self.verified = False
        missing = [name for name, value in [('OPENAI_API_KEY', self.key), ('OPENAI_MODEL', self.model)] if not value]
        if missing:
            raise ProviderError('missing_configuration:' + ','.join(missing))
        if not re.fullmatch(r'[A-Za-z0-9._-]+', self.model):
            raise ProviderError('invalid_openai_model')
        today = datetime.now(timezone.utc).date().isoformat()
        if self.confirmation != self.model + ':' + today:
            raise ProviderError('openai_free_credits_console_confirmation_required')
        # Model access is separate from credit/payment status. A normal project
        # key does not establish the latter; do not query undocumented billing APIs.
        metadata = self.http('GET', 'https://api.openai.com/v1/models/' + self.model,
                             {'Authorization': 'Bearer ' + self.key})
        if metadata.get('id') != self.model:
            raise ProviderError('model_unavailable')
        self.identity['version'] = metadata['id']
        self.verified = True
        return {'status': 'console_attested_and_model_available', 'model': self.identity,
                'account_check': {'method': 'operator_console_confirmation', 'checked_on_utc': today,
                    'scope': 'key-owning organization; sufficient unexpired free credits for all attempts; no paid payment method or recharge; model quota headroom',
                    'independently_verified': False},
                'paid_fallback': False, 'spending_ceiling_usd': 0,
                'source': 'https://developers.openai.com/api/docs/guides/chatgpt-api-credits'}

    def call(self, path, body):
        if not self.verified:
            raise ProviderError('free_access_not_verified')
        return self.clean(self.http('POST', 'https://api.openai.com/v1/' + path,
                                   {'Authorization': 'Bearer ' + self.key}, body))

    def count(self, text):
        raw = self.call('responses/input_tokens', {'model': self.model, 'input': text})
        count = raw.get('input_tokens')
        if type(count) is not int or count < 0:
            raise ProviderError('invalid_token_count')
        return count

    def generate(self, request):
        if request['settings'] != SETTINGS:
            raise ProviderError('unsupported_openai_generation_settings')
        return self.call('responses', {'model': self.model,
            'instructions': request['instructions'], 'input': canonical(request['input']),
            'temperature': request['settings']['temperature'], 'top_p': request['settings']['topP'],
            'max_output_tokens': request['settings']['maxOutputTokens'],
            'text': {'format': {'type': 'json_object'}}, 'store': False, 'truncation': 'disabled'})

    def response_text(self, raw):
        if raw.get('status') != 'completed' or raw.get('error'):
            raise ProviderError('blocked_or_incomplete_output')
        output = raw.get('output', [])
        if any(p.get('type') not in ('reasoning', 'message') for p in output):
            raise ProviderError('unexpected_output_item')
        messages = [p for p in output if p.get('type') == 'message']
        if (len(messages) != 1 or messages[0].get('type') != 'message' or
                messages[0].get('role') != 'assistant' or messages[0].get('status') != 'completed'):
            raise ProviderError('invalid_response_parts')
        parts = messages[0].get('content', [])
        if not parts or any(p.get('type') != 'output_text' or not isinstance(p.get('text'), str) for p in parts):
            raise ProviderError('blocked_or_invalid_output')
        return ''.join(p['text'] for p in parts)
