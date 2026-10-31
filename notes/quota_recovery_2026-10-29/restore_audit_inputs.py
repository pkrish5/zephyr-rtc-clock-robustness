#!/usr/bin/env python3
"""Finish quota-interrupted provisioning of exact original audit dependencies."""
import json
import os
from pathlib import Path
import subprocess
import hashlib


def main():
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Development required')
    repo=Path(os.environ['WORK']).resolve()/'zephyr-rtc-clock-robustness'
    output=Path(os.environ['RTC_RECOVERY_REPORT']).resolve()
    output.relative_to(Path(os.environ['SCRATCH']).resolve());output.mkdir(parents=True,exist_ok=False)
    recovery=repo/'tacc_work/20261029-quota-recovery-v1'
    bootstrap=json.loads((recovery/'bootstrap-3540791.json').read_text())
    if not bootstrap['source_removed'] or bootstrap['protected_files_deleted']:
        raise RuntimeError('Bootstrap cleanup not validated')
    receipt=recovery/('audit-restoration-'+os.environ['SLURM_JOB_ID']+'.json')
    subprocess.run(['python3',str(repo/'harness/tacc_s2_evidence/stage_audit_paths.py'),
        '--repo',str(repo),'--cache',str(repo/'harness/tacc_s2_evidence/protected_inputs_20261024_v1'),
        '--out',str(receipt)],check=True)
    raw=receipt.read_bytes();r=json.loads(raw)
    if r['pre_existing_files_overwritten']:
        # The helper's authoritative full-count check is in its .protected.json.
        raise RuntimeError('Unexpected overwrite/receipt schema')
    audit=json.loads(receipt.with_suffix('.protected.json').read_text())
    if audit['count']!=30067 or audit['changed']:raise RuntimeError('Full protected audit failed')
    result=dict(job_id=os.environ['SLURM_JOB_ID'],receipt=str(receipt),
        receipt_sha256=hashlib.sha256(raw).hexdigest(),protected_verified=30067,
        restored_original_files=len(r['missing_paths_provisioned']),existing_files_overwritten=0,
        new_builds=0,new_simulations=0,source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    with (output/'final.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
