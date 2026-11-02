#!/usr/bin/env python3
"""Independently verify returned E recovery infrastructure archives locally."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--returned', type=Path, required=True)
    ap.add_argument('--job', required=True)
    ap.add_argument('--label', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    stem = a.job + '-' + a.label
    receipt = read(a.returned / (stem + '.json'))
    archive = a.returned / (stem + '.tar.gz')
    manifest_path = a.returned / (stem + '.manifest.json.gz')
    assert sha(archive) == receipt['archive_sha256'] == (a.returned / (stem + '.tar.gz.sha256')).read_text().split()[0]
    assert sha(manifest_path) == receipt['manifest_sha256']
    assert receipt['slurm_job_id'] == a.job and receipt['output_state'] == 'complete'
    manifest = json.loads(gzip.decompress(manifest_path.read_bytes()))['files']
    assert len(manifest) == receipt['archive_entries']
    assert all(row['kind'] in ('file', 'directory') for row in manifest.values())
    spec = importlib.util.spec_from_file_location('storage_archive', a.repo / 'harness/tacc_storage/archive.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.verify(archive, manifest)
    a.out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as tar:
        for member in tar:
            path = a.out / member.name
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, path.open('xb') as dest:
                    while block := source.read(1048576):
                        dest.write(block)
    output = a.out / 'output'
    assert helper.inventory(output) == manifest
    baseline = read(a.repo / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json')['hashes']
    for name in ('protected_before.json', 'protected_after.json'):
        r = read(output / 'job_metadata' / name)
        assert r['count'] == len(baseline) == 30067 and not r['changed']
        assert set(r['files']) == set(baseline)
        assert all(v['before_sha256'] == v['after_sha256'] == baseline[p] for p, v in r['files'].items())
    verification = dict(job_id=a.job, archive_sha256=sha(archive), manifest_sha256=sha(manifest_path),
                        exact_archive_entries=len(manifest), extracted_inventory_matches=True,
                        protected_files_unchanged=30067, output_state=receipt['output_state'])
    if a.label == 'e-storage-fixture':
        setup = read(output / 'job_metadata/fixture_setup.json')
        result = read(output / 'job_metadata/fixture_result.json')
        assert result == dict(all_passed=True, container_mount_probes=32, new_simulations=0, new_builds=0)
        probes = [read(p) for p in (output / 'fixture').glob('*.json')]
        assert {p['index'] for p in probes} == set(setup['fixture_indices']) and len(probes) == 32
        for p in probes:
            assert p['all_mount_checks_passed'] and p['original_stop_preserved']
            assert p['sealed_metadata_read_only'] and p['retained_elf_hashes_match'] and p['frozen_code_hashes_match']
            assert p['new_simulations'] == p['new_builds'] == 0 and p['slurm_job_id'] == a.job
        packet = a.repo / 'notes/e_resume_2026-11-02_v1/packet'
        assert setup['fixture_code_manifest_sha256'] == sha(packet / 'fixture_code.sha256.json')
        assert setup['selection_sha256'] == sha(packet / 'selection.json')
        for name in ('execution.json', 'execution.sha256', 'tasks-evaluate.json', 'tasks-controls.json'):
            assert sha(output / name) == sha(packet / ('original-' + name))
        verification.update(fixture_result=result, fixture_setup=setup,
                            resource_summary=read(output / 'job_metadata/resource_summary.json'))
    with (a.out / 'verification.json').open('x') as stream:
        json.dump(verification, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(verification, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
