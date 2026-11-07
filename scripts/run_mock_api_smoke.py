"""Offline integration proof. Synthetic responses/usage; never loads real credentials."""
import importlib.util
import json
from pathlib import Path
from nrqa.core import canonical
from nrqa.providers import Gemini
from run_api_finqa import main, write

ROOT = Path(__file__).resolve().parents[1]


def run():
    spec = importlib.util.spec_from_file_location('api_test_doubles', ROOT / 'tests/test_api.py')
    test = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test)
    http = test.MockHTTP()
    def factory():
        p = Gemini(test.ENV, http)
        p.identity['transport'] = 'mock'
        return p
    out = ROOT / 'artifacts/api_mock_finqa'
    main(factory, ['--out', str(out)])
    first = json.loads((out / 'manifest.json').read_text())
    first_calls = http.generations()
    main(factory, ['--out', str(out)])
    resumed = json.loads((out / 'manifest.json').read_text())
    report = {'label': 'MOCK transport only; no real inference or measured provider token usage',
              'first_invocation_generation_calls': first['model_calls_this_invocation'],
              'resume_generation_calls': http.generations() - first_calls,
              'resume_cache_hits': resumed['cache_hits'],
              'completed_requests': resumed['completed_requests'],
              'outputs': 'six fixed abstention fixtures; not a reasoning algorithm',
              'official_scores': resumed['official_scores'], 'real_api_calls': 0,
              'token_counts': 'synthetic mock countTokens responses, not actual Gemini tokens',
              'latency': 'local mock latency only', 'spend_usd': 0}
    assert report['resume_generation_calls'] == 0 and report['resume_cache_hits'] == 6
    write(out, 'mock_verification.json', report)
    print(canonical(report))


if __name__ == '__main__':
    run()
