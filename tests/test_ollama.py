import unittest
from nrqa.ollama_provider import Ollama, SETTINGS
from nrqa.providers import ProviderError

class LocalProviderTests(unittest.TestCase):
    def provider(self):
        self.calls=[]
        def http(method,url,headers,body=None):
            self.calls.append((url,body))
            if url.endswith('/tags'):return {'models':[{'name':'qwen2.5:7b-instruct','digest':'fixed','details':{'quantization_level':'Q4_K_M'}}]}
            if url.endswith('/show'):return {'model_info':{}}
            return {'model':'qwen2.5:7b-instruct','done':True,'done_reason':'stop','message':{'content':'{"kind":"abstain"}'},'eval_count':4,'prompt_eval_count':20}
        p=Ollama({'OLLAMA_BASE_URL':'http://127.0.0.1:11434'},http);p.verify_free();return p
    def test_native_schema_and_metadata(self):
        p=self.provider();schema={'type':'object'}
        raw=p.generate({'instructions':'use evidence','input':{'evidence':[]},'schema':schema,'settings':SETTINGS})
        self.assertEqual(self.calls[-1][1]['format'],schema)
        self.assertIs(self.calls[-1][1]['stream'],False)
        self.assertEqual(p.identity['digest'],'fixed')
        self.assertEqual(raw['usage']['output_tokens'],4)
    def test_overflow_refused_before_dispatch(self):
        p=self.provider()
        with self.assertRaisesRegex(ProviderError,'context_budget_exceeded'):
            p.generate({'instructions':'x'*8192,'input':{},'schema':{},'settings':SETTINGS})
        self.assertEqual(len(self.calls),2)
    def test_cloud_url_refused(self):
        with self.assertRaises(ProviderError):Ollama({'OLLAMA_BASE_URL':'https://example.com'}).verify_free()
    def test_incomplete_output(self):
        p=self.provider()
        with self.assertRaises(ProviderError):p.response_text({'done':True,'done_reason':'length'})
