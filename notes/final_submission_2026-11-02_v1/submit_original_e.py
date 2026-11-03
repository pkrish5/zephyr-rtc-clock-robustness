#!/usr/bin/env python3
"""One-shot development submission; refuses existing/uncertain receipts."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess


def command(args, timeout=30):
    return subprocess.check_output(args, text=True, timeout=timeout).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expected-head', required=True)
    a = ap.parse_args()
    repo = Path(os.environ['WORK']).resolve() / 'zephyr-rtc-clock-robustness'
    assert Path.cwd().resolve() == repo
    assert command(['git', 'rev-parse', 'HEAD']) == a.expected_head
    assert not command(['git', 'status', '--porcelain', '--untracked-files=no'])
    jobs = [str(j) for j in range(3547925, 3547932)]
    states_text = command(['sacct', '-X', '-n', '-P', '-j', ','.join(jobs), '--format=JobID,State,ExitCode'])
    rows = [r.split('|') for r in states_text.splitlines() if r.strip()]
    states = {r[0]: r[1:3] for r in rows}
    assert all(states.get(j) == ['COMPLETED', '0:0'] for j in jobs), states
    queue = command(['squeue', '-u', os.environ['USER'], '-h', '-o', '%i %j %T'])
    base = Path(os.environ['SCRATCH']).resolve() / 'zephyr-rtc-clock-robustness' / 'e-original-evidence-20261103-v1'
    base.mkdir(parents=True, exist_ok=False)
    receipt = base / 'submission.json'
    args = ['sbatch', '--parsable', '-A', 'TRA25006', '--export=ALL,RTC_REPO=' + str(repo),
            '--output=' + str(base / 'collector-%j.out'), '--error=' + str(base / 'collector-%j.err'),
            str(repo / 'notes/final_submission_2026-11-02_v1/collect_original_e.sbatch')]
    data = dict(state='attempt_recorded_do_not_duplicate', head=a.expected_head,
                account='TRA25006', partition='development', nodes=1, wall_time='02:00:00',
                SU_reservation_ceiling=2, recovery_job_states=states, queue_before=queue,
                started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=args)
    with receipt.open('x') as stream:
        json.dump(data, stream, indent=2)
    try:
        result = subprocess.run(args, text=True, capture_output=True, timeout=90)
        data.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        ids = re.findall(r'^([0-9]+)(?:;[^\n]+)?$', result.stdout, re.M)
        if result.returncode == 0 and len(ids) == 1:
            data.update(state='accepted', job_id=ids[0])
        else:
            data['state'] = 'reconcile_before_any_retry'
    except subprocess.TimeoutExpired as error:
        data.update(state='uncertain_acceptance_do_not_retry', error=str(error))
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(receipt=str(receipt), **data), indent=2))
    if data['state'] != 'accepted':
        raise SystemExit('STOP and reconcile; never automatically retry')


if __name__ == '__main__':
    main()
