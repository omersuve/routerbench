import hashlib
import json
import os
from pathlib import Path
from . import __version__
from .io import load_inputs, file_hash, write_new
from .protocol import digest, RUBRIC
from .routing import route, policy, validate_assessment

STATES = {'ok', 'invalid', 'error', 'missing', 'abstain'}

def predict(inputs, output, adapter, threshold=None):
    if threshold is not None and not .5 <= threshold <= 1:
        raise ValueError('threshold must be between 0.5 and 1')
    rows = load_inputs(inputs)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    with (output / 'predictions.jsonl').open('x', encoding='utf-8') as file:
        for row in rows:
            observation = adapter.predict(row['task'])
            value = observation.to_dict()
            if value['status'] not in STATES:
                raise ValueError('unknown adapter status')
            if value['status'] == 'ok':
                validate_assessment(value['assessment'])
            if value['status'] == 'ok' and threshold is not None and (value['certainty'] is None or value['certainty'] < threshold):
                value['status'] = 'abstain'
                value['reason'] = 'no_confidence' if value['certainty'] is None else 'below_threshold'
            selected = route(row['task'], value['assessment']) if value['status'] == 'ok' else None
            record = {'id': row['id'], 'task_sha256': digest(row['task']), **value,
                      'route': selected, 'policy': policy(row['task']), 'execute': False}
            file.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
            file.flush()
            records.append(record)
        os.fsync(file.fileno())
    manifest = {'version': __version__, 'count': len(rows), 'adapter': adapter.name,
                'threshold': threshold, 'inputs_sha256': file_hash(inputs),
                'rubric_sha256': digest(RUBRIC), 'routing_sha256': file_hash(Path(__file__).with_name('routing.py')),
                'task_index_sha256': digest([{'id': r['id'], 'task_sha256': r['task_sha256']} for r in records]),
                'predictions_sha256': file_hash(output / 'predictions.jsonl'),
                'metadata': getattr(adapter, 'metadata', {}), 'paid_calls': 0}
    write_new(output / 'manifest.json', manifest)
    return manifest
