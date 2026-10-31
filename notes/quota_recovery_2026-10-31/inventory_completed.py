#!/usr/bin/env python3
"""Compute-only, read-only inventory of exact registered result outputs.

Never walks arbitrary replicated study/results directories: those can be
frozen inputs. Only each bundle plan's exact output is a cleanup candidate.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import time


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def main():
    if os.environ.get('SLURM_JOB_PARTITION')!='development':raise RuntimeError('Compute only')
    repo=Path(os.environ['WORK']).resolve()/'zephyr-rtc-clock-robustness'
    out=Path(os.environ['RTC_RECOVERY_REPORT']).resolve();out.relative_to(Path(os.environ['SCRATCH']).resolve())
    out.mkdir(parents=True,exist_ok=False)
    baseline=repo/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json'
    if sha(baseline)!='b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef':raise RuntimeError('Baseline differs')
    protected=json.loads(baseline.read_text())['hashes']
    roots=[];inputs=set();seen=set();rows=[]
    for attempt in sorted((repo/'tacc_work').iterdir()):
        if not attempt.is_dir() or attempt.name=='20261026-git-checkout-recovery-v1':continue
        for bundle in sorted(attempt.iterdir()):
            if not bundle.is_dir() or 'bundle' not in bundle.name:continue
            for filename in ('plan.json','calibration_plan.json'):
                p=bundle/filename
                if not p.exists():continue
                plan=json.loads(p.read_text())
                for rel in plan.get('input_sha256',{}):inputs.add(str((bundle/rel).resolve()))
                rel=plan.get('output_relative')
                if not rel:continue
                for study in (bundle/'study',bundle):
                    result=study/rel
                    if not result.is_dir() or str(result) in seen:continue
                    result.resolve().relative_to(repo);seen.add(str(result))
                    roots.append((result,p,plan))
    for result,p,plan in roots:
        counts=dict(files=0,dirs=1,symlinks=0,special=0,bytes=0,protected_leaves=0,sealed_input_leaves=0)
        immediate={};jobs=set();record_count=0;top_json={}
        stack=[result]
        while stack:
            directory=stack.pop()
            with os.scandir(directory) as entries:
                for e in entries:
                    q=Path(e.path);parts=q.relative_to(result).parts;first=parts[0]
                    immediate[first]=immediate.get(first,0)+1
                    if e.is_symlink():counts['symlinks']+=1
                    elif e.is_dir(follow_symlinks=False):counts['dirs']+=1;stack.append(q);continue
                    elif e.is_file(follow_symlinks=False):
                        counts['files']+=1;counts['bytes']+=e.stat(follow_symlinks=False).st_size
                    else:counts['special']+=1;continue
                    if str(q.relative_to(repo)) in protected:counts['protected_leaves']+=1
                    if str(q) in inputs:counts['sealed_input_leaves']+=1
                    if q.parent.name=='records' and q.suffix=='.json':record_count+=1
                    if q.parent==result and q.suffix=='.json' and q.stat().st_size<2000000:
                        try:
                            d=json.loads(q.read_text())
                            if isinstance(d,dict):top_json[q.name]={k:v for k,v in d.items() if k in ('complete','records','expected','completed','missing_task_indices','mismatches','status','outcomes','build_outcomes','validated','stop_marker','reason','phase','stage')}
                        except (ValueError,OSError):top_json[q.name]={'unreadable_or_partial':True}
        text=str(result)
        excluded=('tacc_phase2_e_20261024_v1' in text or 's2_production_20261026_v1' in text)
        row=dict(result=str(result.relative_to(repo)),plan=str(p.relative_to(repo)),phase=plan.get('phase'),
            **counts,entries=sum(counts[k] for k in ('files','dirs','symlinks','special')),
            record_count=record_count,immediate_entry_counts=immediate,summary_fields=top_json,
            exclude_partial_E_or_priority_S2_primary=excluded,cleanup_authorized=False)
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k not in ('summary_fields','immediate_entry_counts')}),flush=True)
    value=dict(job_id=os.environ['SLURM_JOB_ID'],new_simulations=0,new_builds=0,files_deleted=0,
        protected_original_result_files=sum(k.startswith('results/') for k in protected),
        original_protected_results_must_remain_loose=True,rows=rows)
    with (out/'inventory.json').open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    with (out/'files.sha256.json').open('x') as f:json.dump({'inventory.json':sha(out/'inventory.json')},f,indent=2);f.write('\n')


if __name__=='__main__':main()
