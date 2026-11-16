"""Strict tasks-only inputs and hash-sealed prediction receipts."""
import hashlib
import json
import os
from pathlib import Path
from .protocol import digest
from .routing import validate_task

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_inputs(path):
    rows = json.loads(Path(path).read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError('nonempty inputs array required')
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'task'}:
            raise ValueError('prediction inputs must contain only id and task; labels refused')
        if not isinstance(row['id'], str) or not row['id'] or row['id'] in ids:
            raise ValueError('unique nonempty task ids required')
        ids.add(row['id'])
        validate_task(row['task'])
    return rows

def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as file:
        json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write('\n')
        file.flush()
        os.fsync(file.fileno())

def verified_run(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    if file_hash(directory / 'predictions.jsonl') != manifest['predictions_sha256']:
        raise ValueError('prediction receipt mismatch')
    records = [json.loads(line) for line in (directory / 'predictions.jsonl').read_text().splitlines()]
    if len(records) != manifest['count'] or len({r['id'] for r in records}) != len(records):
        raise ValueError('incomplete/duplicate predictions')
    if digest([{'id': r['id'], 'task_sha256': r['task_sha256']} for r in records]) != manifest['task_index_sha256']:
        raise ValueError('task index receipt mismatch')
    return manifest, records
