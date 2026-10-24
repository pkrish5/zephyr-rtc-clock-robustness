#!/usr/bin/env python3
"""Approved repair gates and evaluations using the unchanged simulation loops."""
import argparse
import os
import subprocess
from pathlib import Path
from support import load_plan, original_module, provenance, read, save, sha, utc
from build_e import build


def checked_platform(bundle, p, hz):
    rel = p['platforms'][str(hz)]
    path = bundle / 'study' / rel
    if sha(path) != p['input_sha256']['study/' + rel]:
        raise RuntimeError('Saved platform differs')
    return path


def quality(bundle, p, out, vid, v, built, label, operator, hz, meta):
    study = bundle / 'study'
    mod = original_module('rtc_quality_run')
    mod.ROOT, mod.PLATFORM = study, checked_platform(bundle, p, hz)
    writer = mod.write_new

    def enriched(path, value):
        if path.parent.name == 'records':
            value = dict(value, **meta, repair_version_id=vid, repair_variant=v['variant'],
                         operator=operator, lsi_frequency_hz=hz, original_suite_id=v.get('original_suite_id'))
        writer(path, value)
    mod.write_new = enriched
    # Gate manifest is static; evaluation manifest locks the generated ELF set.
    manifest = bundle / 'plan.json' if operator == 'nominal_gate' else study / p['output_relative'] / 'execution.json'
    return mod.simulate(out, label, vid, v['family'], v['kind'], v.get('selected_case'),
                       built['source_sha256'], study / built['elf_path'], manifest,
                       max_virtual_sec=p['fault_max_virtual_sec'])


def replay_quality(bundle, p, target, vid, v, b, label, op, hz, meta, record):
    again = quality(bundle, p, target / 'replays', vid, v, b, label, op, hz, meta)
    study = bundle / 'study'
    a, r = read(study / record['trace_path']), read(study / again['trace_path'])
    fields = ('observations','cases','delay_measurements','outcome','error')
    save(target / 'replay_audit' / (label + '.json'), dict(original=record['outcome'], replay=again['outcome'],
        persisted_fields_match=all(a[k] == r[k] for k in fields), raw_trace_hash_matches=record['trace_sha256']==again['trace_sha256'],
        original_trace_sha256=record['trace_sha256'], replay_trace_sha256=again['trace_sha256']))


def gates(bundle, p, index, meta):
    out = bundle / 'study' / p['output_relative']
    vid = p['tasks'][index]['version_id']
    v = {**p['versions'], **p['references']}[vid]
    primary = vid in p['versions']
    nominal = build(bundle, p, vid, v, 'nominal', meta)
    results = []
    if nominal['status'] == 'pass':
        for n in range(p['nominal_repeats']):
            rid = vid + f'--nominal-{n:02d}'
            record = quality(bundle,p,out/'gates',vid,v,nominal,rid,'nominal_gate',32000,meta)
            results.append(dict(outcome=record['outcome'], error=record['error'],
                record_path=str((out/'gates/records'/(rid+'.json')).relative_to(bundle/'study')),
                record_sha256=sha(out/'gates/records'/(rid+'.json'))))
            if record['outcome'] == 'fail':
                replay_quality(bundle,p,out/'gates',vid,v,nominal,rid,'nominal_gate',32000,meta,record)
    passed = nominal['status']=='pass' and len(results)==p['nominal_repeats'] and all(r['outcome']=='pass' for r in results)
    builds = {'nominal': nominal}
    if passed:
        operators = ['nonarrival'] + (['offset_early','offset_late'] if v['family']!='rtc_time_counting' else [])
        for op in operators:
            builds[op] = build(bundle,p,vid,v,op,meta)
    save(out/'gate_summaries'/(vid+'.json'),dict(version_id=vid, primary=primary, variant=v['variant'],
        gate_pass=passed, nominal_outcomes=results, builds=builds, timestamp_utc=utc(), **meta))
    print(vid, '5/5 nominal gate:', passed, flush=True)


