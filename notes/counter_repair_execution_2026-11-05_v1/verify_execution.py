#!/usr/bin/env python3
"""Independently verify a packed recovery job; never replace a missing outcome."""
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import re
import shlex
import shutil
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--returned', type=Path, required=True)
    p.add_argument('--job', required=True)
    p.add_argument('--group', choices=['gate', 'legal-a', 'legal-b', 'fault'], required=True)
    p.add_argument('--sacct-json', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    sacct = read(a.sacct_json)
    assert sacct['job_id'] == a.job and sacct['state'] not in ['PENDING', 'RUNNING']
    recovery = read(HERE / 'plan.json'); group = recovery['groups'][a.group]
    assert sha(HERE / 'plan.json') == '037f96a96a1596ced1e82e6a379641ca959a31d36aa3c24fb67b6649835fc1fc'
    stem = a.job + '-counter-recovery-' + a.group
    receipt = read(a.returned / (stem + '.json'))
    archive = a.returned / (stem + '.tar.gz'); mp = a.returned / (stem + '.manifest.json.gz')
    assert receipt['slurm_job_id'] == a.job and receipt['output_state'] in ['complete', 'failed', 'interrupted']
    assert sha(archive) == receipt['archive_sha256'] == (a.returned / (stem + '.tar.gz.sha256')).read_text().split()[0]
    assert sha(mp) == receipt['manifest_sha256']
    manifest = json.loads(gzip.decompress(mp.read_bytes()))['files']
    assert len(manifest) == receipt['archive_entries']
    spec = importlib.util.spec_from_file_location('archive_helper', ROOT / 'harness/tacc_storage/archive.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    helper.verify(archive, manifest)
    a.out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as tar:
        for item in tar:
            rel = PurePosixPath(item.name)
            assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] == 'output'
            target = a.out / item.name
            if item.isdir(): target.mkdir(parents=True, exist_ok=True)
            else:
                assert item.isfile(); target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(item) as src, target.open('xb') as dst: shutil.copyfileobj(src, dst)
    out = a.out / 'output'; assert helper.inventory(out) == manifest
    baseline = read(ROOT / 'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json')['hashes']
    for stage in ['before', 'after']:
        proof = read(out / f'job_metadata/protected_{stage}.json')
        assert proof['count'] == len(baseline) == 30067 and not proof['changed']
        assert set(proof['files']) == set(baseline)
        assert all(v['before_sha256'] == v['after_sha256'] == baseline[k] for k, v in proof['files'].items())
    source = ROOT / 'notes/counter_repair_recovery_2026-11-05_v1/verified-3558303-v1/output/evidence'
    source = source / recovery['original_bundle_relative'] / 'plan.json'
    assert sha(source) == recovery['original_plan_sha256']; plan = read(source)
    guarded = all((out / f'job_metadata/input_verification_{s}.json').exists() and
                  read(out / f'job_metadata/input_verification_{s}.json')['all_passed'] for s in ['before', 'after'])
    if (out / 'job_metadata/plan.json').exists(): assert sha(out / 'job_metadata/plan.json') == sha(HERE / 'plan.json')
    if receipt['output_state'] == 'complete':
        assert guarded
        assert read(out / 'job_metadata/input_verification_after.json')['active_seals_unchanged'] == 764
    for unit in plan['units']:
        base = out / 'builds' / unit['id']; rp = base / 'build_record.json'
        if rp.exists():
            assert sha(rp) == recovery['builds'][unit['id']]['build_record_sha256']
            record = read(rp)
            assert sha(out / Path(record['elf_path']).relative_to(plan['output_relative'])) == recovery['builds'][unit['id']]['elf_sha256']
        elif receipt['output_state'] == 'complete': raise AssertionError('Missing copied ELF/build record')
    expected_rids = {f"{plan['tasks'][i]['unit_id']}-{plan['tasks'][i]['condition']}-{i:03d}" for i in group['indices']}
    assert {p.stem for p in (out / 'records').glob('*.json')} <= expected_rids
    assert {int(p.stem) for p in (out / 'processes').glob('*.json')} <= set(group['indices'])
    jobfile = out / 'launcher/jobfile'
    if jobfile.exists():
        commands = [shlex.split(line) for line in jobfile.read_text().splitlines()]
        assert len(commands) == len(group['indices'])
        assert [int(c[-1]) for c in commands] == group['indices']
        assert all(len(c) == 3 and c[0] == 'bash' and c[1].endswith('/notes/counter_repair_execution_2026-11-05_v1/task.sh') for c in commands)
    rows = []; case_rows = []; gate_ok = True
    for index in group['indices']:
        task = plan['tasks'][index]; unit = next(u for u in plan['units'] if u['id'] == task['unit_id'])
        rid = f"{task['unit_id']}-{task['condition']}-{index:03d}"
        rp = out / 'records' / (rid + '.json'); pp = out / 'processes' / f'{index}.json'
        row = dict(index=index, variant=task['variant'], condition=task['condition'], frequency_hz=task['frequency_hz'],
                   selected_outcome='missing', partial_selected='', downstream_single_shot='',
                   reason='no complete primary/process pair', primary_record_sha256=None, process_exit_code=None)
        if pp.exists():
            process = read(pp); assert process['index'] == index and process['slurm_job_id'] == a.job
            row['process_exit_code'] = process['exit_code']
        if rp.exists():
            record = read(rp); assert record['run_id'] == rid and all(record[k] == v for k, v in task.items())
            assert record['slurm_job_id'] == a.job and record['slurm_partition'] == 'normal'
            assert record['container_sha256'] == recovery['image_sha256']
            assert record['plan_sha256'] == recovery['original_plan_sha256']
            assert record['elf_sha256'] == recovery['builds'][unit['id']]['elf_sha256']
            assert record['build_record_sha256'] == recovery['builds'][unit['id']]['build_record_sha256']
            assert record['renode_version'] == plan['renode_version']
            assert record['apptainer_version'].startswith('apptainer version 1.4.1')
            assert record['apptainer_module'] == 'tacc-apptainer/1.4.1' and record['launcher_module'] == 'launcher/3.10'
            for kind, digest in record['log_sha256'].items():
                if digest: assert sha(out / kind / (rid + ('.json' if kind == 'traces' else '.log'))) == digest
            platform = out / 'platforms' / (rid + '.repl'); assert sha(platform) == record['platform_sha256']
            assert platform.read_text() == f'using "/renode/platforms/boards/stm32f4_discovery.repl"\nrtc:\n    wakeupTimerFrequency: {task["frequency_hz"]}\nnvic:\n    systickFrequency: 16000000\n'
            trace = read(out / 'traces' / (rid + '.json'))
            assert trace['run_id'] == rid and trace['cases'] == record['cases'] and trace['outcome'] == record['outcome']
            uart = out / 'uart' / (rid + '.log')
            if uart.exists():
                parsed = [dict(case=c, status=s.lower()) for s, c in re.findall(r'-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]', uart.read_text(errors='replace'))]
                assert parsed == record['cases']
            selected = [c['status'] for c in record['cases'] if c['case'] == 'counter_basic.test_all_channels']
            row.update(primary_record_sha256=sha(rp), partial_selected=';'.join(selected),
                       downstream_single_shot=';'.join(c['status'] for c in record['cases'] if c['case'] == 'counter_basic.test_single_shot_alarm_notop'))
            case_rows.extend(dict(index=index, **c) for c in record['cases'])
            complete = (record['outcome'] == 'complete' and record['application_completed'] and not record['error']
                        and not record['missing_cases'] and not record['duplicate_cases'] and row['process_exit_code'] == 0
                        and len(selected) == 1 and Counter(c['case'] for c in record['cases']) == Counter(unit['expected_declared_cases']))
            if complete:
                assert selected[0] in ['pass', 'fail', 'skip']; row.update(selected_outcome=selected[0], reason='explicit verdict in complete verified application')
                monitor = (out / 'monitor' / (rid + '.log')).read_text(errors='replace')
                assert 'cpu PerformanceInMips 16' in monitor and 'SetGlobalQuantum "0.000001"' in monitor
            else: row['reason'] = record['error'] or row['reason']
            if not complete or selected != ['pass'] or any(c['status'] == 'fail' for c in record['cases']): gate_ok = False
        else: gate_ok = False
        rows.append(row)
    if (out / 'recovery_summary.json').exists():
        saved = read(out / 'recovery_summary.json')
        assert saved['planned'] == len(rows) and saved['group'] == a.group
        assert {r['index']: r['selected_outcome'] for r in saved['rows']} == {r['index']: r['selected_outcome'] for r in rows}
    for name, data in [('per_index.csv', rows), ('all_case_verdicts.csv', case_rows)]:
        if data:
            with (a.out / name).open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
    result = dict(job_id=a.job, group=a.group, archive_sha256=sha(archive), exact_entries=len(manifest),
                  output_state=receipt['output_state'], protected_files_unchanged=30067,
                  planned=len(rows), primary_records=sum(bool(r['primary_record_sha256']) for r in rows),
                  counts={k: sum(r['selected_outcome'] == k for r in rows) for k in ['pass', 'fail', 'skip', 'missing']},
                  gate_qualified=False, fault_activation_and_references_still_required=a.group == 'fault')
    if a.group == 'gate':
        passed = gate_ok and guarded and receipt['output_state'] == 'complete' and sacct['state'] == 'COMPLETED' and sacct['exit_code'] == '0:0'
        result['gate_qualified'] = passed
        if passed:
            qualification = dict(passed=True, recovery_plan_sha256=sha(HERE / 'plan.json'), gate_job_id=a.job,
                                 gate_job_state=sacct['state'], gate_exit_code=sacct['exit_code'],
                                 archive_sha256=sha(archive), independently_verified_nominal_launches=20)
            (a.out / 'qualification.json').write_text(json.dumps(qualification, indent=2) + '\n')
    (a.out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()
