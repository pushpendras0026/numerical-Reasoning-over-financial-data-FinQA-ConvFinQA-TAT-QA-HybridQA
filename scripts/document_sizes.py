"""Median document size per dataset, in the same estimated tokens the budget uses."""
import json
import statistics
from pathlib import Path
from nrqa.core import VisibleTokens
from nrqa.coverage import SOURCES
from nrqa.datasets import read

counter = VisibleTokens()
result = {}
for name, (path, member, corpus) in SOURCES.items():
    sizes = {}
    for example, _ in read(name, path, 'dev', corpus, member):
        sizes.setdefault(example.document['id'], sum(counter.cost(f) for f in example.facts))
    values = sorted(sizes.values())
    result[name] = {'documents': len(values), 'median_tokens': statistics.median(values),
                    'quartiles': statistics.quantiles(values, n=4)}
    print(name, result[name], flush=True)
Path('artifacts/v11/document_sizes.json').write_text(json.dumps(result, indent=1) + '\n')