def legal(bundle,p,execution,task,meta):
    study = bundle/'study'
    out = study/p['output_relative']
    vid = task['version_id']
    v = execution['versions'][vid]
    module = original_module('rtc_factorial_v2')
    module.ROOT, module.OUT, module.MANIFEST = study,out/'legal',out/'execution.json'
    module.path_for = lambda hz:checked_platform(bundle,p,hz)
    writer = module.write_new

    def enriched(path,value):
        if path.parent.name.endswith('records'):
            value = dict(value,**meta,repair_version_id=vid,repair_variant=v['variant'],operator='legal',
                         original_suite_id=v.get('original_suite_id'))
        writer(path,value)
    module.write_new = enriched
    schedule = read(study/'subjects/phase3_rtc/plan.json')
    record = module.simulate(execution,schedule,vid,task['condition'],task['seed'])
    if record['outcome']=='fail':
        again = module.simulate(execution,schedule,vid,task['condition'],task['seed'],replay=True)
        a,r=read(study/record['trace_path']),read(study/again['trace_path'])
        fields=('lsi_frequency_hz','observations','cases','outcome','error')
        save(out/'legal/replay_audit'/(record['run_id']+'.json'),dict(original=record['outcome'],replay=again['outcome'],
            persisted_fields_match=all(a[k]==r[k] for k in fields),raw_trace_hash_matches=record['trace_sha256']==again['trace_sha256']))
        fam=v['family']
        key=f'{fam}-{record["lsi_frequency_hz"]}'
        try:
            save(out/'legal/reference_claims'/(key+'.json'),dict(trigger=record['run_id'],**meta))
        except FileExistsError:
            pass
        else:
            module.OUT=out/'legal/references'/key
            rs=dict(schedule,seeded_frequencies_hz=[record['lsi_frequency_hz']])
            ref=module.simulate(execution,rs,'reference-'+fam,'seeded',0)
            save(out/'legal/reference_results'/(key+'.json'),dict(trigger=record['run_id'],record=ref,**meta))
    return record


def evaluate(bundle,p,index,stage,meta):
    study=bundle/'study'
    out=study/p['output_relative']
    execution=read(out/'execution.json')
    if sha(out/'execution.json')!=(out/'execution.sha256').read_text().split()[0]:
        raise RuntimeError('Generated ELF manifest seal differs')
    file=out/('tasks-controls.json' if stage=='controls' else 'tasks-evaluate.json')
    if sha(file)!=execution['task_sha256'][file.name]:
        raise RuntimeError('Evaluation task seal differs')
    task=read(file)[index]
    vid=task['version_id'];v=execution['versions'][vid]
    if task['operator']=='legal':
        record=legal(bundle,p,execution,task,meta)
    else:
        op=task['operator']
        built=execution['builds'][vid]['nominal' if op in ('fast','slow') else op]
        if sha(study/built['elf_path'])!=built['elf_sha256']:
            raise RuntimeError('Generated ELF differs')
        hz=64000 if op=='fast' else 10000 if op=='slow' else 32000
        target=out/('controls' if stage=='controls' else 'faults')
        rid=vid+'--'+op
        record=quality(bundle,p,target,vid,v,built,rid,op,hz,meta)
        if record['outcome']=='fail':
            replay_quality(bundle,p,target,vid,v,built,rid,op,hz,meta,record)
        uart=(study/record['uart_path']).read_text(errors='replace') if record.get('uart_sha256') else ''
        active=(f'QUALITY_ALARM_OFFSET id=' in uart and f'sign={-1 if op=="offset_early" else 1} ' in uart) if op.startswith('offset_') else True
        score=dict(version_id=vid,operator=op,outcome=record['outcome'],active=active,
                   detected=active and record['outcome']=='fail',evaluable=active and record['outcome'] in ('pass','fail'),
                   record_sha256=sha(target/'records'/(rid+'.json')))
        save(target/'scores'/(rid+'.json'),score)
    print(stage,index,vid,task['operator'],record['outcome'],flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--index',type=int,required=True)
    ap.add_argument('--stage',choices=['gates','controls','evaluate'],required=True)
    a=ap.parse_args();bundle=a.bundle.resolve();p=load_plan(bundle)
    out=bundle/'study'/p['output_relative']
    if (out/'STOP.json').exists():
        raise RuntimeError('Integrity/control stop exists')
    meta=provenance(bundle)
    save(out/'claims'/a.stage/f'{a.index:05d}.json',dict(stage=a.stage,index=a.index,**meta))
    try:
        for rel,digest in p['code_sha256'].items():
            if sha(Path('/phase2')/Path(rel).name)!=digest:
                raise RuntimeError('Adapter differs: '+rel)
        for rel,digest in p['frozen_code_sha256'].items():
            if sha(Path('/opt/rtc-code')/rel)!=digest:
                raise RuntimeError('Frozen harness differs: '+rel)
        actual=subprocess.check_output([os.environ['RENODE_BIN'],'--version'],text=True).strip()
        if actual!=p['execution_renode_version']:
            raise RuntimeError('Renode differs')
        if a.stage=='gates':gates(bundle,p,a.index,meta)
        else:evaluate(bundle,p,a.index,a.stage,meta)
    except Exception as exc:
        try:save(out/'STOP.json',dict(reason=f'{type(exc).__name__}: {exc}',stage=a.stage,index=a.index,**meta))
        except FileExistsError:pass
        raise


if __name__=='__main__':main()
