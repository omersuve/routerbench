"""Reproduce shipped offline metrics without opening provider recordings."""
import json
from pathlib import Path
import tempfile
import unittest

from routerbench.adapters import Replay, Rules
from routerbench.runner import predict
from routerbench.scoring import score

ROOT = Path(__file__).resolve().parents[1]


class PublicSnapshotTests(unittest.TestCase):
    def test_all_rules_metrics_reproduce_recorded_results(self):
        summary = json.loads((ROOT / 'results/summary.json').read_text())
        for phase in ('phase1', 'phase2', 'phase3'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                predict(ROOT / f'datasets/{phase}/inputs.json', Path(directory) / 'run', Rules())
                actual = score(Path(directory) / 'run', ROOT / f'datasets/{phase}/labels.json')
                reference = summary[phase]['rules']
                for key in ('n', 'observed', 'coverage', 'metrics', 'set_metrics',
                            'hard_count', 'high_risk_count', 'statuses', 'paid_calls_this_run'):
                    self.assertEqual(actual[key], reference[key], key)
                self.assertEqual({key: len(ids) for key, ids in actual['events'].items()},
                                 reference['event_counts'])

    def test_documented_replay_is_complete_and_correct(self):
        with tempfile.TemporaryDirectory() as directory:
            predict(ROOT / 'examples/inputs.json', Path(directory) / 'run',
                    Replay(ROOT / 'examples/responses.jsonl'))
            result = score(Path(directory) / 'run', ROOT / 'examples/labels.json')
            self.assertEqual(result['n'], 1)
            self.assertEqual(result['coverage'], 1.0)
            self.assertEqual(result['metrics']['all_exact']['correct'], 1)
            self.assertEqual(result['paid_calls_this_run'], 0)
