#!/usr/bin/env python3
"""Infrastructure unit tests only: never starts Renode or submits a job."""
import json
import tempfile
import unittest
from pathlib import Path
from calibration import exclusive, plan_at, stop
from prepare import sha
from resources import parse_time, select_concurrency


class InfrastructureTests(unittest.TestCase):
    def test_time_minutes(self):
        self.assertEqual(parse_time('Elapsed (wall clock) time (h:mm:ss or m:ss): 0:40.50\n'
                                    'Maximum resident set size (kbytes): 524288\n'), (524288, 40.5))

    def test_time_hours(self):
        self.assertEqual(parse_time('Elapsed (wall clock) time (h:mm:ss or m:ss): 1:02:03\n'
                                    'Maximum resident set size (kbytes): 10\n'), (10, 3723.0))

    def test_incomplete_resource_log(self):
        with self.assertRaises(ValueError):
            parse_time('terminated before measurement')

    def test_memory_limit(self):
        self.assertEqual(select_concurrency(100, 1000, 128, 32), (5, 5))

    def test_cpu_limit(self):
        self.assertEqual(select_concurrency(1, 1000, 4, 32)[0], 4)

    def test_user_cap(self):
        self.assertEqual(select_concurrency(1, 1000, 128, 16)[0], 16)

    def test_insufficient_memory(self):
        with self.assertRaises(ValueError):
            select_concurrency(100, 100, 128, 32)

    def test_exclusive_records(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'record.json'
            exclusive(path, {'original': True})
            with self.assertRaises(FileExistsError):
                exclusive(path, {'replacement': True})
            self.assertEqual(json.loads(path.read_text()), {'original': True})

    def test_stop_preserves_first_cause(self):
        with tempfile.TemporaryDirectory() as d:
            stop(Path(d), 'first failure')
            stop(Path(d), 'second failure')
            self.assertEqual(json.loads((Path(d)/'STOP.json').read_text())['reason'], 'first failure')

    def test_tampered_plan_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / 'calibration_plan.json'
            p.write_text('{"tasks": []}\n')
            (root/'calibration_plan.sha256').write_text(sha(p)+'  calibration_plan.json\n')
            self.assertEqual(plan_at(root)[0], {'tasks': []})
            p.write_text('{"tasks": [1]}\n')
            with self.assertRaises(ValueError):
                plan_at(root)


if __name__ == '__main__':
    unittest.main()
