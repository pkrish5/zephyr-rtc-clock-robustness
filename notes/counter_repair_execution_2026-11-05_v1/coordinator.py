#!/usr/bin/env python3
"""Infrastructure overlay around the unchanged sealed counter worker."""
import gzip
import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import tarfile
from collections import Counter
from pathlib import Path

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()

def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(data, f, indent=2, sort_keys=True); f.write('\n')

def require_gate(r, task, unit, plan, recovery, job):
    assert all(r[k] == v for k, v in task.items())
    assert r['outcome'] == 'complete' and r['application_completed'] and not r['error']
    assert not r['missing_cases'] and not r['duplicate_cases']
    assert Counter(c['case'] for c in r['cases']) == Counter(unit['expected_declared_cases'])
    assert all(c['status'] in ['pass', 'skip'] for c in r['cases'])
    assert [c['status'] for c in r['cases'] if c['case'] == 'counter_basic.test_all_channels'] == ['pass']
    assert r['elf_sha256'] == recovery['builds'][unit['id']]['elf_sha256']
    assert r['build_record_sha256'] == recovery['builds'][unit['id']]['build_record_sha256']
    assert r['slurm_job_id'] == job and r['renode_version'] == plan['renode_version']
    assert r['container_sha256'] == recovery['image_sha256']
    assert r['plan_sha256'] == recovery['original_plan_sha256']

