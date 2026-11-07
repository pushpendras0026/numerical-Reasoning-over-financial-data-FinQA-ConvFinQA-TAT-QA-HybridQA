"""Offline, read-only smoke audit. No .env, provider calls, or ledger repair."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

from nrqa.model import cache_key


def inspect(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'manifest.json').read_text())
    current = json.loads((directory/'current_input.json').read_text())
    current_key = cache_key(current['request'])
    with sqlite3.connect((directory/'cache.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        records = []
        for key, value in db.execute('SELECT key,record FROM requests ORDER BY key'):
            record = json.loads(value)
            records.append({'logical_request_id': key,
                'dataset_id': current['id'] if key == current_key else None,
                'variant': current['variant'] if key == current_key else None,
                'status': record['status'], 'raw_response_saved': 'raw_response' in record,
                'attempts': [{**attempt, 'attempt_number': n, 'logical_request_id': key}
                             for n, attempt in enumerate(record['attempts'], 1)]})
        count_entries = db.execute('SELECT count(*) FROM counts').fetchone()[0]
    return {'mode': 'offline_read_only', 'manifest_status': manifest['status'],
            'manifest_error': manifest.get('error'), 'manifest_error_details': manifest.get('error_details'),
            'count_cache_entries': count_entries,
            'counted_generation_attempts': sum(len(r['attempts']) for r in records),
            'requests': records,
            'file_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(directory.iterdir()) if p.is_file()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.directory), indent=2))


if __name__ == '__main__':
    main()
