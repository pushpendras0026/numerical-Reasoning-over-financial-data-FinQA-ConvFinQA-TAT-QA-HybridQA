"""Local native Ollama chat; no cloud credentials, fallback or attestation."""
import os
from urllib.parse import urlsplit
from .core import canonical
from .providers import ProviderError, transport

SETTINGS = {'temperature': 0, 'top_p': 1, 'seed': 2626, 'num_ctx': 8192, 'num_predict': 2048}

class Ollama:
    name = 'ollama'
    counter_name = 'conservative_utf8_byte_token_upper_bound'
    count_scope = 'UTF-8 bytes as conservative token bound; NOT tokenizer counts'
    count_estimated = True

    def __init__(self, env=None, http=transport):
        env = os.environ if env is None else env
        self.base = env.get('OLLAMA_BASE_URL', '').rstrip('/')
        self.model = env.get('OLLAMA_MODEL', 'qwen2.5:7b-instruct')
        self.http = http
        self.verified = False
        self.identity = {'provider': self.name, 'model': self.model, 'api': 'native/api/chat',
                         'context_size': SETTINGS['num_ctx'], 'packing_counter': self.counter_name}

    def verify_free(self):
        url = urlsplit(self.base)
        import ipaddress
        try:
            local = url.hostname == 'localhost' or ipaddress.ip_address(url.hostname).is_private
        except (ValueError, TypeError):
            local = False
        if url.scheme != 'http' or not local or url.username or url.query or url.path:
            raise ProviderError('local_ollama_base_url_required')
        tags = self.http('GET', self.base + '/api/tags', {})
        item = next((x for x in tags.get('models', []) if x.get('name') == self.model), None)
        if not item or not item.get('digest'):
            raise ProviderError('local_model_unavailable')
        show = self.http('POST', self.base + '/api/show', {}, {'model': self.model})
        self.identity.update(digest=item['digest'], quantization=item.get('details', {}).get('quantization_level'),
                             model_info=show.get('model_info', {}), template=show.get('template'),
                             parameters=show.get('parameters'))
        self.verified = True
        return {'status': 'local_model_verified', 'model': dict(self.identity), 'paid_fallback': False}

    def count(self, text):
        return len(text.encode('utf-8'))

    def generate(self, request):
        if not self.verified:
            raise ProviderError('local_model_not_verified')
        settings = request['settings']
        messages = [{'role': 'system', 'content': request['instructions']},
                    {'role': 'user', 'content': canonical(request['input'])}]
        # Byte upper bound plus explicit template/framing allowance and reserved output.
        bound = self.count(canonical(messages)) + 512
        if bound + settings['num_predict'] > settings['num_ctx']:
            raise ProviderError('context_budget_exceeded', details={'input_upper_bound': bound,
                                'output_reserved': settings['num_predict'], 'context': settings['num_ctx']})
        raw = self.http('POST', self.base + '/api/chat', {}, {
            'model': self.model, 'messages': messages, 'stream': False,
            'format': request['schema'], 'options': settings, 'keep_alive': '10m'})
        raw['usage'] = {'input_tokens': raw.get('prompt_eval_count', 0), 'output_tokens': raw.get('eval_count', 0)}
        raw['usageDetails'] = {k: raw[k] for k in ('total_duration','load_duration','prompt_eval_duration','eval_duration') if k in raw}
        raw['usageDetails']['input_byte_upper_bound'] = bound
        if raw.get('prompt_eval_count', 0) > bound or raw.get('prompt_eval_count', 0) + settings['num_predict'] > settings['num_ctx']:
            raise ProviderError('context_bound_violated')
        return raw

    def response_text(self, raw):
        if not raw.get('done') or raw.get('done_reason') != 'stop':
            raise ProviderError('blocked_or_incomplete_output')
        return raw['message']['content']
