#!/usr/bin/env python3
"""Check the storage fixture's outcome from the batch shell, after publication.

Infrastructure only. Writes its verdict to SCRATCH, outside the published output.
"""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time

from archive import inventory, sha


def mount_lines(path):
    # Compare the mount/nesting lines the fixture and replay tasks share.
    keep = re.compile(r'^\s*(/usr/bin/time|timeout |apptainer exec|--bind|--home)')
    return [line.strip().replace('resources/fixture', 'resources/replays')
            for line in path.read_text().splitlines()
            if keep.match(line) and 'fixture_probe' not in line]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--packed-status', type=int, required=True)
    ap.add_argument('--signal-forwarded', type=int, required=True)
    ap.add_argument('--slots', type=int, required=True)
    ap.add_argument('--stamp', type=Path, required=True)
    a = ap.parse_args()
    job = os.environ['SLURM_JOB_ID']
    repo = Path(os.environ['RTC_REPO']).resolve()
    out = Path(os.environ['RTC_JOB_OUTPUT']).resolve()
    dest = Path(os.environ['RTC_ARCHIVE_BASE']).resolve()
    primary = Path(os.environ['RTC_PRIMARY_BUNDLE']).resolve()
    proposal = json.loads(Path(os.environ['RTC_REPLAY_PROPOSAL']).read_text())
    stem = job + '-storage-fixture'
    checks = {}
    checks['interrupt_signal_received'] = a.signal_forwarded == 1
    checks['coordinator_exit_124_interrupted'] = a.packed_status == 124
    survivors = subprocess.run(['pgrep', '-a', '-u', os.environ['USER'], '-f',
                                'fixture_probe.py|fixture_task.sh|paramrun|apptainer exec'],
                               capture_output=True, text=True).stdout.strip()
    checks['no_surviving_writer_process'] = not survivors
    receipt = json.loads((dest / (stem + '.json')).read_text())
    archive = dest / (stem + '.tar.gz')
    digest = sha(archive)
    checks['receipt_state_interrupted'] = receipt['output_state'] == 'interrupted'
    checks['work_archive_hash_matches'] = digest == receipt['archive_sha256'] == \
        (dest / (stem + '.tar.gz.sha256')).read_text().split()[0]
    checks['work_receipt_paths_only'] = {p.name for p in dest.iterdir() if p.name.startswith(stem)} == {
        stem + '.tar.gz', stem + '.tar.gz.sha256', stem + '.manifest.json.gz', stem + '.json'}
    with gzip.open(dest / (stem + '.manifest.json.gz'), 'rt') as stream:
        manifest = json.load(stream)['files']
    # Any writer still alive would change these bytes while this check waits.
    time.sleep(20)
    checks['loose_output_unchanged_after_publication'] = inventory(out) == manifest
    probes = sorted((out / 'fixture').glob('probe-*.json'))
    writers = sorted((out / 'fixture').glob('writer-*.log'))
    checks['every_slot_probed'] = len(probes) == a.slots
    checks['every_slot_wrote'] = len(writers) == a.slots and all(p.stat().st_size for p in writers)
    covered = sorted(i for p in probes for i in json.loads(p.read_text())['checked_indices'])
    checks['all_roster_preconditions_checked'] = covered == sorted(
        t['primary_task']['index'] for t in proposal['tasks'])
    checks['no_firmware_or_worker_run'] = not any(
        (out / kind).exists() for kind in ('records', 'uart', 'monitor', 'traces', 'platforms'))
    checks['output_on_scratch'] = out.is_relative_to(Path(os.environ['SCRATCH']).resolve())
    checks['loose_output_not_on_work'] = not out.is_relative_to(Path(os.environ['WORK']).resolve())
    private = list(Path(os.environ['RTC_NODE_BASE']).glob('replay-*/tmp/fixture-marker'))
    checks['private_node_local_runtime'] = len(private) == a.slots
    for name in ('protected_before.json', 'protected_after.json'):
        report = json.loads((out / 'job_metadata' / name).read_text())
        checks[name + '_30067_unchanged'] = report['count'] == 30067 and not report['changed']
        checks[name + '_in_archive'] = 'job_metadata/' + name in manifest
    changed = subprocess.check_output(['find', str(primary), '-newer', str(a.stamp)], text=True).split()
    checks['primary_bundle_nothing_newer_than_start'] = not changed
    checks['task_mounts_match_replay_task'] = (
        mount_lines(repo / 'harness/tacc_storage/fixture_task.sh')
        == mount_lines(repo / 'harness/tacc_s2_evidence/replay_task.sh'))
    value = dict(passed=all(checks.values()), checks=checks, survivors=survivors,
                 primary_paths_newer=changed[:20], slurm_job_id=job, node=socket.gethostname(),
                 archive=str(archive), archive_sha256=digest, firmware_runs=0, new_builds=0,
                 fixture_receipt=receipt)
    with (Path(os.environ['RTC_JOB_BASE']) / 'fixture_check.json').open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(dict(passed=value['passed'], checks=checks), indent=2))
    if not value['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
