"""Carry saved model responses into a new run directory and re-parse them locally.

Requests are keyed by content, so unchanged requests replay from this copy with no
API call. Status 'response_saved' makes the runner re-parse with the current code.
"""
import shutil
import sqlite3
import sys
import json


def main(source, target):
    shutil.copy(source, target)
    db = sqlite3.connect(target)
    rows = db.execute('SELECT key, record FROM requests').fetchall()
    carried = 0
    for key, text in rows:
        record = json.loads(text)
        if 'raw_response' in record:
            record['status'] = 'response_saved'
            db.execute('UPDATE requests SET record=? WHERE key=?', (json.dumps(record), key))
            carried += 1
    db.commit()
    db.close()
    print(f'{carried} saved responses carried to {target}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