def main():
    assert os.environ['SLURM_JOB_PARTITION'] == 'normal'
    repo = Path(os.environ['RTC_REPO'])
    note = repo / 'notes/counter_repair_execution_2026-11-05_v1'
    recovery_path = note / 'plan.json'
    recovery = json.loads(recovery_path.read_text())
    approval = json.loads(Path(os.environ['RTC_RECOVERY_APPROVAL']).read_text())
    assert approval['approved'] is True and approval['plan_sha256'] == sha(recovery_path)
    assert approval['normal_ceiling_su'] == 8 and approval['account'] == 'TRA25006'
    assert approval['human_authorization']
    for rel, digest in recovery['code_sha256'].items(): assert sha(repo / rel) == digest, rel
    assert sha(note / 'PROTOCOL.md') == recovery['protocol_sha256']
    bundle = repo / recovery['original_bundle_relative']
    assert sha(bundle / 'plan.json') == recovery['original_plan_sha256']
    plan = json.loads((bundle / 'plan.json').read_text())
    assert not list((bundle / plan['output_relative'] / 'records').glob('*.json'))
    image = repo / recovery['image_relative']
    assert sha(image) == recovery['image_sha256']
    seals = recovery['active_counter_inputs_sha256']
    for rel, digest in seals.items(): assert sha(repo / rel) == digest, rel
    for path in ['/opt/apps/lmod/lmod/init/sh', '/opt/apps/lmod/lmod/libexec/lmod']:
        assert Path(path).is_file(), path
    assert os.environ['RTC_APPTAINER_VERSION'].startswith('apptainer version 1.4.1')
    assert 'launcher/3.10' in os.environ['LOADEDMODULES'].split(':')
    out = Path(os.environ['RTC_JOB_OUTPUT'])
    for unit in plan['units']:
        rel = Path(plan['output_relative']) / 'builds' / unit['id']
        original = bundle / rel
        record = json.loads((original / 'build_record.json').read_text())
        expected = recovery['builds'][unit['id']]
        assert sha(original / 'build_record.json') == expected['build_record_sha256']
        assert sha(bundle / record['elf_path']) == expected['elf_sha256']
        assert record['status'] == 'built' and record['slurm_job_id'] == '3552460'
        for p in [original / 'build_record.json', bundle / record['elf_path']]:
            target = out / p.relative_to(bundle / plan['output_relative'])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            assert sha(p) == sha(target)
    save(out / 'job_metadata/input_verification_before.json', dict(all_passed=True,
         active_seals=len(seals), original_plan_sha256=sha(bundle / 'plan.json'),
         image_sha256=recovery['image_sha256'], recovery_plan_sha256=sha(recovery_path)))
    for p in [recovery_path, note / 'PROTOCOL.md']:
        shutil.copyfile(p, out / 'job_metadata' / p.name)
    save(out / 'job_metadata/approval.json', approval)
    group = recovery['groups'][os.environ['RTC_RECOVERY_GROUP']]
    if group['stage'] != 'gate':
        gate_job = os.environ['RTC_RECOVERY_GATE_JOB']
        stem = gate_job + '-counter-recovery-gate'
        packed = repo / 'tacc_work/packed-results'
        receipt = json.loads((packed / (stem + '.json')).read_text())
        archive = packed / (stem + '.tar.gz')
        mp = packed / (stem + '.manifest.json.gz')
        assert receipt['output_state'] == 'complete' and receipt['slurm_job_id'] == gate_job
        assert sha(archive) == receipt['archive_sha256'] and sha(mp) == receipt['manifest_sha256']
        manifest = json.loads(gzip.decompress(mp.read_bytes()))['files']
        spec = importlib.util.spec_from_file_location('archive_helper', repo / 'harness/tacc_storage/archive.py')
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        helper.verify(archive, manifest)
        with tarfile.open(archive) as tar:
            def read_json(name): return json.load(tar.extractfile('output/' + name))
            def read_hash(name): return hashlib.sha256(tar.extractfile('output/' + name).read()).hexdigest()
            assert read_hash('job_metadata/plan.json') == sha(recovery_path)
            assert read_json('job_metadata/input_verification_after.json')['all_passed']
            gate_rows = read_json('recovery_summary.json')['rows']
            assert {r['index'] for r in gate_rows} == set(recovery['groups']['gate']['indices'])
            for index in recovery['groups']['gate']['indices']:
                task = plan['tasks'][index]; unit = next(u for u in plan['units'] if u['id'] == task['unit_id'])
                rid = f"{task['unit_id']}-{task['condition']}-{index:03d}"
                record = read_json('records/' + rid + '.json')
                require_gate(record, task, unit, plan, recovery, gate_job)
                assert read_json(f'processes/{index}.json')['exit_code'] == 0
                for kind, digest in record['log_sha256'].items():
                    assert digest and read_hash(kind + '/' + rid + ('.json' if kind == 'traces' else '.log')) == digest
        save(out / 'job_metadata/gate_qualification.json', dict(job_id=gate_job,
             archive_sha256=receipt['archive_sha256'], qualified_nominal_launches=20))
    env = dict(os.environ, RTC_COUNTER_BUNDLE=str(bundle), RTC_COUNTER_STAGE=group['stage'],
               RTC_COUNTER_OUT_REL=plan['output_relative'],
               LAUNCHER_PPN='32', LAUNCHER_NHOSTS='1', LAUNCHER_LOCALHOST='1',
               LAUNCHER_SCHED='interleaved', LAUNCHER_BIND='1')
    for k in ['LAUNCHER_RMI', 'LAUNCHER_HOSTFILE', 'LAUNCHER_RMI_HOSTFILE']: env.pop(k, None)
    launch = out / 'launcher'; launch.mkdir()
    jobfile = launch / 'jobfile'
    with jobfile.open('x') as f:
        for index in group['indices']: f.write(shlex.join(['bash', str(note / 'task.sh'), str(index)]) + '\n')
    env.update(LAUNCHER_WORKDIR=str(launch), LAUNCHER_JOB_FILE=str(jobfile), LAUNCHER_LOGFILE=str(launch / 'launcher.log'))
    code = subprocess.run([str(Path(env['LAUNCHER_DIR']) / 'paramrun')], cwd=launch, env=env).returncode
    rows = []; gate_ok = True
    for index in group['indices']:
        task = plan['tasks'][index]; rid = f"{task['unit_id']}-{task['condition']}-{index:03d}"
        rp = out / 'records' / (rid + '.json'); pp = out / 'processes' / f'{index}.json'
        outcome = 'missing'; reason = 'absent primary record or process receipt'
        if rp.exists() and pp.exists():
            record = json.loads(rp.read_text()); proc = json.loads(pp.read_text())
            assert all(record[k] == v for k, v in task.items())
            selected = [c['status'] for c in record['cases'] if c['case'] == 'counter_basic.test_all_channels']
            if (proc['exit_code'] == 0 and record['outcome'] == 'complete' and record['application_completed']
                and not record['error'] and not record['missing_cases'] and not record['duplicate_cases'] and len(selected) == 1):
                outcome = selected[0]; reason = 'explicit verdict in complete application'
            if group['stage'] == 'gate':
                try:
                    require_gate(record, task, next(u for u in plan['units'] if u['id'] == task['unit_id']), plan, recovery, os.environ['SLURM_JOB_ID'])
                    assert proc['exit_code'] == 0
                except AssertionError: gate_ok = False
        elif group['stage'] == 'gate': gate_ok = False
        rows.append(dict(index=index, selected_outcome=outcome, reason=reason,
                         primary_record_sha256=sha(rp) if rp.exists() else None))
    for rel, digest in seals.items(): assert sha(repo / rel) == digest, rel
    for unit in plan['units']:
        p = out / 'builds' / unit['id'] / 'build/zephyr/zephyr.elf'
        assert sha(p) == recovery['builds'][unit['id']]['elf_sha256']
    assert not list((bundle / plan['output_relative'] / 'records').glob('*.json'))
    save(out / 'job_metadata/input_verification_after.json', dict(all_passed=True,
         active_seals_unchanged=len(seals), copied_original_elves_unchanged=4, original_primary_records=0))
    save(out / 'recovery_summary.json', dict(group=os.environ['RTC_RECOVERY_GROUP'],
         launcher_exit_code=code, planned=len(group['indices']), rows=rows,
         counts=dict(Counter(r['selected_outcome'] for r in rows)), gate_qualified=gate_ok if group['stage'] == 'gate' else None))
    if group['stage'] == 'gate' and (not gate_ok or code): raise SystemExit(2)

if __name__ == '__main__': main()
