#!/usr/bin/env python3
"""New measurements through the unchanged, calibrated RTC simulation function."""
import argparse
import os
import subprocess
from pathlib import Path
from support import load_plan, original_module, provenance, read, save, sha, utc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', required=True, type=Path)
    ap.add_argument('--index', required=True, type=int)
    args = ap.parse_args()
    bundle = args.bundle.resolve()
    p = load_plan(bundle)
    study = bundle / 'study'
    out = study / p['output_relative']
    if (out / 'STOP.json').exists():
        raise RuntimeError('Integrity stop marker exists')
    task = p['tasks'][args.index]
    prov = provenance(bundle)
    save(out / 'claims' / f'{args.index:04d}.json', dict(task=task, **prov))
    try:
        for rel, digest in p['code_sha256'].items():
            if sha(Path('/phase2') / Path(rel).name) != digest:
                raise RuntimeError('New adapter differs: ' + rel)
        # Check all old Python harness bytes; no copy is edited or patched on disk.
        for rel, digest in p['frozen_code_sha256'].items():
            if sha(Path('/opt/rtc-code') / rel) != digest:
                raise RuntimeError('Original harness differs: ' + rel)
        v = p['versions'][task['suite_id']]
        for kind in ('source', 'elf'):
            if sha(study / v[kind + '_path']) != v[kind + '_sha256']:
                raise RuntimeError('Frozen input differs: ' + kind)
        actual = subprocess.check_output([os.environ['RENODE_BIN'], '--version'], text=True).strip()
        if actual != p['execution_renode_version']:
            raise RuntimeError('Renode version differs')
        module = original_module('rtc_factorial_v2')
        module.ROOT, module.OUT, module.MANIFEST = study, out, bundle / 'plan.json'
        schedule = read(study / 'subjects/phase3_rtc/plan.json')

        def platform(hz):
            rel = p['platforms'][str(hz)]
            path = study / rel
            if sha(path) != p['input_sha256']['study/' + rel]:
                raise RuntimeError('Platform differs')
            return path
        module.path_for = platform
        original_writer = module.write_new

        def writer(path, value):
            if path.parent.name.endswith('records'):
                value = dict(value, **prov, actual_renode_version=actual)
            original_writer(path, value)
        module.write_new = writer
        manifest = dict(versions={**p['versions'], **p['references']},
                        renode_version=actual, schedule_sha256=p['schedule_sha256'])
        record = module.simulate(manifest, schedule, task['suite_id'], task['condition'], task['seed'])
        comparison = dict(task_index=args.index, run_id=record['run_id'], observed=record['outcome'],
                          record_sha256=sha(out / 'records' / (record['run_id'] + '.json')),
                          timestamp_utc=utc())
        if task['condition'] == 'seeded':
            predicted = 'fail' if task['seed'] in v['predicted_failure_seeds'] else 'pass'
            comparison.update(predicted=predicted, evaluable=record['outcome'] in ('pass', 'fail'),
                agrees=(predicted == record['outcome']) if record['outcome'] in ('pass', 'fail') else None)
        save(out / 'forecast_comparisons' / f'{args.index:04d}.json', comparison)
        if record['outcome'] == 'fail':
            replay = module.simulate(manifest, schedule, task['suite_id'], task['condition'], task['seed'], replay=True)
            fields = ('lsi_frequency_hz', 'observations', 'cases', 'outcome', 'error')
            t1, t2 = read(study / record['trace_path']), read(study / replay['trace_path'])
            save(out / 'replay_audit' / (record['run_id'] + '.json'), dict(
                original=record['outcome'], replay=replay['outcome'],
                persisted_fields_match=all(t1[k] == t2[k] for k in fields),
                raw_trace_hash_matches=record['trace_sha256'] == replay['trace_sha256'],
                classification='unknown_pending_reference_and_source_review'))
            key = f"{v['family']}-{record['lsi_frequency_hz']}"
            try:
                save(out / 'reference_claims' / (key + '.json'), dict(trigger=record['run_id'], **prov))
            except FileExistsError:
                pass
            else:
                module.OUT = out / 'references' / key
                # A one-frequency schedule reuses exactly the saved platform.
                rs = dict(schedule, seeded_frequencies_hz=[record['lsi_frequency_hz']])
                ref = module.simulate(manifest, rs, 'reference-' + v['family'], 'seeded', 0)
                save(out / 'reference_results' / (key + '.json'), dict(trigger=record['run_id'],
                     outcome=ref['outcome'], record=ref, **prov))
        print(comparison, flush=True)
    except Exception as exc:
        try:
            save(out / 'STOP.json', dict(reason=f'{type(exc).__name__}: {exc}', index=args.index, **prov))
        except FileExistsError:
            pass
        raise


if __name__ == '__main__':
    main()
