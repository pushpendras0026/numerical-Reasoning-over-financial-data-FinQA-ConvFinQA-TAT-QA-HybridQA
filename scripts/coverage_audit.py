"""Gold-evidence coverage for every dev question, method and cap. No API calls."""
import argparse
import json
import multiprocessing
import time
from pathlib import Path
from nrqa.coverage import SOURCES, load, one, summarize

ITEMS = None


def work(index):
    return one(ITEMS[index])


def main():
    global ITEMS
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='artifacts/v11/coverage.json')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    results = {}
    context = multiprocessing.get_context('fork')
    for dataset in SOURCES:
        start = time.monotonic()
        ITEMS = load(dataset)
        with context.Pool(args.workers) as pool:
            rows = pool.map(work, range(len(ITEMS)), chunksize=16)
        results[dataset] = dict(summarize(rows), total=len(ITEMS), seconds=time.monotonic() - start)
        print(dataset, results[dataset]['n'], round(results[dataset]['seconds']), flush=True)
    Path(args.out).write_text(json.dumps(results, indent=1) + '\n')


if __name__ == '__main__':
    main()
