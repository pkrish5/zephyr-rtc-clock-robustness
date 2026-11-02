#!/usr/bin/env python3
"""Compute-node orchestration only: pack the unchanged read-only E index audit."""
import hashlib
import os
from pathlib import Path

if os.environ.get('SLURM_JOB_PARTITION') != 'development':
    raise RuntimeError('Development compute allocation required')
repo = Path(os.environ['WORK']).resolve() / 'zephyr-rtc-clock-robustness'
audit = repo / 'notes/quota_recovery_2026-10-29/audit_e_partial.py'
digest = hashlib.sha256(audit.read_bytes()).hexdigest()
if digest != '43364d36d82af2725a45fc33db5db45fc47a6d164c84bf9192670400eb47e952':
    raise RuntimeError('Original E audit source differs')
env = dict(os.environ, RTC_REPO=str(repo),
           RTC_CONTAINER_SHA256='94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1',
           RTC_RECOVERY_SOURCE_SHA256=digest)
command = r'''set -euo pipefail
export RTC_RECOVERY_REPORT="$RTC_JOB_OUTPUT/e_audit"
python3 "$RTC_REPO/notes/quota_recovery_2026-10-29/audit_e_partial.py"
'''
os.execve('/bin/bash', ['bash', str(repo / 'harness/tacc_storage/run_packed.sh'),
                       'e-partial-audit', 'bash', '-l', '-c', command], env)
