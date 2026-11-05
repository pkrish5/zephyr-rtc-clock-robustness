#!/usr/bin/env python3
"""Dry-run by default; real submission requires a recorded human approval."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--group', choices=['gate', 'legal-a', 'legal-b', 'fault'], required=True)
parser.add_argument('--approval', type=Path, default=HERE / 'approval.json')
parser.add_argument('--gate-proof', type=Path)
parser.add_argument('--submit', action='store_true')
a = parser.parse_args()
plan_path = HERE / 'plan.json'
plan = json.loads(plan_path.read_text())
digest = hashlib.sha256(plan_path.read_bytes()).hexdigest()
group = plan['groups'][a.group]
repo = Path(os.environ.get('WORK', '/work/10970/pk23377/ls6')) / 'zephyr-rtc-clock-robustness'
note = repo / 'notes/counter_repair_execution_2026-11-05_v1'
base = repo / 'tacc_work/20261105-counter-repair-recovery-v1'
scratch = Path(os.environ.get('SCRATCH', '/scratch/10970/pk23377'))
logs = scratch / 'zephyr-rtc-clock-robustness/counter-recovery-20261105-v1/slurm'
values = dict(RTC_REPO=str(repo), RTC_RECOVERY_GROUP=a.group,
              RTC_RECOVERY_APPROVAL=str(note / 'approval.json' if a.approval == HERE / 'approval.json' else a.approval),
              RTC_IMAGE=str(repo / plan['image_relative']))
if a.group != 'gate':
    if a.submit:
        assert a.gate_proof is not None
        proof = json.loads(a.gate_proof.read_text())
        assert proof['passed'] is True and proof['recovery_plan_sha256'] == digest
        assert proof['gate_job_state'] == 'COMPLETED' and proof['gate_exit_code'] == '0:0'
        assert re.fullmatch('[0-9]+', proof['gate_job_id'])
        values['RTC_RECOVERY_GATE_JOB'] = proof['gate_job_id']
    else:
        values['RTC_RECOVERY_GATE_JOB'] = '<independently-verified-gate-job>'
cmd = ['sbatch', '--parsable', '-A', 'TRA25006', '-p', 'normal', '-N', '1', '-n', '128',
       '-t', group['wall_limit'], '--job-name=rtc-counter-' + a.group,
       '--chdir=' + str(repo), '--output=' + str(logs / (a.group + '-%j.out')),
       '--error=' + str(logs / (a.group + '-%j.err')),
       '--export=ALL,' + ','.join(k + '=' + v for k, v in values.items()), str(note / 'job.sbatch')]
record = dict(state='dry_run', group=a.group, command=cmd, plan_sha256=digest,
              planned_launches=len(group['indices']), estimated_su=group['estimated_su'],
              reservation_su_ceiling=group['ceiling_su'])
if not a.submit:
    print(json.dumps(record, indent=2))
    raise SystemExit(0)
assert 'WORK' in os.environ and HERE == note
approval = json.loads(a.approval.read_text())
assert approval['approved'] is True and approval['plan_sha256'] == digest
assert approval['account'] == 'TRA25006' and approval['normal_ceiling_su'] == 8
assert approval['human_authorization'] and a.group in approval['allowed_groups']
for rel, expected in plan['code_sha256'].items():
    assert hashlib.sha256((repo / rel).read_bytes()).hexdigest() == expected
base.mkdir(exist_ok=True)
logs.mkdir(parents=True, exist_ok=True)
with (base / ('submission-' + a.group + '.intent.json')).open('x') as f:
    json.dump(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), plan_sha256=digest,
                   group=a.group, approval_sha256=hashlib.sha256(a.approval.read_bytes()).hexdigest()), f)
record['state'] = 'uncertain'
try:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    record.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
    ids = re.findall(r'^([0-9]+)(?:;[^\n]*)?$', result.stdout, re.M)
    if result.returncode == 0 and len(ids) == 1:
        record.update(state='accepted', job_id=ids[0])
    else:
        record['state'] = 'rejected_or_uncertain'
except subprocess.TimeoutExpired:
    record['error'] = 'submission client timed out; inspect queue and receipt before any retry'
with (base / ('submission-' + a.group + '.json')).open('x') as f:
    json.dump(record, f, indent=2)
    f.write('\n')
print(json.dumps(record, indent=2))
raise SystemExit(0 if record['state'] == 'accepted' else 2)
