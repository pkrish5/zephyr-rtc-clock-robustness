#!/usr/bin/env python3
"""Synthetic metadata checks only; does not build firmware or invoke Renode."""
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name('control.py')


def put(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj))


def main():
    with tempfile.TemporaryDirectory(prefix='s2-accounting-only-') as d:
        b = Path(d)
        names = ['s.working', 's.skip', 's.fail', 's.missing', 's.duplicate']
        units = [dict(id='f4-rtc', board_id='f4', family='rtc', expected_declared_cases=names),
                 dict(id='f4-wdt', board_id='f4', family='wdt', expected_declared_cases=['w.test'])]
        tasks = [dict(index=i) for i in range(13)]
        p = dict(output_relative='out', boards=dict(f4=dict(board='stm32f4_disco')),
                 units=units, tasks=tasks, watchdog_attempt=1)
        put(b / 'plan.json', p)
        (b / 'plan.sha256').write_text(hashlib.sha256((b / 'plan.json').read_bytes()).hexdigest())
        put(b / 'out/capacity.json', dict(workers=4))
        for u in units:
            put(b / 'out/builds' / u['id'] / 'build_record.json', dict(status='built'))
        for i in range(12):
            cases = [dict(case='s.working', status='pass'), dict(case='s.skip', status='skip'),
                     dict(case='s.fail', status='fail' if i == 0 else 'pass'),
                     dict(case='s.duplicate', status='pass'), dict(case='s.duplicate', status='pass')]
            # A missing case remains missing even though the application completed.
            put(b / f'out/records/{i:02d}.json', dict(index=i, unit_id='f4-rtc', run_id=str(i),
                condition='nominal' if i < 5 else 'min', application_completed=True, cases=cases,
                rtc_divider_observations=[32000], wall_seconds=10))
            t = b / f'out/resources/run/{i}.time'
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text('Maximum resident set size (kbytes): 100000\n')
        put(b / 'out/records/12.json', dict(index=12, unit_id='f4-wdt', run_id='w', condition='nominal',
            watchdog_reboot_and_completion=False, cases=[dict(case='w.test', status='pass')]))
        subprocess.run([sys.executable, str(SCRIPT), 'report', '--bundle', str(b)], check=True)
        report = json.loads((b / 'out/qualification_report.json').read_text())
        rows = {r['case']: r for r in csv.DictReader((b / 'out/per_case_qualification.csv').open())}
        assert report['units'][0]['qualified_cases'] == ['s.working']
        assert rows['s.skip']['nominal_classification'] == 'capability_skip'
        assert rows['s.fail']['nominal_classification'] == 'nominal_failure'
        assert rows['s.missing']['nominal_missing'] == '5'
        assert rows['s.duplicate']['nominal_missing'] == '5'
        assert report['watchdog'][0]['qualified'] is False
        assert report['production_authorized'] is False
        assert report['provisional_primary_production_launches'] == 0
        assert report['units'][0]['configuration_ready_for_review'] is False
    print('Synthetic accounting checks passed: skips/missing/duplicates never qualify; watchdog needs reboot evidence.')


if __name__ == '__main__':
    main()
