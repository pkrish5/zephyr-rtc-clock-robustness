#!/usr/bin/env python3
"""Read-only E index audit on development; never reruns or edits originals.

Produces classification and follow-up lists in SCRATCH. An integrity anomaly
blocks resumption. Finalized missing verdicts are retained, not retried.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
from collections import Counter

IMAGE_SHA = '94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1'
PLAN_SHA = '2c9317ea293b72a4cbf1e7779f22ceecdbf5f3a835559db35e4114a1a95971b6'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as f: json.dump(value, f, indent=2, sort_keys=True); f.write('\n')


def main():
    if os.environ.get('SLURM_JOB_PARTITION') != 'development':
        raise RuntimeError('Development compute required')
    repo = Path(os.environ['WORK']).resolve() / 'zephyr-rtc-clock-robustness'
    bundle = repo / 'tacc_work/20261024-repair-v1/e-bundle'
    study = bundle / 'study'
    dest = Path(os.environ['RTC_RECOVERY_REPORT']).resolve()
    dest.relative_to(Path(os.environ['SCRATCH']).resolve())
    dest.mkdir(parents=True, exist_ok=False)
    if sha(bundle / 'plan.json') != PLAN_SHA:
        raise RuntimeError('Plan differs')
    plan = read(bundle / 'plan.json')
    for rel, digest in plan['input_sha256'].items():
        if sha(bundle / rel) != digest: raise RuntimeError('Frozen input differs: ' + rel)
    out = study / plan['output_relative']
    execution_sha = sha(out / 'execution.json')
    if execution_sha != (out / 'execution.sha256').read_text().split()[0]:
        raise RuntimeError('Execution seal differs')
    ex = read(out / 'execution.json')
    for name, digest in ex['task_sha256'].items():
        if sha(out / name) != digest: raise RuntimeError('Task seal differs: ' + name)
    schedule = read(study / 'subjects/phase3_rtc/plan.json')
    verified = {}
    anomalies = []

    def record(path, *, vid=None, operator=None, hz=None):
        # Only complete JSON whose raw evidence matches can count as valid.
        r = read(path)
        verified[str(path.relative_to(bundle))] = sha(path)
        for key in ('trace', 'uart', 'monitor'):
            digest = r.get(key + '_sha256')
            if not digest:
                if key == 'trace': raise RuntimeError('Missing trace hash: ' + str(path))
                continue  # A saved harness error may legitimately lack UART.
            raw = study / r[key + '_path']
            raw.resolve().relative_to(study)
            if sha(raw) != digest: raise RuntimeError('Raw hash differs: ' + str(raw))
            verified[str(raw.relative_to(bundle))] = digest
        for key in ('node_name', 'slurm_job_id', 'container_sha256', 'apptainer_version'):
            if not r.get(key): raise RuntimeError('Missing provenance ' + key)
        if r['container_sha256'] != IMAGE_SHA: raise RuntimeError('Container differs')
        if not r['apptainer_version'].startswith('apptainer version 1.4.1'):
            raise RuntimeError('Apptainer differs')
        if r.get('manifest_sha256') != execution_sha and operator != 'nominal_gate':
            raise RuntimeError('Record execution manifest differs')
        if vid is not None:
            if r['suite_id'] != vid or r.get('repair_version_id') != vid:
                raise RuntimeError('Version differs')
            if r.get('operator') != operator or r.get('lsi_frequency_hz') != hz:
                raise RuntimeError('Operator/frequency differs')
            v = ex['versions'][vid]
            op = 'nominal' if operator in ('legal', 'fast', 'slow') else operator
            built = ex['builds'][vid][op]
            if r['source_sha256'] != built['source_sha256'] or r['elf_sha256'] != built['elf_sha256']:
                raise RuntimeError('Recorded source/ELF differs')
        tr = read(study / r['trace_path'])
        for key in ('run_id', 'outcome', 'error', 'cases'):
            if r[key] != tr[key]: raise RuntimeError('Trace/record differs: ' + key)
        if r['outcome'] not in ('pass', 'fail', 'harness_error', 'timeout', 'unknown', 'skip'):
            raise RuntimeError('Unexpected recorded outcome')
        return r

    # Gate records and final ELFs are retained and checked, not rerun/rebuilt.
    for vid, digest in ex['gate_summary_sha256'].items():
        path = out / 'gate_summaries' / (vid + '.json')
        if sha(path) != digest: raise RuntimeError('Gate summary differs: ' + vid)
        gate = read(path)
        for row in gate['nominal_outcomes']:
            p = study / row['record_path']
            if sha(p) != row['record_sha256']: raise RuntimeError('Gate record differs')
            if record(p, operator='nominal_gate')['outcome'] != row['outcome']:
                raise RuntimeError('Gate outcome differs')
    for vid, builds in ex['builds'].items():
        for operator, built in builds.items():
            if built['status'] == 'pass' and sha(study / built['elf_path']) != built['elf_sha256']:
                raise RuntimeError('ELF differs: ' + vid + ' ' + operator)

    def paths(task, controls=False):
        vid, op = task['version_id'], task['operator']
        if op == 'legal':
            cond = task['condition']
            rid = vid + '-' + cond + (f'-{task["seed"]:03d}' if cond == 'seeded' else '')
            target = out / 'legal'
            hz = schedule['seeded_frequencies_hz'][task['seed']] if cond == 'seeded' else schedule['endpoints_hz'][cond]
        else:
            rid = vid + '--' + op
            target = out / ('controls' if controls else 'faults')
            hz = 64000 if op == 'fast' else 10000 if op == 'slow' else 32000
        return target, rid, hz

    controls = read(out / 'tasks-controls.json')
    if len(controls) != 19 or not read(out / 'control_audit.json')['validated']:
        raise RuntimeError('Registered controls not validated')
    for task in controls:
        target, rid, hz = paths(task, True)
        r = record(target / 'records' / (rid + '.json'), vid=task['version_id'], operator=task['operator'], hz=hz)
        if r['outcome'] != ('pass' if task['operator'] == 'legal' else 'fail'):
            raise RuntimeError('Reference control changed')

    err = repo / 'tacc_work/20261024-repair-v1/logs/evaluate12h-3535400.err'
    quota_evidence = 'Disk quota exceeded' in err.read_text(errors='replace')
    if not quota_evidence: raise RuntimeError('No saved quota evidence')
    save(dest / 'quota_cause.json', dict(stderr=str(err), sha256=sha(err), stop=read(out / 'STOP.json')))
    rows, retries, followups = [], [], []
    tasks = read(out / 'tasks-evaluate.json')
    for index, task in enumerate(tasks):
        if task['index'] != index: raise RuntimeError('Task order differs')
        target, rid, hz = paths(task)
        p = target / 'records' / (rid + '.json')
        row = dict(index=index, version_id=task['version_id'], operator=task['operator'],
                   condition=task.get('condition'), seed=task.get('seed'), record_path=str(p.relative_to(bundle)),
                   classification=None, outcome=None, record_sha256=None, wall_seconds=None, partial_files={})
        try:
            if p.exists():
                # Truncated record creation is different from a valid saved error.
                try: read(p)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    row['classification'] = 'incomplete'
                    row['partial_files'][str(p.relative_to(bundle))] = sha(p)
                else:
                    r = record(p, vid=task['version_id'], operator=task['operator'], hz=hz)
                    row.update(classification='complete-and-valid', outcome=r['outcome'], record_sha256=sha(p),wall_seconds=r['wall_seconds'])
                    if task['operator'] != 'legal':
                        s = target / 'scores' / (rid + '.json')
                        if s.exists():
                            if read(s)['record_sha256'] != sha(p): raise RuntimeError('Score seal differs')
                        else: followups.append(dict(index=index, kind='derived_score_missing', record_path=row['record_path']))
                    if r['outcome'] == 'fail':
                        rp = target / ('replay_records' if task['operator'] == 'legal' else 'replays/records') / (rid + '.json')
                        if rp.exists(): record(rp, vid=task['version_id'], operator=task['operator'], hz=hz)
                        else: followups.append(dict(index=index, kind='failure_replay_missing', record_path=row['record_path']))
            if row['classification'] != 'complete-and-valid':
                for folder, suffix in (('uart', '.log'), ('monitor', '.log'), ('traces', '.json')):
                    raw = target / folder / (rid + suffix)
                    if raw.exists(): row['partial_files'][str(raw.relative_to(bundle))] = sha(raw)
                row['simulator_artifacts_present'] = bool(row['partial_files'])
                # The worker writes a claim after actually starting. This is
                # stronger evidence than a Launcher dispatch, but does not
                # prove that firmware/virtual time began; retain that distinction.
                claim = out / 'claims/evaluate' / f'{index:05d}.json'
                if claim.exists():row['partial_files'][str(claim.relative_to(bundle))]=sha(claim)
                row['classification'] = 'incomplete' if row['partial_files'] else 'not-started'
                row['worker_claim_exists'] = claim.exists()
                retries.append(index)
        except Exception as exc:
            row['classification'] = 'integrity-anomaly'
            anomalies.append(dict(index=index, error=f'{type(exc).__name__}: {exc}'))
        rows.append(row)
    save(dest / 'per_index.json', rows)
    save(dest / 'verified_original_file_hashes.json', verified)
    save(dest / 'unfinished_followups.json', followups)
    save(dest / 'integrity_anomalies.json', anomalies)
    save(dest / 'retry_indices.json', retries)
    with (dest / 'per_index.csv').open('x', newline='') as f:
        keys = ('index','version_id','operator','condition','seed','classification','outcome','record_path','record_sha256','wall_seconds')
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    for relative, digest in verified.items():
        if sha(bundle / relative) != digest: raise RuntimeError('Original changed during audit: ' + relative)
    result = dict(job_id=os.environ['SLURM_JOB_ID'], classifications=dict(Counter(r['classification'] for r in rows)),
                  completed_outcomes=dict(Counter(r['outcome'] for r in rows if r['classification']=='complete-and-valid')),
                  retry_count=len(retries), followups_missing=len(followups), anomalies=len(anomalies),
                  execution_sha256=execution_sha, tasks_sha256=sha(out / 'tasks-evaluate.json'),
                  quota_evidence_sha256=sha(err), originals_modified=False, new_simulations=0, new_builds=0,
                  resume_allowed=not anomalies, source_sha256=os.environ['RTC_RECOVERY_SOURCE_SHA256'])
    save(dest / 'summary.json', result)
    save(dest / 'files.sha256.json', {p.name:sha(p) for p in dest.iterdir() if p.is_file()})
    print(json.dumps(result, indent=2), flush=True)
    if anomalies: raise RuntimeError('Integrity anomaly; no resumption authorized')


if __name__ == '__main__': main()
