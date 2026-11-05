#!/usr/bin/env python3
"""One receipt-protected development diagnostic; never a replacement test job."""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

repo = Path(os.environ['WORK']) / 'zephyr-rtc-clock-robustness'
note = repo / 'notes/counter_repair_recovery_2026-11-05_v1'
plan = json.loads((note / 'audit_plan.json').read_text())
assert plan['scientific_tasks_authorized'] == 0
base = repo / 'tacc_work/20261105-counter-infra-audit-v1'
base.mkdir(exist_ok=True)
intent = base / 'submission.intent.json'
receipt = base / 'submission.json'
with intent.open('x') as stream:
    json.dump(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
                   audit_plan_sha256=hashlib.sha256((note / 'audit_plan.json').read_bytes()).hexdigest()), stream)
logs = Path(os.environ['SCRATCH']) / 'zephyr-rtc-clock-robustness/counter-infra-audit-20261105-v1/slurm'
logs.mkdir(parents=True, exist_ok=True)
image = repo / plan['image_relative']
assert image.is_file()
assert (image.parent / 'rtc-ls6-v1.sif.sha256').read_text().split()[0] == plan['image_sha256']
cmd = ['sbatch', '--parsable', '-A', 'TRA25006', '-p', 'development', '-N', '1', '-n', '128',
       '-t', '00:15:00', '--chdir=' + str(repo), '--output=' + str(logs / 'audit-%j.out'),
       '--error=' + str(logs / 'audit-%j.err'),
       '--export=ALL,RTC_REPO=' + str(repo) + ',RTC_IMAGE=' + str(image), str(note / 'audit.sbatch')]
result = dict(state='uncertain', command=cmd, reservation_su_ceiling=0.25,
              scientific_tasks=0, original_jobs_changed=False)
try:
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    result.update(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    ids = re.findall(r'^([0-9]+)(?:;[^\n]*)?$', proc.stdout, re.M)
    if proc.returncode == 0 and len(ids) == 1:
        result.update(state='accepted', job_id=ids[0])
    else:
        result['state'] = 'rejected_or_uncertain'
except subprocess.TimeoutExpired:
    result['error'] = 'sbatch timed out; inspect receipt and queue, never retry blindly'
with receipt.open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['state'] == 'accepted' else 2)
