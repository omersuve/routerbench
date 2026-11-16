"""Label-only scoring after a sealed prediction run. No inference imports."""
from collections import Counter
import json
import math
import statistics
from pathlib import Path
from .io import verified_run, write_new
from .routing import validate_assessment

FIELDS = ('difficulty', 'risk', 'capabilities', 'model', 'effort', 'skills')

def wilson(correct, count):
    if not count:
        return None
    p = correct / count
    z = 1.959963984540054
    denominator = 1 + z*z/count
    centre = (p + z*z/(2*count)) / denominator
    radius = z * math.sqrt(p*(1-p)/count + z*z/(4*count*count)) / denominator
    return [max(0, centre-radius), min(1, centre+radius)]

def score(run, labels):
    manifest, predictions = verified_run(run)
    packet = json.loads(Path(labels).read_text())
    if packet['inputs_sha256'] != manifest['inputs_sha256']:
        raise ValueError('labels belong to another input dataset')
    expected = {r['id']: r for r in packet['labels']}
    if len(expected) != len(packet['labels']) or set(expected) != {r['id'] for r in predictions}:
        raise ValueError('label ids must match all predictions exactly')
    counts = Counter()
    matrices = {key: Counter() for key in ('difficulty', 'risk', 'model', 'effort')}
    statuses = Counter()
    errors = []
    special = {key: [] for key in ('hard_to_local', 'hard_under_effort', 'high_risk_as_low', 'high_risk_below_high', 'capability_miss', 'uncertain', 'unobserved_high_risk')}
    hard_count = high_count = 0
    for pred in predictions:
        label = expected[pred['id']]
        if label['task_sha256'] != pred['task_sha256']:
            raise ValueError('task/label hash mismatch')
        e = label['expected']
        validate_assessment({key: e[key] for key in ('difficulty', 'risk', 'capabilities', 'skills')})
        hard_count += e['difficulty'] == 'hard'
        high_count += e['risk'] == 'high'
        statuses[pred['status']] += 1
        if pred['status'] != 'ok':
            errors.append({'id': pred['id'], 'status': pred['status'], 'reason': pred['reason']})
            if pred['status'] == 'abstain':
                special['uncertain'].append(pred['id'])
            if e['risk'] == 'high':
                special['unobserved_high_risk'].append(pred['id'])
            continue
        a = validate_assessment(pred['assessment'])
        route = pred['route']
        actual = {**a, 'model': route['model'], 'effort': route['effort']}
        matches = {}
        for key in FIELDS:
            matches[key] = sorted(actual[key]) == sorted(e[key]) if isinstance(e[key], list) else actual[key] == e[key]
            counts[key] += matches[key]
            if key in matrices:
                matrices[key][(e[key], actual[key])] += 1
        counts['route_exact'] += matches['model'] and matches['effort']
        counts['all_exact'] += all(matches.values())
        for key in ('capabilities', 'skills'):
            truth, guessed = set(e[key]), set(actual[key])
            counts[key+'_tp'] += len(truth & guessed)
            counts[key+'_fp'] += len(guessed - truth)
            counts[key+'_fn'] += len(truth - guessed)
        if e['difficulty'] == 'hard':
            if route['model'] == 'local':
                special['hard_to_local'].append(pred['id'])
            if route['effort'] not in ('high', 'none'):
                special['hard_under_effort'].append(pred['id'])
        if e['risk'] == 'high' and a['risk'] != 'high':
            special['high_risk_below_high'].append(pred['id'])
            if a['risk'] == 'low':
                special['high_risk_as_low'].append(pred['id'])
        from .routing import CATALOG
        profile = next((m for m in CATALOG if m.id == route['model']), None)
        if profile and not set(e['capabilities']) <= profile.capabilities:
            special['capability_miss'].append(pred['id'])
        if not all(matches.values()):
            errors.append({'id': pred['id'], 'differences': {k: {'expected': e[k], 'actual': actual[k]} for k,v in matches.items() if not v}})
    n = len(predictions)
    observed = statuses['ok']
    fields = {key: {'correct': counts[key], 'total': n, 'accuracy': counts[key]/n if observed else None, 'yield': counts[key]/n,
                    'observed_accuracy': counts[key]/observed if observed else None,
                    'wilson95': wilson(counts[key], n) if observed else None} for key in (*FIELDS, 'route_exact', 'all_exact')}
    set_metrics = {}
    for key in ('capabilities', 'skills'):
        tp, fp, fn = (counts[key+x] for x in ('_tp', '_fp', '_fn'))
        set_metrics[key] = {'tp': tp, 'fp': fp, 'fn': fn, 'micro_f1_observed': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
    times = [r['latency_ms'] for r in predictions if r['latency_ms'] is not None]
    return {'version': manifest['version'], 'adapter': manifest['adapter'], 'inputs_sha256': manifest['inputs_sha256'],
            'n': n, 'observed': observed, 'coverage': observed/n, 'statuses': dict(statuses),
            'metrics': fields, 'set_metrics': set_metrics,
            'confusion': {key: [{'expected': e, 'actual': a, 'count': count} for (e,a),count in sorted(values.items())] for key,values in matrices.items()},
            'hard_count': hard_count, 'high_risk_count': high_count, 'events': special,
            'latency_ms': {'n': len(times), 'median': statistics.median(times), 'p95': sorted(times)[math.ceil(.95*len(times))-1]} if times else None,
            'latency_sources': dict(Counter(p['source'] for p in predictions)),
            'paid_calls_this_run': manifest['paid_calls'], 'errors': errors,
            'limitations': ['Reference preference labels, not optimal model quality.', 'Effort is derived from difficulty, not independent.',
                            'Wilson intervals describe this sample, not independent adjudication.', 'Replay latency is historical, never a fresh measurement.']}
