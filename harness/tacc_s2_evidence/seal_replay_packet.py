#!/usr/bin/env python3
"""Seal the new outer code and cost proposal; never submit a Slurm job."""
import argparse
import hashlib
import json
from pathlib import Path

FILES = [
    'harness/tacc_s2/worker.py',
    'harness/tacc_s2_evidence/replay_worker.py',
    'harness/tacc_s2_evidence/replay_task.sh',
    'harness/tacc_s2_evidence/setup_replays.py',
    'harness/tacc_s2_evidence/replays.sbatch',
    'harness/tacc_storage/runtime.sh',
    'harness/tacc_storage/run_packed.sh',
    'harness/tacc_storage/protected_check.py',
    'harness/tacc_storage/check_headroom.py',
    'harness/tacc_storage/publish.py',
    'harness/tacc_storage/archive.py',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('proposal', 'repo', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    proposal = json.loads(a.proposal.read_text())
    if not proposal['source_evidence_archive_sha256']:
        raise RuntimeError('Verified source archive is required')
    code = {rel: sha(a.repo / rel) for rel in FILES}
    if code['harness/tacc_s2/worker.py'] != proposal['unchanged_simulation_worker_sha256']:
        raise RuntimeError('Frozen simulation source differs')
    a.out.mkdir(parents=True, exist_ok=False)
    def save(path, value):
        with path.open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
    save(a.out / 'code.sha256.json', code)
    packet = dict(queue='normal', allocation='TRA25006', nodes=1,
                  wall_time='01:00:00', concurrency=32, arrays=False,
                  proposed_reservation_ceiling_SU=1, estimated_budget_SU=1,
                  minimum_billed_SU=0.25,
                  billing_source='https://docs.tacc.utexas.edu/hpc/lonestar6/#job-accounting',
                  billing_verified_date='2026-10-31',
                  su_convention='LS6 whole-node hours used in the existing S2 protocol',
                  saved_runtime_throughput_estimate_node_hours=proposal[
                      'throughput_estimated_node_hours_with_1_5_margin'],
                  estimate_excludes='queue wait, protection checks, filesystem slowdown and packing',
                  primary_failures_covered=proposal['primary_case_failures_covered'],
                  application_replays=proposal['full_application_launches'],
                  original_plan_sha256=proposal['source_primary_plan_sha256'],
                  proposal_sha256=sha(a.proposal),
                  code_manifest_sha256=sha(a.out / 'code.sha256.json'),
                  protected_inputs_changed=False, new_builds=0,
                  execution_authorized=False, submitted=False,
                  prerequisite='Explicit user normal-queue approval and successful compute-node '
                               'storage-coordinator infrastructure check',
                  interruption_policy='Pack existing partial bytes; never replace primary scores',
                  reference_jobs_included=False, E_started=False)
    save(a.out / 'submission_proposal.json', packet)
    print(json.dumps(packet, indent=2))


if __name__ == '__main__':
    main()
