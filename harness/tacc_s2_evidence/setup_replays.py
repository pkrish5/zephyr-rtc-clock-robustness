#!/usr/bin/env python3
"""Compute-node input checks and Launcher packing for an approved replay job.

Requires a separate sealed proposal and code manifest, created only after
full S2 evidence verification. Creating this script authorizes no execution.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    if os.environ['SLURM_JOB_PARTITION'] != 'normal':
        raise RuntimeError('Approved normal allocation required')
    repo = Path(os.environ['RTC_REPO']).resolve()
    primary = Path(os.environ['RTC_PRIMARY_BUNDLE']).resolve()
    primary.relative_to(repo / 'tacc_work')
    proposal_path = Path(os.environ['RTC_REPLAY_PROPOSAL']).resolve()
    if sha(proposal_path) != os.environ['RTC_REPLAY_PROPOSAL_SHA256']:
        raise RuntimeError('Proposal differs')
    manifest_path = Path(os.environ['RTC_REPLAY_CODE_MANIFEST']).resolve()
    if sha(manifest_path) != os.environ['RTC_REPLAY_CODE_MANIFEST_SHA256']:
        raise RuntimeError('Code manifest differs')
    code = json.loads(manifest_path.read_text())
    for rel, expected in code.items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts or sha(repo / rel) != expected:
            raise RuntimeError('Frozen code differs: ' + rel)
    plan_path = primary / 'plan.json'
    proposal = json.loads(proposal_path.read_text())
    plan = json.loads(plan_path.read_text())
    if sha(plan_path) != proposal['source_primary_plan_sha256']:
        raise RuntimeError('Primary plan differs')
    for rel, expected in plan['input_sha256'].items():
        if sha(primary / rel) != expected:
            raise RuntimeError('Primary input differs: ' + rel)
    if sha(Path(os.environ['RTC_IMAGE'])) != plan['image_sha256']:
        raise RuntimeError('Calibrated image differs')
    if os.environ['RTC_CONTAINER_SHA256'] != plan['image_sha256']:
        raise RuntimeError('Image provenance differs')
    output = Path(os.environ['RTC_JOB_OUTPUT']).resolve()
    output.relative_to(Path(os.environ['RTC_JOB_BASE']).resolve())
    output.relative_to(Path(os.environ['SCRATCH']).resolve())
    for folder in ('builds', 'launcher', 'job_metadata'):
        (output / folder).mkdir(exist_ok=True)
    # The physical builds directory stays empty; the task binds original
    # build records read only inside its container. Original ELFs are not copied.
    jobfile = output / 'launcher/jobfile'
    with jobfile.open('x') as stream:
        for item in proposal['tasks']:
            stream.write(shlex.join(['bash', '-l', str(repo / 'harness/tacc_s2_evidence/replay_task.sh'),
                                     str(item['primary_task']['index'])]) + '\n')
    with (output / 'job_metadata/replay_setup.json').open('x') as stream:
        json.dump(dict(proposal_sha256=sha(proposal_path), code_manifest_sha256=sha(manifest_path),
                       original_plan_sha256=sha(plan_path), original_bundle=str(primary),
                       physical_new_output=str(output), logical_output='/bundle/' + plan['output_relative'],
                       original_builds_read_only=True, new_builds=0,
                       slurm_job_id=os.environ['SLURM_JOB_ID'],
                       launcher_lines=len(proposal['tasks']),
                       original_records_modified=False), stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
