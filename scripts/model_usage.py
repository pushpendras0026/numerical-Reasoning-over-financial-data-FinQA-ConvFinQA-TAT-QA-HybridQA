"""Model, served version and token usage per answer block, from saved responses. No API calls.

Writes artifacts/v11/model_usage.json.
"""
import glob
import json
import statistics

out = {}
for block in ('a', 'b'):
    prompt, output, models, versions = [], [], set(), set()
    for path in glob.glob(f'artifacts/v11/{block}/*/results.json'):
        for row in json.load(open(path)):
            for attempt in row['prediction'].get('attempts', []):
                if attempt.get('status') != 'response':
                    continue
                usage = attempt.get('usage') or {}
                prompt.append(usage.get('promptTokenCount', 0))
                output.append(usage.get('candidatesTokenCount', 0) or 0)
                models.add(attempt['provider_model']['model'])
                versions.add(attempt['provider_model']['version'])
    out[block] = {'model': sorted(models), 'served_version': sorted(versions), 'responses': len(prompt),
                  'prompt_tokens_median': statistics.median(prompt), 'output_tokens_median': statistics.median(output)}
json.dump(out, open('artifacts/v11/model_usage.json', 'w'), indent=1)
print(out)
