#!/usr/bin/env python3
"""Verify and safely unpack returned S2 replay evidence; no experiment execution."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--returned', type=Path, required=True)
    ap.add_argument('--repo', type=Path, required=True)
    a = ap.parse_args()
    root = a.returned
    stem = '3546149-s2-replays'
    archive = root / (stem + '.tar.gz')
    manifest_path = root / (stem + '.manifest.json.gz')
    receipt = json.loads((root / (stem + '.json')).read_text())
    digest = sha(archive)
    assert digest == receipt['archive_sha256']
    assert digest == (root / (stem + '.tar.gz.sha256')).read_text().split()[0]
    assert sha(manifest_path) == receipt['manifest_sha256']
    assert receipt['output_state'] == 'complete'
    assert receipt['slurm_job_id'] == '3546149'
    manifest = json.loads(gzip.decompress(manifest_path.read_bytes()))
    original = manifest['files']
    assert len(original) == receipt['archive_entries']
    assert all(row['kind'] in ('file', 'directory') for row in original.values()), 'No link extraction permitted'
    spec = importlib.util.spec_from_file_location('packed_archive', a.repo / 'harness/tacc_storage/archive.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.verify(archive, original)
    destination = root / 'verified'
    destination.mkdir(exist_ok=False)
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open('xb') as sink:
                    while block := source.read(1048576):
                        sink.write(block)
    output = destination / 'output'
    assert helper.inventory(output) == original
    baseline = json.loads((a.repo / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json').read_text())['hashes']
    checks = {}
    for name in ('protected_before.json', 'protected_after.json'):
        p = output / 'job_metadata' / name
        check = json.loads(p.read_text())
        assert check['count'] == len(baseline) == 30067 and not check['changed']
        assert set(check['files']) == set(baseline)
        assert all(row['before_sha256'] == row['after_sha256'] == baseline[rel]
                   for rel, row in check['files'].items())
        assert check['slurm_job_id'] == '3546149'
        checks[name] = sha(p)
    result = dict(job_id='3546149', archive_sha256=digest,
                  manifest_sha256=sha(manifest_path), output_state='complete',
                  archive_entries_verified=len(original),
                  extracted_inventory_matches=True, protected_files_unchanged=30067,
                  protected_receipts_sha256=checks,
                  no_new_builds_or_simulations=True, original_records_modified=False)
    (root / 'local_archive_verification.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
