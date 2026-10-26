#!/usr/bin/env python3
"""Packing, acceptance, and audit of the approved unchanged calibration runs."""
import argparse, hashlib, json, os, shlex, shutil, tarfile
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['jobfile','report','archive'])
    ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--repo',type=Path,required=True)
    a=ap.parse_args();p=json.loads((a.bundle/'plan.json').read_text());out=a.bundle/p['output_relative']
    assert os.environ['SLURM_JOB_PARTITION']=='development'
    assert sha(a.bundle/'plan.json')==(a.bundle/'plan.sha256').read_text().split()[0]
    for rel,d in {**p['code_sha256'],**p['followup_code_sha256']}.items():assert sha(a.repo/rel)==d,rel
    assert sha(a.repo/'paper/DESIGN.md')==p['design_sha256']
    if a.command=='jobfile':
        original=Path(os.environ['RTC_S2_PREVIOUS']);old=json.loads((original/'plan.json').read_text())
        assert sha(original/'plan.json')==p['continuation']['original_plan_sha256']
        oldout=original/old['output_relative']
        dst=out/'launcher/resume/jobfile';dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open('x') as f:
            for i in p['continuation']['task_indices']:
                t=p['tasks'][i];assert t['condition']!='nominal'
                rid=f"{t['unit_id']}-{t['condition']}-{i:03d}"
                assert not (oldout/'records'/(rid+'.json')).exists(),rid
                ns=[x for x in p['tasks'] if x['unit_id']==t['unit_id'] and x['condition']=='nominal'];assert len(ns)==5
                for n in ns:
                    r=json.loads((oldout/'records'/f"{n['unit_id']}-nominal-{n['index']:03d}.json").read_text())
                    assert r['application_completed'] and not r['missing_cases'] and not r['duplicate_cases']
                    assert {c['case']:c['status'] for c in r['cases']}==p['acceptance'][str(i)]['nominal_vector']
                f.write(shlex.join(['bash','-l',str(a.repo/'harness/tacc_s2/task.sh'),'run',str(i)])+'\n')
        save(out/'continuation_launch_manifest.json',dict(indices=p['continuation']['task_indices'],
            original_plan_sha256=p['continuation']['original_plan_sha256'],
            new_plan_sha256=sha(a.bundle/'plan.json'),scientific_inputs_changed=[],
            prior_missing_outcomes_preserved=True,workers=15,slurm_job_id=os.environ['SLURM_JOB_ID']))
    elif a.command=='report':
        checked=[];all_ok=True
        for i in p['continuation']['task_indices']:
            t=p['tasks'][i];rid=f"{t['unit_id']}-{t['condition']}-{i:03d}"
            rp=out/'records'/(rid+'.json');reasons=[];r=json.loads(rp.read_text()) if rp.exists() else {}
            if not r:reasons.append('missing final record')
            else:
                for field,expected in [('application_completed',True),('error',None),('missing_cases',[]),('duplicate_cases',[]),('outcome','complete'),('plan_sha256',sha(a.bundle/'plan.json')),('container_sha256',p['image_sha256']),('renode_version',p['renode_version']),('slurm_partition','development')]:
                    if r.get(field)!=expected:reasons.append('invalid '+field)
                actual={c['case']:c['status'] for c in r.get('cases',[])}
                if actual!=p['acceptance'][str(i)]['expected_vector']:reasons.append('unexpected per-case verdict vector')
                for kind,d in r.get('log_sha256',{}).items():
                    q=out/kind/(rid+('.json' if kind=='traces' else '.log'))
                    if not d or not q.exists() or sha(q)!=d:reasons.append('invalid '+kind+' hash')
                if i in (71,72):
                    text=(out/'uart'/(rid+'.log')).read_text(errors='replace')
                    if not all(s in text for s in ('main.c:41','elapsed >= MIN_BOUND','busted minimum bound')):reasons.append('anticipated lower-bound assertion not confirmed')
                homes=list((Path(os.environ['RTC_BASE'])/'runtime').glob(f"{r['slurm_job_id']}-run-{i}.*"))
                if len(homes)!=1:reasons.append('missing/ambiguous runtime cache')
                elif t['unit_id'].startswith(('f767-','f746-')):
                    svd=homes[0]/'home/.config/renode/cached_binaries/bin1'
                    if not svd.exists() or sha(svd)!=p['verified_f7_svd_sha256']:reasons.append('F7 SVD changed from qualification')
            all_ok=all_ok and not reasons
            checked.append(dict(index=i,unit_id=t['unit_id'],frequency_hz=t['frequency_hz'],accepted=not reasons,reasons=reasons,
                actual_cases=r.get('cases'),wall_seconds=r.get('wall_seconds'),record_sha256=sha(rp) if rp.exists() else None))
        save(out/'acceptance_report.json',dict(all_15_accepted=all_ok,settings=checked,
            production_condition_satisfied=all_ok,original_missing_outcomes_preserved=True,
            slurm_job_id=os.environ['SLURM_JOB_ID'],new_design_sha256=p['design_sha256']))
        print(json.dumps(dict(all_15_accepted=all_ok,abnormal_settings=[r for r in checked if not r['accepted']])))
    else:
        dest=Path(os.environ['RTC_S2_EVIDENCE']);dest.resolve().relative_to(a.repo.resolve())
        dest.mkdir(parents=True,exist_ok=False)
        shutil.copytree(out,dest/'raw')
        for rel in ['plan.json','plan.sha256','approved_runtime.json']:shutil.copyfile(a.bundle/rel,dest/rel)
        for rel in ['configs','renode','renode-cache']:shutil.copytree(a.bundle/rel,dest/rel)
        shutil.copyfile(a.repo/'paper/DESIGN.md',dest/'DESIGN.md')
        cache=dest/'runtime-caches';cache.mkdir()
        for rfile in (out/'records').glob('*.json'):
            r=json.loads(rfile.read_text());homes=list((Path(os.environ['RTC_BASE'])/'runtime').glob(f"{r['slurm_job_id']}-run-{r['index']}.*"))
            if len(homes)==1:shutil.copytree(homes[0]/'home/.config/renode',cache/r['run_id'])
        for rel in {**p['code_sha256'],**p['followup_code_sha256']}:
            d=dest/'code'/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.repo/rel,d)
        save(dest/'files.sha256.json',{str(f.relative_to(dest)):sha(f) for f in sorted(dest.rglob('*')) if f.is_file()})
        archive=dest.with_suffix('.tar.gz');assert not archive.exists()
        with tarfile.open(archive,'w:gz') as tar:tar.add(dest,arcname=dest.name)
        archive.with_suffix(archive.suffix+'.sha256').write_text(sha(archive)+'  '+archive.name+'\n')
        print(json.dumps(dict(archive=str(archive),sha256=sha(archive))))
if __name__=='__main__':main()
