#!/usr/bin/env python3
"""Seal generated repair ELFs and independently audit new study outputs."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from support import load_plan, read, save, sha, utc


def gate_valid(summary, repeats):
    rows=summary['nominal_outcomes']
    return (summary['builds']['nominal']['status']=='pass' and len(rows)==repeats
            and all(r['outcome']=='pass' for r in rows))


def seal(bundle,p,out):
    summaries={vid:read(out/'gate_summaries'/(vid+'.json')) for vid in [t['version_id'] for t in p['tasks']]}
    versions,builds,skips={},{},[]
    controls,tasks=[],[]
    for vid,v in {**p['versions'],**p['references']}.items():
        s=summaries[vid]
        reference=vid in p['references']
        if s['gate_pass']!=gate_valid(s,p['nominal_repeats']):
            raise RuntimeError('Gate flag disagrees with original nominal outcomes: '+vid)
        for row in s['nominal_outcomes']:
            path=bundle/'study'/row['record_path']
            if sha(path)!=row['record_sha256'] or audit_record(bundle/'study',path)['outcome']!=row['outcome']:
                raise RuntimeError('Nominal gate record differs: '+vid)
        if not s['gate_pass']:
            skips.append(dict(version_id=vid,reason='nominal_gate_or_build_not_passed',gate=s))
            if reference:
                raise RuntimeError('Reference nominal gate failed: '+vid)
            continue
        b=s['builds']
        for op,r in b.items():
            if r['status']=='pass' and sha(bundle/'study'/r['elf_path'])!=r['elf_sha256']:
                raise RuntimeError('Generated ELF changed: '+vid+' '+op)
        builds[vid]=b
        versions[vid]=dict(v,elf_path=b['nominal']['elf_path'],elf_sha256=b['nominal']['elf_sha256'])
        available=['fast','slow']
        for op in ['nonarrival']+(['offset_early','offset_late'] if v['family']!='rtc_time_counting' else []):
            if b.get(op,{}).get('status')=='pass':
                available.append(op)
            elif reference:
                raise RuntimeError('Reference mutant build failed: '+vid+' '+op)
            else:
                skips.append(dict(version_id=vid,operator=op,reason='fault_build_failed',build=b.get(op)))
        target=controls if reference else tasks
        for op in available:
            target.append(dict(version_id=vid,operator=op))
        for condition,n in [('seeded',100),('min',1),('max',1)]:
            if reference and condition=='seeded':continue
            for i in range(n):
                target.append(dict(version_id=vid,operator='legal',condition=condition,seed=i))
    for name,rows in [('controls',controls),('evaluate',tasks)]:
        for i,r in enumerate(rows):r['index']=i
        save(out/('tasks-'+name+'.json'),rows)
    execution=dict(registered_utc=utc(),renode_version=p['renode_version'],schedule_sha256=p['schedule_sha256'],
        plan_sha256=sha(bundle/'plan.json'),versions=versions,builds=builds,skips=skips,
        gate_summary_sha256={vid:sha(out/'gate_summaries'/(vid+'.json')) for vid in summaries},
        task_sha256={f'tasks-{s}.json':sha(out/f'tasks-{s}.json') for s in ('controls','evaluate')},
        planned_primary_versions=165,nominal_gate_passed=sum(vid in p['versions'] for vid in versions))
    save(out/'execution.json',execution)
    (out/'execution.sha256').write_text(sha(out/'execution.json')+'  execution.json\n')
    print('Sealed',execution['nominal_gate_passed'],'primary gate passes;',len(tasks),'evaluations;',len(controls),'controls')


def audit_record(study,path):
    r=read(path)
    for key in ('trace','uart','monitor'):
        if r.get(key+'_sha256') and sha(study/r[key+'_path'])!=r[key+'_sha256']:
            raise RuntimeError('Raw artifact changed: '+str(path))
    for key in ('node_name','slurm_job_id','container_sha256','apptainer_version'):
        if not r.get(key):raise RuntimeError('Missing provenance: '+key)
    return r


def control_audit(bundle,p,out):
    expected_slow={'rtc_alarm_callback':'callbacks absent past legal-clock ceiling plus service margin',
                   'rtc_alarm_pending':'pending absent past legal-clock ceiling plus service margin',
                   'rtc_time_counting':'calendar did not reach target by ceiling'}
    expected_fast={'rtc_alarm_callback':'alarm fired early','rtc_alarm_pending':'pending before fastest legal transition',
                   'rtc_time_counting':'calendar reached target too early'}
    rows=[]
    for t in read(out/'tasks-controls.json'):
        op,vid=t['operator'],t['version_id']
        fam=p['references'][vid]['family']
        if op=='legal':
            path=out/'legal/records'/(vid+'-'+t['condition']+'.json')
            r=audit_record(bundle/'study',path)
            ok=r['outcome']=='pass'
            required=None
        else:
            path=out/'controls/records'/(vid+'--'+op+'.json')
            r=audit_record(bundle/'study',path)
            uart=(bundle/'study'/r['uart_path']).read_text(errors='replace')
            required=expected_fast[fam] if op=='fast' else expected_slow[fam] if op in ('slow','nonarrival') else 'programmed alarm second differs from requested target'
            score=read(out/'controls/scores'/(vid+'--'+op+'.json'))
            ok=r['outcome']=='fail' and required in uart and score['active']
        rows.append(dict(task=t,outcome=r['outcome'],required_assertion=required,validated=ok,record_sha256=sha(path)))
    valid=len(rows)==19 and all(r['validated'] for r in rows)
    save(out/'control_audit.json',dict(timestamp_utc=utc(),validated=valid,rows=rows))
    if not valid:raise RuntimeError('Reference activation or endpoint control failed')
    print('All 19 fault-activation/endpoint controls validated')


def report(bundle,p,out):
    if not read(out/'control_audit.json')['validated']:
        raise RuntimeError('Controls unvalidated')
    tasks=read(out/'tasks-evaluate.json')
    legal={}
    for path in (out/'legal/records').glob('*.json'):
        r=audit_record(bundle/'study',path)
        if r['suite_id'] in p['versions']:legal.setdefault(r['suite_id'],[]).append(r)
    scores={}
    for path in (out/'faults/scores').glob('*.json'):
        s=read(path);scores[(s['version_id'],s['operator'])]=s
        audit_record(bundle/'study',out/'faults/records'/(s['version_id']+'--'+s['operator']+'.json'))
    rows=[]
    for vid,v in p['versions'].items():
        g=read(out/'gate_summaries'/(vid+'.json'))
        rs=legal.get(vid,[])
        seeded=[r for r in rs if r['condition']=='seeded']
        seeds=Counter(r['outcome'] for r in seeded)
        endpoints=Counter(r['outcome'] for r in rs if r['condition']!='seeded')
        row=dict(version_id=vid,original_suite_id=v['original_suite_id'],variant=v['variant'],family=v['family'],
            model=v['model'],prompt_condition=v['prompt_condition'],gate_pass=g['gate_pass'],
            nominal_outcomes=dict(Counter(r['outcome'] for r in g['nominal_outcomes'])),
            seeded_pass=seeds['pass'],seeded_fail=seeds['fail'],seeded_missing=100-seeds['pass']-seeds['fail'],
            endpoint_pass=endpoints['pass'],endpoint_fail=endpoints['fail'],endpoint_missing=2-endpoints['pass']-endpoints['fail'],
            complete_100_pass=seeds['pass']==100,complete_102_pass=len(rs)==102 and all(r['outcome']=='pass' for r in rs),
            observed_clock_flip=any(r['outcome']=='fail' for r in rs),
            original_budget_ms=v['original_budget_ms'],scalar_ceiling_ms=v['scalar_ceiling_ms'],
            separate_service_ms=v['separate_service_ms'])
        for op in ('fast','slow','nonarrival','offset_early','offset_late'):
            s=scores.get((vid,op))
            row[op]=s if s else dict(outcome='not_applicable' if op.startswith('offset_') and v['family']=='rtc_time_counting' else 'unconfirmed_or_missing',evaluable=False,detected=False)
        rows.append(row)
    per_variant={}
    for variant in ('V0','V1','V1b','V2','V3'):
        rr=[r for r in rows if r['variant']==variant]
        per_variant[variant]=dict(attempts=33,gate_pass=sum(r['gate_pass'] for r in rr),
            confirmed_robust_100=sum(r['complete_100_pass'] for r in rr),confirmed_robust_102=sum(r['complete_102_pass'] for r in rr),
            observed_clock_flip_subjects=sum(r['observed_clock_flip'] for r in rr),
            seeded_pass=sum(r['seeded_pass'] for r in rr),seeded_fail=sum(r['seeded_fail'] for r in rr),
            seeded_missing=sum(r['seeded_missing'] for r in rr),
            faults={op:dict(detected=sum(r[op]['detected'] for r in rr),evaluable=sum(r[op]['evaluable'] for r in rr))
                    for op in ('fast','slow','nonarrival','offset_early','offset_late')},
            robust_and_slow_detecting=sum(r['complete_100_pass'] and r['slow']['detected'] for r in rr))
    expected_legal=sum(t['operator']=='legal' for t in tasks)
    actual_legal=sum(len(rs) for rs in legal.values())
    actual_fault=len(scores)
    result=dict(timestamp_utc=utc(),per_variant=per_variant,subjects=rows,expected_evaluation_tasks=len(tasks),
        expected_legal_tasks=expected_legal,actual_legal_records=actual_legal,actual_fault_scores=actual_fault,
        complete=actual_legal+actual_fault==len(tasks),
        next_action='STOP at Phase 3 with old/new number table before paper edits. E2 remains on hold.')
    save(out/'repair_report.json',result)
    with (out/'repair_per_subject.csv').open('x',newline='') as f:
        keys=[k for k in rows[0] if k not in ('fast','slow','nonarrival','offset_early','offset_late','nominal_outcomes')]
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r[k] for k in keys} for r in rows)
    print(json.dumps({k:v for k,v in result.items() if k!='subjects'},indent=2))
    if not result['complete']:raise RuntimeError('Incomplete evaluation task accounting')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=['seal','controls','report'])
    ap.add_argument('--bundle',type=Path,required=True)
    a=ap.parse_args();p=load_plan(a.bundle);out=a.bundle/'study'/p['output_relative']
    try:{'seal':seal,'controls':control_audit,'report':report}[a.command](a.bundle,p,out)
    except Exception as exc:
        try:save(out/'STOP.json',dict(stage=a.command,reason=f'{type(exc).__name__}: {exc}',timestamp_utc=utc()))
        except FileExistsError:pass
        raise


if __name__=='__main__':main()
