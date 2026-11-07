"""Exactly three predeclared dev questions, two packers, one provider/model."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from nrqa.core import canonical, pack, retrieve, EstimatedTokens
from nrqa.finqa import convert, VERSION
from nrqa.model import request, cache_key, SETTINGS, INSTRUCTIONS, SCHEMA
from nrqa.providers import Gemini, ProviderError
from nrqa.runner import Ledger, ProviderCounter, StopRun
from nrqa.evaluation import score

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'FinQA/dataset/dev.json'
CONFIG = ROOT / 'experiments/finqa_api_smoke.json'


def write(out, name, value):
    target = out / name
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(canonical(value) + '\n')
    temporary.replace(target)


def main(provider_factory=Gemini, argv=None, settings=None, default_out=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--out', type=Path, default=default_out or ROOT / 'artifacts/api_finqa')
    args = parser.parse_args(argv)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text())
    raw = json.loads(SOURCE.read_text())
    indexed = {row['id']: (i, row) for i, row in enumerate(raw)}
    examples = [convert(indexed[qid][1], 'dev', '../FinQA/dataset/dev.json', indexed[qid][0])[0]
                for qid in config['ids']]
    provider = provider_factory()
    settings = SETTINGS if settings is None else settings
    mock = provider.identity.get('transport') == 'mock'
    manifest = {'label': 'three-question development smoke; no improvement inference',
                'dataset_revision': VERSION, 'split': 'dev', 'source_count': len(raw),
                'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'config': config, 'settings': settings, 'instructions': INSTRUCTIONS, 'schema': SCHEMA,
                'started_unix': time.time(), 'model': provider.identity, 'model_calls': 0,
                'status': 'prepared_only', 'official_scores': None}
    if mock:
        manifest['label'] = 'MOCK transport engineering smoke; NOT model predictions or measured token usage'
    # Freeze experiment before dispatch. Resuming with changed inputs/config is refused.
    contract = cache_key({k: manifest[k] for k in ('dataset_revision', 'source_sha256', 'config', 'settings', 'instructions', 'schema')})
    previous = out / 'manifest.json'
    old = json.loads(previous.read_text()) if previous.exists() else None
    if old and old['contract'] != contract:
        raise SystemExit('Run configuration changed; select a new output directory')
    manifest['contract'] = contract
    prepared = []
    for example in examples:
        for variant in ('ordinary', 'dependency'):
            bundle = pack(example, retrieve(example), config['evidence_cap'], variant == 'dependency')
            prepared.append({'id': example.id, 'variant': variant, 'packing': bundle,
                             'request': request(example.question, bundle, provider.identity, settings),
                             'label': 'PREPARATION ONLY; estimated tokens; not sent to model'})
    write(out, 'prepared_inputs.json', prepared)
    if args.prepare_only:
        write(out, 'manifest.json', manifest)
        print(canonical({'status': manifest['status'], 'prepared_requests': len(prepared), 'model_calls': 0}))
        return
    try:
        manifest['free_access'] = provider.verify_free()
    except ProviderError as error:
        manifest.update(status='blocked_before_inference', error=error.code, error_details=error.details)
        write(out, 'manifest.json', manifest)
        print(canonical({'status': manifest['status'], 'error': error.code, 'model_calls': 0}))
        return
    # Pin provider metadata across restarts as well as across the two variants.
    if old and old.get('free_access') and old['free_access']['model'] != provider.identity:
        raise SystemExit('Model metadata changed; refuse to mix this comparison')
    manifest['model'] = provider.identity
    manifest['status'] = 'running'
    write(out, 'manifest.json', manifest)
    ledger = Ledger(out / 'cache.sqlite', provider, max_calls=config['max_generation_calls'])
    initial_calls = ledger.calls()
    outputs, stop = [], None
    try:
        for example in examples:
            for variant in ('ordinary', 'dependency'):
                bundle = pack(example, retrieve(example), config['evidence_cap'], variant == 'dependency',
                              counter=ProviderCounter(ledger))
                req = request(example.question, bundle, provider.identity, settings)
                # This count excludes system/schema overhead. Provider usageMetadata
                # records the actual whole-request prompt/output/thinking usage.
                input_count = ledger.count(canonical(req['input']))
                entry = {'id': example.id, 'variant': variant, 'packing': bundle,
                         'request': req, 'input_text_tokens': input_count,
                         'input_count_scope': getattr(provider, 'count_scope',
                             'user text only; excludes system/schema; countTokens, not estimate')}
                write(out, 'current_input.json', entry)  # Survives a stop on this request.
                result = ledger.predict(req, bundle)
                entry['prediction'] = result
                outputs.append(entry)
                write(out, 'results.json', outputs)
                # Retain resolved version and stop rather than score mixed-model pairs.
                resolved = {e['prediction'].get('resolved_model') for e in outputs if e['prediction'].get('resolved_model')}
                if len(resolved) > 1:
                    raise StopRun('resolved_model_drift')
    except (StopRun, ProviderError) as error:
        stop = str(error)
        if isinstance(error, ProviderError): manifest['error_details'] = error.details
    finally:
        manifest.update(model_calls=ledger.calls(), cache_hits=ledger.cache_hits,
                        model_calls_this_invocation=ledger.calls() - initial_calls,
                        token_count_calls_this_invocation=ledger.count_calls, stop_reason=stop,
                        completed_requests=len(outputs), status='stopped' if stop else 'completed',
                        finished_unix=time.time())
        ledger.close()
        write(out, 'manifest.json', manifest)
    if stop:
        print(canonical({'status': 'stopped', 'reason': stop, 'completed_requests': len(outputs)}))
        return
    # Trusted scoring phase ONLY. Inference is already finished; references are
    # never used to select, repair or regenerate a model prediction.
    references = [indexed[qid][1] for qid in config['ids']]
    write(out, 'official_references.json', references)
    metrics = {}
    for variant in ('ordinary', 'dependency'):
        entries = [e for e in outputs if e['variant'] == variant]
        predictions = [{'id': e['id'], 'predicted': e['prediction'].get('execution', {}).get('tokens') or ['EOF']}
                       for e in entries]
        name = f'official_predictions_{variant}.json'
        write(out, name, predictions)
        metrics[variant] = score(predictions, config['ids'], out / name,
                                 out / 'official_references.json', ROOT.parent / 'FinQA/code/evaluate/evaluate.py')
        metrics[variant]['label'] = ('MOCK abstention fixtures; NOT model results' if mock else
                                    'model predictions; three dev questions only')
        metrics[variant]['failures'] = sum(e['prediction'].get('execution', {}).get('status') != 'ok' for e in entries)
    write(out, 'metrics.json', metrics)
    manifest['official_scores'] = metrics
    write(out, 'manifest.json', manifest)
    print(canonical(metrics))


if __name__ == '__main__':
    # Same literal parser as the retained OpenAI route; never source a secret file.
    from nrqa.openai_provider import local_environment
    try:
        main(lambda: Gemini(local_environment(ROOT / '.env', {
            'GEMINI_API_KEY', 'GEMINI_MODEL', 'GEMINI_FREE_TIER_CONFIRMED'})))
    except ProviderError as error:
        raise SystemExit(error.code) from None
