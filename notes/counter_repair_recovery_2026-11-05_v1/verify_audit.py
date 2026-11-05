#!/usr/bin/env python3
"""Local independent verification of the read-only counter infrastructure audit."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import shutil
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--returned', type=Path, required=True)
    parser.add_argument('--job', required=True)
    parser.add_argument('--out', type=Path, required=True)
    a = parser.parse_args()
    stem = a.job + '-counter-infra-audit'
    receipt = read(a.returned / (stem + '.json'))
    archive = a.returned / (stem + '.tar.gz')
    mp = a.returned / (stem + '.manifest.json.gz')
    assert receipt['slurm_job_id'] == a.job
    assert receipt['output_state'] in ('complete', 'failed', 'interrupted')
    assert sha(archive) == receipt['archive_sha256'] == (a.returned / (stem + '.tar.gz.sha256')).read_text().split()[0]
    assert sha(mp) == receipt['manifest_sha256']
    manifest = json.loads(gzip.decompress(mp.read_bytes()))['files']
    assert len(manifest) == receipt['archive_entries']
    spec = importlib.util.spec_from_file_location('archive_helper', ROOT / 'harness/tacc_storage/archive.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.verify(archive, manifest)
    a.out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as tar:
        for item in tar:
            rel = PurePosixPath(item.name)
            assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] == 'output'
            target = a.out / item.name
            if item.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                assert item.isfile()
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(item) as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
    out = a.out / 'output'
    assert helper.inventory(out) == manifest
    baseline = read(ROOT / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json')['hashes']
    for stage in ['before', 'after']:
        proof = read(out / f'job_metadata/protected_{stage}.json')
        assert proof['count'] == len(baseline) == 30067 and not proof['changed']
        assert set(proof['files']) == set(baseline)
        assert all(v['before_sha256'] == v['after_sha256'] == baseline[k] for k, v in proof['files'].items())
    result = dict(job_id=a.job, archive_sha256=sha(archive), exact_entries=len(manifest),
                  output_state=receipt['output_state'], protected_files_unchanged=30067,
                  recovery_ready=False)
    if receipt['output_state'] == 'complete':
        registration = read(HERE / 'audit_plan.json')
        evidence = out / 'evidence'
        note = evidence / HERE.relative_to(ROOT)
        assert sha(note / 'audit_plan.json') == sha(HERE / 'audit_plan.json')
        assert sha(note / 'PROTOCOL.md') == registration['protocol_sha256']
        assert sha(note / 'original_scientific_protocol.md') == registration['original_scientific_protocol_sha256']
        bundle = evidence / registration['original_bundle_relative']
        assert sha(bundle / 'plan.json') == registration['original_plan_sha256']
        plan = read(bundle / 'plan.json')
        audit = read(out / 'audit.json')
        assert audit['scientific_tasks_executed'] == audit['builds_executed'] == audit['original_files_modified'] == 0
        assert audit['original_jobs_changed'] is False and audit['existing_primary_records'] == []
        for item in audit['copied_files']:
            assert sha(evidence / item['path']) == item['sha256']
        for rel, digest in registration['counter_inputs_sha256'].items():
            assert audit['seals_unchanged']['repo/' + rel] == digest
            assert sha(evidence / rel) == digest
        environment = read(out / 'environment.json')
        assert environment['job_id'] == a.job
        assert all(environment['module_paths'].values())
        assert environment['image_sha256'] == registration['image_sha256']
        assert environment['container_true_probe']['exit_code'] == 0
        assert environment['apptainer_version'].startswith('apptainer version 1.4.1')
        assert 'launcher/3.10' in environment['loaded_modules'].split(':')
        for unit in plan['units']:
            base = bundle / plan['output_relative'] / 'builds' / unit['id']
            record = read(base / 'build_record.json')
            assert record['status'] == 'built' and record['exit_code'] == 0 and record['error'] is None
            assert sha(bundle / record['elf_path']) == record['elf_sha256']
            assert sha(base / 'build.log') == record['log_sha256']
            assert record['plan_sha256'] == registration['original_plan_sha256']
            assert record['slurm_job_id'] == '3552460'
            assert set(record['compiled_case_names']) == set(unit['expected_declared_cases'])
            for rel, digest in record['build_products_sha256'].items():
                assert sha(base / 'build' / rel) == digest
        assert len(audit['builds']) == 4
        result.update(recovery_ready=True, saved_builds_verified=4, existing_primary_records=0,
                      active_input_seals_unchanged=len(registration['counter_inputs_sha256']),
                      module_container_probe_passed=True, node=environment['node'])
    (a.out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
